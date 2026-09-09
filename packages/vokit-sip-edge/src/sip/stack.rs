use std::collections::HashMap;
use std::net::SocketAddr;
use std::sync::Arc;

use dashmap::DashMap;
use tokio::net::UdpSocket;
use tokio::sync::{mpsc, watch, Mutex};
use tracing::{error, info, warn};

use crate::config::AppConfig;
use crate::error::{EdgeError, EdgeResult};
use crate::media::bridge::MediaBridge;
use crate::rtp::session::RtpSession;
use crate::sip::dialog::{CallDirection, CallSession, CallStatus, SipDialog};
use crate::sip::message::{random_token, sanitize_number, sip_uri};
use crate::sip::transfer::{
    format_refer_to_with_replaces, map_sip_code_to_reason, parse_sipfrag_status_code,
    TransferState, TransferStatus,
};
use crate::sip::sdp::{extract_sdp_body, parse_sdp, pick_local_rtp_port, SdpSession};
use crate::sip::trace::{
    log_sip_diag, log_sip_rx, log_sip_state, log_sip_tx, log_sip_unmatched_response, log_sip_warn,
    summarize_sip,
};

#[derive(Clone)]
pub struct StackHandle {
    inner: Arc<StackInner>,
}

struct StackInner {
    config: AppConfig,
    socket: Arc<UdpSocket>,
    trunk_addr: SocketAddr,
    calls: DashMap<String, Arc<Mutex<CallSession>>>,
    call_id_index: DashMap<String, String>,
    /// Signals media bridge tasks to send Django `stop` and exit on call end.
    media_shutdown: DashMap<String, watch::Sender<bool>>,
    cmd_tx: mpsc::Sender<StackCommand>,
}

enum StackCommand {
    Originate {
        call_id: String,
        from: String,
        to: String,
        node_media_url: Option<String>,
    },
    Hangup {
        call_id: String,
    },
    Transfer {
        call_id: String,
        to: String,
        max_timeout_seconds: Option<u32>,
    },
}

pub struct SipStack;

impl SipStack {
    pub async fn start(config: AppConfig) -> EdgeResult<StackHandle> {
        if config.trunk_host.is_empty() {
            return Err(EdgeError::Config("SIP_TRUNK_HOST is required".into()));
        }

        let trunk_addr = config
            .trunk_socket_addr()
            .map_err(|e| EdgeError::Config(e))?;

        let socket = UdpSocket::bind(config.local_bind).await?;
        let socket = Arc::new(socket);
        info!(
            "SIP stack bound {} (via {}) → trunk {} ({:?})",
            config.local_bind,
            config.signaling_via(),
            trunk_addr,
            config.transport
        );

        let calls: DashMap<String, Arc<Mutex<CallSession>>> = DashMap::new();
        let call_id_index: DashMap<String, String> = DashMap::new();
        let media_shutdown: DashMap<String, watch::Sender<bool>> = DashMap::new();
        let (cmd_tx, mut cmd_rx) = mpsc::channel::<StackCommand>(128);

        let inner = Arc::new(StackInner {
            config: config.clone(),
            socket: socket.clone(),
            trunk_addr,
            calls,
            call_id_index,
            media_shutdown,
            cmd_tx,
        });

        let recv_inner = inner.clone();
        tokio::spawn(async move {
            let mut buf = vec![0u8; 65535];
            loop {
                match socket.recv_from(&mut buf).await {
                    Ok((n, peer)) => {
                        let msg = String::from_utf8_lossy(&buf[..n]).to_string();
                        if let Err(e) = recv_inner.handle_incoming(&msg, peer).await {
                            warn!("SIP incoming handler error: {e}");
                        }
                    }
                    Err(e) => {
                        error!("SIP socket recv error: {e}");
                        tokio::time::sleep(std::time::Duration::from_millis(250)).await;
                    }
                }
            }
        });

        let cmd_inner = inner.clone();
        tokio::spawn(async move {
            while let Some(cmd) = cmd_rx.recv().await {
                match cmd {
                    StackCommand::Originate {
                        call_id,
                        from,
                        to,
                        node_media_url,
                    } => {
                        if let Err(e) = cmd_inner
                            .originate_call(&call_id, &from, &to, node_media_url)
                            .await
                        {
                            error!("originate {call_id} failed: {e}");
                            if let Some(entry) = cmd_inner.calls.get(&call_id) {
                                let mut session = entry.lock().await;
                                session.status = CallStatus::Failed;
                                session.error = Some(e.to_string());
                                session.ended_at = Some(std::time::Instant::now());
                            }
                            cmd_inner.signal_media_end(&call_id);
                        }
                    }
                    StackCommand::Hangup { call_id } => {
                        if let Err(e) = cmd_inner.hangup_call(&call_id).await {
                            warn!("hangup {call_id}: {e}");
                        }
                    }
                    StackCommand::Transfer {
                        call_id,
                        to,
                        max_timeout_seconds,
                    } => {
                        match cmd_inner
                            .transfer_call(&call_id, &to, max_timeout_seconds)
                            .await
                        {
                            Ok(()) => {
                                if let Some(secs) = max_timeout_seconds.filter(|s| *s > 0) {
                                    let inner = cmd_inner.clone();
                                    let cid = call_id.clone();
                                    tokio::spawn(async move {
                                        tokio::time::sleep(std::time::Duration::from_secs(
                                            secs as u64,
                                        ))
                                        .await;
                                        let _ = inner.mark_transfer_timeout_if_pending(&cid).await;
                                    });
                                }
                            }
                            Err(e) => warn!("transfer {call_id}: {e}"),
                        }
                    }
                }
            }
        });

        Ok(StackHandle { inner })
    }
}

impl StackHandle {
    pub fn config(&self) -> &AppConfig {
        &self.inner.config
    }

    pub async fn create_outbound(
        &self,
        from: &str,
        to: &str,
        node_media_url: Option<String>,
    ) -> EdgeResult<CallSession> {
        let id = uuid::Uuid::new_v4().to_string();
        let session = CallSession::new_outbound(id.clone(), from.to_string(), to.to_string(), node_media_url);
        let arc = Arc::new(Mutex::new(session.clone()));
        self.inner.calls.insert(id.clone(), arc);
        self.inner
            .cmd_tx
            .send(StackCommand::Originate {
                call_id: id.clone(),
                from: from.to_string(),
                to: to.to_string(),
                node_media_url: session.node_media_url.clone(),
            })
            .await
            .map_err(|e| EdgeError::Other(e.to_string()))?;
        Ok(session)
    }

    pub async fn get_call(&self, id: &str) -> Option<CallSession> {
        if let Some(entry) = self.inner.calls.get(id) {
            let guard = entry.lock().await;
            return Some(guard.clone());
        }
        None
    }

    pub async fn hangup(&self, id: &str) -> EdgeResult<()> {
        self.inner
            .cmd_tx
            .send(StackCommand::Hangup {
                call_id: id.to_string(),
            })
            .await
            .map_err(|e| EdgeError::Other(e.to_string()))
    }

    pub async fn transfer(
        &self,
        id: &str,
        to: &str,
        max_timeout_seconds: Option<u32>,
    ) -> EdgeResult<()> {
        self.inner
            .cmd_tx
            .send(StackCommand::Transfer {
                call_id: id.to_string(),
                to: to.to_string(),
                max_timeout_seconds,
            })
            .await
            .map_err(|e| EdgeError::Other(e.to_string()))
    }

    pub async fn list_calls(&self) -> Vec<CallSession> {
        let mut out = Vec::new();
        for entry in self.inner.calls.iter() {
            out.push(entry.value().lock().await.clone());
        }
        out
    }
}

impl StackInner {
    async fn originate_call(
        &self,
        call_id: &str,
        from: &str,
        to: &str,
        node_media_url: Option<String>,
    ) -> EdgeResult<()> {
        let entry = self
            .calls
            .get(call_id)
            .ok_or_else(|| EdgeError::NotFound(call_id.to_string()))?;
        let mut session = entry.lock().await;

        let local_tag = random_token(10);
        let branch = format!("z9hG4bK{}", random_token(12));
        let from_uri = sip_uri(from, &self.config.domain, self.config.local_bind.port());
        let to_uri = sip_uri(to, &self.config.trunk_host, self.config.trunk_port);
        let request_uri = sip_uri(to, &self.config.trunk_host, self.config.trunk_port);
        let contact = format!(
            "<sip:{}:{}>",
            self.config.public_ip,
            self.config.local_bind.port()
        );

        let rtp_port = pick_local_rtp_port(self.config.rtp_port_min, self.config.rtp_port_max);
        let sdp = SdpSession::new(&self.config.public_ip, rtp_port, self.config.codec);
        session.rtp_local_port = Some(rtp_port);
        session.status = CallStatus::Ringing;
        session.node_media_url = node_media_url;

        let dialog = SipDialog {
            call_id: session.sip_call_id.clone(),
            local_tag: local_tag.clone(),
            remote_tag: None,
            branch: branch.clone(),
            cseq: 1,
            from_uri: from_uri.clone(),
            from_display: sanitize_number(from),
            to_uri: to_uri.clone(),
            to_display: sanitize_number(to),
            contact_uri: contact.clone(),
            route_target: request_uri.clone(),
        };
        session.dialog = Some(dialog.clone());
        let sip_id = session.sip_call_id.clone();
        drop(session);

        self.call_id_index.insert(sip_id.clone(), call_id.to_string());

        let invite = build_invite(
            &self.config,
            &dialog,
            &request_uri,
            &sdp.to_sdp(),
        );
        self.send_to(&invite, self.trunk_addr).await?;
        log_sip_diag(&format!(
            "INVITE sent call_key={call_id} to={to} from={from} trunk={} sip_call_id={sip_id}",
            self.trunk_addr
        ));
        Ok(())
    }

    async fn hangup_call(&self, call_id: &str) -> EdgeResult<()> {
        let entry = self
            .calls
            .get(call_id)
            .ok_or_else(|| EdgeError::NotFound(call_id.to_string()))?;
        let mut session = entry.lock().await;
        let dest = session.remote_signaling.unwrap_or(self.trunk_addr);
        if let Some(dialog) = session.dialog.clone() {
            let bye = build_bye(&self.config, &dialog);
            self.send_to(&bye, dest).await?;
        }
        session.status = CallStatus::Completed;
        session.ended_at = Some(std::time::Instant::now());
        drop(session);
        self.signal_media_end(call_id);
        Ok(())
    }

    async fn transfer_call(
        &self,
        call_id: &str,
        to: &str,
        _max_timeout_seconds: Option<u32>,
    ) -> EdgeResult<()> {
        let entry = self
            .calls
            .get(call_id)
            .ok_or_else(|| EdgeError::NotFound(call_id.to_string()))?;
        let mut session = entry.lock().await;

        if session.status != CallStatus::Answered {
            return Err(EdgeError::Sip(format!(
                "call not answered for transfer (status={})",
                session.status.as_str()
            )));
        }

        if session.dialog.is_none() {
            return Err(EdgeError::Sip("no dialog for transfer".into()));
        }

        if let Some(existing) = session.transfer.as_ref() {
            if matches!(
                existing.status,
                TransferStatus::Pending | TransferStatus::InProgress
            ) {
                return Err(EdgeError::Sip("transfer already in progress".into()));
            }
        }

        // Consult-then-REFER: keep inbound AI media up while human rings.
        let from = if !self.config.default_from.trim().is_empty() {
            self.config.default_from.clone()
        } else {
            session.to_number.clone()
        };
        let consult_id = uuid::Uuid::new_v4().to_string();
        session.transfer = Some(TransferState::new_pending(
            to.to_string(),
            Some(consult_id.clone()),
        ));
        drop(session);

        let mut consult = CallSession::new_outbound(
            consult_id.clone(),
            from.clone(),
            to.to_string(),
            None, // no Pipecat media on consultation leg
        );
        consult.parent_call_key = Some(call_id.to_string());
        self.calls
            .insert(consult_id.clone(), Arc::new(Mutex::new(consult)));

        log_sip_diag(&format!(
            "transfer consult INVITE parent={call_id} consult={consult_id} to={to}"
        ));
        self.originate_call(&consult_id, &from, to, None).await?;
        Ok(())
    }

    async fn mark_transfer_timeout_if_pending(&self, call_key: &str) -> EdgeResult<()> {
        let consult_key = {
            let entry = self
                .calls
                .get(call_key)
                .ok_or_else(|| EdgeError::NotFound(call_key.to_string()))?;
            let mut session = entry.lock().await;
            let Some(ref mut transfer) = session.transfer else {
                return Ok(());
            };
            if !matches!(
                transfer.status,
                TransferStatus::Pending | TransferStatus::InProgress
            ) {
                return Ok(());
            }
            transfer.status = TransferStatus::Failed;
            transfer.sip_code = Some(408);
            transfer.reason = Some("timeout".into());
            let consult = transfer.consult_call_key.clone();
            log_sip_diag(&format!(
                "transfer timeout call_key={call_key} to={}",
                transfer.to
            ));
            consult
        };
        if let Some(consult_key) = consult_key {
            let _ = self.hangup_consult_leg(&consult_key).await;
        }
        Ok(())
    }

    /// Hang up a consultation outbound leg without ending the parent inbound media.
    async fn hangup_consult_leg(&self, consult_key: &str) -> EdgeResult<()> {
        let entry = match self.calls.get(consult_key) {
            Some(e) => e,
            None => return Ok(()),
        };
        let session = entry.lock().await;
        if matches!(
            session.status,
            CallStatus::Completed | CallStatus::Failed | CallStatus::Canceled
        ) {
            return Ok(());
        }
        let dest = session.remote_signaling.unwrap_or(self.trunk_addr);
        let answered = session.status == CallStatus::Answered;
        if let Some(dialog) = session.dialog.clone() {
            drop(session);
            if answered {
                let bye = build_bye(&self.config, &dialog);
                let _ = self.send_to(&bye, dest).await;
            } else {
                let cancel = build_cancel(&self.config, &dialog);
                let _ = self.send_to(&cancel, dest).await;
            }
        } else {
            drop(session);
        }
        if let Some(entry) = self.calls.get(consult_key) {
            let mut session = entry.lock().await;
            session.status = CallStatus::Canceled;
            session.ended_at = Some(std::time::Instant::now());
        }
        Ok(())
    }

    async fn on_consult_ringing(&self, consult_key: &str) -> EdgeResult<()> {
        let parent_key = {
            let entry = self
                .calls
                .get(consult_key)
                .ok_or_else(|| EdgeError::NotFound(consult_key.to_string()))?;
            let session = entry.lock().await;
            session.parent_call_key.clone()
        };
        let Some(parent_key) = parent_key else {
            return Ok(());
        };
        self.mark_transfer_in_progress(&parent_key).await
    }

    async fn on_consult_answered(&self, consult_key: &str) -> EdgeResult<()> {
        let (parent_key, consult_dialog, to_number) = {
            let entry = self
                .calls
                .get(consult_key)
                .ok_or_else(|| EdgeError::NotFound(consult_key.to_string()))?;
            let session = entry.lock().await;
            (
                session.parent_call_key.clone(),
                session.dialog.clone(),
                session.to_number.clone(),
            )
        };
        let Some(parent_key) = parent_key else {
            return Ok(());
        };
        let Some(consult_dialog) = consult_dialog else {
            return self
                .on_consult_failed(&parent_key, consult_key, 500, "sip_error")
                .await;
        };
        let Some(remote_tag) = consult_dialog.remote_tag.clone() else {
            return self
                .on_consult_failed(&parent_key, consult_key, 500, "sip_error")
                .await;
        };

        let base_uri = sip_uri(
            &to_number,
            &self.config.trunk_host,
            self.config.trunk_port,
        );
        let refer_to = format_refer_to_with_replaces(
            &base_uri,
            &consult_dialog.call_id,
            &remote_tag,
            &consult_dialog.local_tag,
        );

        let (refer, dest) = {
            let entry = self
                .calls
                .get(&parent_key)
                .ok_or_else(|| EdgeError::NotFound(parent_key.clone()))?;
            let mut session = entry.lock().await;
            let dialog = session
                .dialog
                .clone()
                .ok_or_else(|| EdgeError::Sip("no inbound dialog for REFER".into()))?;
            let dest = session.remote_signaling.unwrap_or(self.trunk_addr);
            let refer = build_refer(&self.config, &dialog, &refer_to);
            let sent_cseq = dialog.cseq + 1;
            if let Some(ref mut d) = session.dialog {
                d.cseq = sent_cseq;
            }
            if let Some(ref mut transfer) = session.transfer {
                transfer.refer_cseq = sent_cseq;
                transfer.status = TransferStatus::InProgress;
            }
            (refer, dest)
        };

        log_sip_diag(&format!(
            "transfer REFER+Replaces parent={parent_key} consult={consult_key}"
        ));
        self.send_to(&refer, dest).await?;
        Ok(())
    }

    async fn on_consult_failed(
        &self,
        parent_key: &str,
        consult_key: &str,
        sip_code: u16,
        reason: &str,
    ) -> EdgeResult<()> {
        self.mark_transfer_failed(parent_key, sip_code, reason)
            .await?;
        if let Some(entry) = self.calls.get(consult_key) {
            let mut session = entry.lock().await;
            if !matches!(
                session.status,
                CallStatus::Completed | CallStatus::Failed | CallStatus::Canceled
            ) {
                session.status = CallStatus::Failed;
                session.ended_at = Some(std::time::Instant::now());
            }
        }
        Ok(())
    }

    fn is_transfer_active(session: &CallSession) -> bool {
        session.transfer.as_ref().is_some_and(|t| {
            matches!(
                t.status,
                TransferStatus::Pending | TransferStatus::InProgress
            )
        })
    }

    async fn mark_transfer_in_progress(&self, call_key: &str) -> EdgeResult<()> {
        let entry = self
            .calls
            .get(call_key)
            .ok_or_else(|| EdgeError::NotFound(call_key.to_string()))?;
        let mut session = entry.lock().await;
        if let Some(ref mut transfer) = session.transfer {
            if transfer.status == TransferStatus::Pending {
                transfer.status = TransferStatus::InProgress;
            }
        }
        Ok(())
    }

    async fn mark_transfer_succeeded(&self, call_key: &str, sip_code: u16) -> EdgeResult<()> {
        let consult_key = {
            let entry = self
                .calls
                .get(call_key)
                .ok_or_else(|| EdgeError::NotFound(call_key.to_string()))?;
            let mut session = entry.lock().await;
            let consult = session
                .transfer
                .as_ref()
                .and_then(|t| t.consult_call_key.clone());
            if let Some(ref mut transfer) = session.transfer {
                transfer.status = TransferStatus::Succeeded;
                transfer.sip_code = Some(sip_code);
                transfer.reason = Some(map_sip_code_to_reason(sip_code).into());
            }
            consult
        };
        if let Some(consult_key) = consult_key {
            let _ = self.hangup_consult_leg(&consult_key).await;
        }
        self.signal_media_end(call_key);
        Ok(())
    }

    async fn mark_transfer_failed(
        &self,
        call_key: &str,
        sip_code: u16,
        reason: &str,
    ) -> EdgeResult<()> {
        let entry = self
            .calls
            .get(call_key)
            .ok_or_else(|| EdgeError::NotFound(call_key.to_string()))?;
        let mut session = entry.lock().await;
        if let Some(ref mut transfer) = session.transfer {
            transfer.status = TransferStatus::Failed;
            transfer.sip_code = Some(sip_code);
            transfer.reason = Some(reason.into());
            log_sip_diag(&format!(
                "transfer failed call_key={call_key} code={sip_code} reason={reason}"
            ));
        }
        Ok(())
    }

    async fn handle_inbound_notify(&self, raw: &str, peer: SocketAddr) -> EdgeResult<()> {
        let headers = parse_headers(raw);
        let call_id = headers.get("call-id").cloned().unwrap_or_default();
        let event = headers
            .get("event")
            .map(|e| e.to_lowercase())
            .unwrap_or_default();
        let cseq = headers.get("cseq").cloned().unwrap_or_default();

        let call_key = self
            .call_id_index
            .get(&call_id)
            .map(|e| e.value().clone());

        if let Some(call_key) = call_key {
            if event.starts_with("refer") {
                let body = extract_body(raw);
                if let Some(code) = parse_sipfrag_status_code(&body) {
                    log_sip_diag(&format!(
                        "NOTIFY refer sipfrag {code} call_key={call_key} peer={peer}"
                    ));
                    if (100..200).contains(&code) {
                        self.mark_transfer_in_progress(&call_key).await?;
                    } else if code == 200 {
                        self.mark_transfer_succeeded(&call_key, code).await?;
                    } else if code >= 300 {
                        let reason = map_sip_code_to_reason(code);
                        self.mark_transfer_failed(&call_key, code, reason).await?;
                    }
                }
            }

            if let Some(entry) = self.calls.get(&call_key) {
                let session = entry.lock().await;
                if let Some(dialog) = session.dialog.clone() {
                    drop(session);
                    let ok = build_200_ok_notify(&self.config, &dialog, &headers, &cseq);
                    self.send_to(&ok, peer).await?;
                }
            }
        } else {
            log_sip_warn(&format!(
                "NOTIFY without matching call sip_call_id={call_id} peer={peer}"
            ));
        }
        Ok(())
    }

    async fn handle_incoming(&self, raw: &str, peer: SocketAddr) -> EdgeResult<()> {
        log_sip_rx(peer, raw);
        let first_line = raw.lines().next().unwrap_or_default();
        if first_line.starts_with("SIP/2.0") {
            return self.handle_response(raw, peer).await;
        }
        if first_line.starts_with("INVITE ") {
            log_sip_diag(&format!("inbound INVITE from {peer}"));
            return self.handle_inbound_invite(raw, peer).await;
        }
        if first_line.starts_with("CANCEL ") {
            return self.handle_inbound_cancel(raw, peer).await;
        }
        if first_line.starts_with("BYE ") {
            return self.handle_inbound_bye(raw, peer).await;
        }
        if first_line.starts_with("ACK ") {
            log_sip_diag(&format!("ACK received from {peer}"));
            return Ok(());
        }
        if first_line.starts_with("OPTIONS ") {
            log_sip_diag(&format!("OPTIONS received from {peer} (ignored)"));
            return Ok(());
        }
        if first_line.starts_with("NOTIFY ") {
            return self.handle_inbound_notify(raw, peer).await;
        }
        log_sip_warn(&format!("unhandled SIP request from {peer}: {first_line}"));
        Ok(())
    }

    fn list_known_call_ids(&self) -> Vec<String> {
        self.call_id_index
            .iter()
            .map(|e| e.key().clone())
            .take(20)
            .collect()
    }

    async fn handle_response(&self, raw: &str, peer: SocketAddr) -> EdgeResult<()> {
        let status_code = raw
            .lines()
            .next()
            .and_then(|l| l.split_whitespace().nth(1))
            .and_then(|c| c.parse::<u16>().ok())
            .unwrap_or(0);
        let headers = parse_headers(raw);
        let call_id = headers.get("call-id").cloned().unwrap_or_default();
        let call_key = self
            .call_id_index
            .get(&call_id)
            .map(|e| e.value().clone());

        let Some(call_key) = call_key else {
            log_sip_unmatched_response(status_code, &call_id, peer, &self.list_known_call_ids());
            return Ok(());
        };

        let cseq = headers.get("cseq").cloned().unwrap_or_default();
        let reason = headers.get("reason").cloned().unwrap_or_default();
        log_sip_diag(&format!(
            "SIP response {status_code} matched call_key={call_key} sip_call_id={call_id} cseq={cseq} reason={reason} peer={peer}"
        ));

        let entry = self
            .calls
            .get(&call_key)
            .ok_or_else(|| EdgeError::NotFound(call_key.clone()))?;

        match status_code {
            100 => {
                let mut session = entry.lock().await;
                let prev = session.status.as_str();
                session.remote_signaling = Some(peer);
                log_sip_state(&call_key, prev, "ringing", "100 Trying");
            }
            180 | 183 => {
                self.handle_provisional(&call_key, peer, &headers, status_code, raw)
                    .await?;
                let is_consult = {
                    let session = entry.lock().await;
                    session.is_consult_leg()
                };
                if is_consult {
                    self.on_consult_ringing(&call_key).await?;
                }
            }
            202 => {
                if cseq.to_uppercase().contains("REFER") {
                    self.mark_transfer_in_progress(&call_key).await?;
                } else {
                    log_sip_warn(&format!(
                        "unhandled 202 Accepted cseq={cseq} call_key={call_key}"
                    ));
                }
            }
            200 => {
                if cseq.to_uppercase().contains("INVITE") {
                    self.handle_invite_200(&call_key, peer, &headers, raw)
                        .await?;
                } else if cseq.to_uppercase().contains("PRACK") {
                    log_sip_diag(&format!("200 OK for PRACK call_key={call_key} (ignored)"));
                } else if cseq.to_uppercase().contains("CANCEL") {
                    self.mark_call_ended(&call_key, CallStatus::Canceled, "200 OK for CANCEL")
                        .await?;
                } else if cseq.to_uppercase().contains("REFER") {
                    log_sip_diag(&format!("200 OK for REFER call_key={call_key} (ignored)"));
                } else {
                    log_sip_warn(&format!(
                        "unhandled 200 OK cseq={cseq} call_key={call_key} — {}",
                        summarize_sip(raw)
                    ));
                }
            }
            401 | 403 | 404 | 408 | 480 | 484 | 486 | 488 | 503 | 603 | 604 => {
                if cseq.to_uppercase().contains("REFER") {
                    self.mark_transfer_failed(&call_key, status_code, "sip_error")
                        .await?;
                } else {
                    let (is_consult, parent_key, transfer_active) = {
                        let session = entry.lock().await;
                        (
                            session.is_consult_leg(),
                            session.parent_call_key.clone(),
                            Self::is_transfer_active(&session),
                        )
                    };
                    if is_consult {
                        if let Some(parent_key) = parent_key {
                            let reason = map_sip_code_to_reason(status_code);
                            self.on_consult_failed(&parent_key, &call_key, status_code, reason)
                                .await?;
                        }
                    } else if transfer_active {
                        log_sip_diag(&format!(
                            "SIP {status_code} during active transfer call_key={call_key} — not failing inbound leg"
                        ));
                    } else {
                        self.mark_call_failed(&call_key, peer, status_code, &reason)
                            .await?;
                    }
                }
            }
            487 => {
                let (is_consult, parent_key) = {
                    let session = entry.lock().await;
                    (session.is_consult_leg(), session.parent_call_key.clone())
                };
                if is_consult {
                    if let Some(parent_key) = parent_key {
                        self.on_consult_failed(&parent_key, &call_key, 487, "no_answer")
                            .await?;
                    }
                } else {
                    self.mark_call_ended(&call_key, CallStatus::Canceled, "487 Request Terminated")
                        .await?;
                }
            }
            code => {
                log_sip_warn(&format!(
                    "unhandled SIP response {code} call_key={call_key} — {}",
                    summarize_sip(raw)
                ));
            }
        }
        Ok(())
    }

    async fn mark_call_failed(
        &self,
        call_key: &str,
        peer: SocketAddr,
        status_code: u16,
        reason: &str,
    ) -> EdgeResult<()> {
        let entry = self
            .calls
            .get(call_key)
            .ok_or_else(|| EdgeError::NotFound(call_key.to_string()))?;
        let mut session = entry.lock().await;
        let prev = session.status.as_str();
        session.remote_signaling = Some(peer);
        session.status = CallStatus::Failed;
        let detail = if reason.is_empty() {
            format!("SIP {status_code} from {peer}")
        } else {
            format!("SIP {status_code} from {peer}: {reason}")
        };
        session.error = Some(detail.clone());
        session.ended_at = Some(std::time::Instant::now());
        log_sip_state(call_key, prev, "failed", &detail);
        drop(session);
        self.signal_media_end(call_key);
        Ok(())
    }

    async fn mark_call_ended(&self, call_key: &str, status: CallStatus, detail: &str) -> EdgeResult<()> {
        let entry = self
            .calls
            .get(call_key)
            .ok_or_else(|| EdgeError::NotFound(call_key.to_string()))?;
        let mut session = entry.lock().await;
        let prev = session.status.as_str();
        let to_status = status.as_str();
        session.status = status;
        session.ended_at = Some(std::time::Instant::now());
        log_sip_state(call_key, prev, to_status, detail);
        drop(session);
        // Unblock media bridge so it can send Django `stop` (CallRecord finalize).
        self.signal_media_end(call_key);
        Ok(())
    }

    fn signal_media_end(&self, call_id: &str) {
        if let Some((_, tx)) = self.media_shutdown.remove(call_id) {
            if tx.send(true).is_err() {
                log_sip_diag(&format!(
                    "media shutdown receiver already dropped call_key={call_id}"
                ));
            } else {
                log_sip_diag(&format!("media shutdown signaled call_key={call_id}"));
            }
        }
    }

    async fn handle_provisional(
        &self,
        call_key: &str,
        peer: SocketAddr,
        headers: &HashMap<String, String>,
        status_code: u16,
        raw: &str,
    ) -> EdgeResult<()> {
        let entry = self
            .calls
            .get(call_key)
            .ok_or_else(|| EdgeError::NotFound(call_key.to_string()))?;
        let mut session = entry.lock().await;
        if session.status == CallStatus::Answered {
            return Ok(());
        }
        session.remote_signaling = Some(peer);
        let prev = session.status.as_str();
        session.status = CallStatus::Ringing;
        apply_to_tag(&mut session, headers);
        log_sip_state(call_key, prev, "ringing", &format!("provisional {status_code}"));

        if let Some(contact) = headers.get("contact") {
            if let Some(uri) = extract_uri(contact) {
                if let Some(mut dialog) = session.dialog.clone() {
                    dialog.route_target = uri;
                    session.dialog = Some(dialog);
                }
            }
        }

        if status_code == 183 {
            let body = extract_sdp_body(raw);
            if let Some(parsed) = parse_sdp(&body) {
                session.rtp_remote_host = Some(parsed.remote_ip.clone());
                session.rtp_remote_port = Some(parsed.remote_port);
                log_sip_diag(&format!(
                    "183 SDP call_key={call_key} rtp={}:{}",
                    parsed.remote_ip, parsed.remote_port
                ));
            } else if !body.is_empty() {
                log_sip_warn(&format!(
                    "183 with unparseable SDP call_key={call_key} bytes={}",
                    body.len()
                ));
            }
        }

        let require = headers.get("require").cloned().unwrap_or_default();
        let rseq = headers.get("rseq").cloned().unwrap_or_default();
        log_sip_diag(&format!(
            "provisional {status_code} call_key={call_key} Require={require} RSeq={rseq} To-tag={:?}",
            headers.get("to").and_then(|t| extract_tag(t))
        ));

        let dialog = session.dialog.clone();
        drop(session);

        if requires_100rel(headers) {
            if let (Some(dialog), Some(rseq)) = (dialog, parse_rseq(headers)) {
                let prack_uri = headers
                    .get("contact")
                    .and_then(|c| extract_uri(c))
                    .unwrap_or_else(|| dialog.route_target.clone());
                let prack_cseq = dialog.cseq.saturating_add(1);
                let prack = build_prack(&self.config, &dialog, &prack_uri, rseq, prack_cseq);
                self.send_to(&prack, peer).await?;
                log_sip_diag(&format!("PRACK sent rseq={rseq} call_key={call_key} status={status_code} uri={prack_uri}"));
            } else {
                log_sip_warn(&format!(
                    "100rel required but missing RSeq={rseq} or dialog call_key={call_key}"
                ));
            }
        } else if status_code == 183 {
            log_sip_diag(&format!("183 without Require:100rel call_key={call_key}"));
        }

        Ok(())
    }

    async fn handle_invite_200(
        &self,
        call_key: &str,
        peer: SocketAddr,
        headers: &HashMap<String, String>,
        raw: &str,
    ) -> EdgeResult<()> {
        let body = extract_sdp_body(raw);
        let parsed_sdp = parse_sdp(&body);
        log_sip_diag(&format!(
            "INVITE 200 OK call_key={call_key} peer={peer} sdp_bytes={} parsed={}",
            body.len(),
            parsed_sdp.is_some()
        ));
        if parsed_sdp.is_none() && !body.is_empty() {
            log_sip_warn(&format!(
                "200 OK SDP parse failed call_key={call_key} preview={}",
                truncate_for_log(&body, 200)
            ));
        }

        let entry = self
            .calls
            .get(call_key)
            .ok_or_else(|| EdgeError::NotFound(call_key.to_string()))?;
        let mut session = entry.lock().await;
        if session.status == CallStatus::Answered {
            log_sip_diag(&format!("duplicate INVITE 200 OK ignored call_key={call_key}"));
            return Ok(());
        }

        let prev = session.status.as_str();
        session.remote_signaling = Some(peer);
        apply_to_tag(&mut session, headers);

        if let Some(parsed) = &parsed_sdp {
            session.rtp_remote_host = Some(parsed.remote_ip.clone());
            session.rtp_remote_port = Some(parsed.remote_port);
            log_sip_diag(&format!(
                "answer RTP call_key={call_key} remote={}:{}",
                parsed.remote_ip, parsed.remote_port
            ));
        } else {
            session.error = Some("200 OK without parseable SDP".into());
            log_sip_warn(&format!("200 OK without parseable SDP call_key={call_key}"));
        }

        session.status = CallStatus::Answered;
        session.answered_at = Some(std::time::Instant::now());
        log_sip_state(call_key, prev, "answered", "INVITE 200 OK");

        let mut dialog = session.dialog.clone();
        drop(session);

        if let Some(ref mut dialog) = dialog {
            if let Some(to) = headers.get("to") {
                if let Some(tag) = extract_tag(to) {
                    dialog.remote_tag = Some(tag);
                } else {
                    log_sip_warn(&format!("200 OK missing To tag call_key={call_key}"));
                }
            }
            // Persist remote tag before ACK / transfer follow-up.
            if let Some(entry) = self.calls.get(call_key) {
                let mut session = entry.lock().await;
                session.dialog = Some(dialog.clone());
            }
            let ack = build_ack(&self.config, dialog);
            if let Err(e) = self.send_to(&ack, peer).await {
                log_sip_warn(&format!("ACK send failed call_key={call_key}: {e}"));
            } else {
                log_sip_diag(&format!("ACK sent call_key={call_key} peer={peer}"));
            }
        } else {
            log_sip_warn(&format!("200 OK but no dialog for ACK call_key={call_key}"));
        }

        let is_consult = {
            if let Some(entry) = self.calls.get(call_key) {
                let session = entry.lock().await;
                session.is_consult_leg()
            } else {
                false
            }
        };

        if is_consult {
            // Consultation answered: REFER+Replaces on parent; do not start Pipecat media.
            self.on_consult_answered(call_key).await?;
            return Ok(());
        }

        if let Some(parsed) = parsed_sdp {
            if let Err(e) = self
                .start_media_bridge(call_key, parsed.remote_ip, parsed.remote_port)
                .await
            {
                log_sip_warn(&format!("media bridge failed call_key={call_key}: {e}"));
                if let Some(entry) = self.calls.get(call_key) {
                    let mut session = entry.lock().await;
                    session.error = Some(format!("media bridge: {e}"));
                }
            } else {
                log_sip_diag(&format!("media bridge started call_key={call_key}"));
            }
        }

        Ok(())
    }

    async fn handle_inbound_invite(&self, raw: &str, peer: SocketAddr) -> EdgeResult<()> {
        let headers = parse_headers(raw);
        let call_id = headers.get("call-id").cloned().unwrap_or_else(|| uuid::Uuid::new_v4().to_string());
        let from = headers.get("from").cloned().unwrap_or_default();
        let to = headers.get("to").cloned().unwrap_or_default();
        let via = headers.get("via").cloned().unwrap_or_default();
        let cseq = headers.get("cseq").cloned().unwrap_or_else(|| "1 INVITE".into());
        let from_number = extract_number(&from);
        let to_number = extract_number(&to);
        let remote_tag = extract_tag(&from);

        let id = uuid::Uuid::new_v4().to_string();
        let mut session = CallSession::new_inbound(
            id.clone(),
            from_number.clone(),
            to_number.clone(),
            call_id.clone(),
        );

        let rtp_port = pick_local_rtp_port(self.config.rtp_port_min, self.config.rtp_port_max);
        session.rtp_local_port = Some(rtp_port);
        let local_tag = random_token(10);
        // Option B: Asterisk dials us on 127.0.0.1:5071. Contact + SDP must use
        // loopback — public_ip:5071 is not bound, so ACK/BYE to Contact would miss us
        // and the inbound leg drops (outbound originate path is unchanged).
        let local_ip = if peer.ip().is_loopback() {
            "127.0.0.1".to_string()
        } else {
            self.config.public_ip.clone()
        };
        let contact = format!(
            "<sip:{}:{}>",
            local_ip,
            self.config.local_bind.port()
        );
        let to_uri = extract_uri(&to).unwrap_or_else(|| to.clone());
        let from_uri = extract_uri(&from).unwrap_or_else(|| from.clone());

        let dialog = SipDialog {
            call_id: call_id.clone(),
            local_tag: local_tag.clone(),
            remote_tag: remote_tag.clone(),
            branch: extract_branch(&via).unwrap_or_else(|| format!("z9hG4bK{}", random_token(10))),
            cseq: cseq.split_whitespace().next().unwrap_or("1").parse().unwrap_or(1),
            from_uri,
            from_display: from_number.clone(),
            to_uri: to_uri.clone(),
            to_display: to_number.clone(),
            contact_uri: contact.clone(),
            route_target: extract_uri(&first_request_uri(raw)).unwrap_or(to_uri),
        };
        session.dialog = Some(dialog.clone());

        // 100 Trying must not add a To-tag (RFC 3261); tag appears on 18x/200 only.
        let trying = format!(
            "SIP/2.0 100 Trying\r\nVia: {via}\r\nFrom: {from}\r\nTo: {to}\r\nCall-ID: {call_id}\r\nCSeq: {cseq}\r\nContent-Length: 0\r\n\r\n"
        );
        self.send_to(&trying, peer).await?;

        let sdp = SdpSession::new(&local_ip, rtp_port, self.config.codec);
        let ok = build_200_ok_invite(&self.config, &dialog, &via, &from, &to, &cseq, &call_id, &local_tag, &sdp.to_sdp());
        self.send_to(&ok, peer).await?;

        session.status = CallStatus::Answered;
        session.answered_at = Some(std::time::Instant::now());

        let body = extract_body(raw);
        if let Some(parsed) = parse_sdp(&body) {
            session.rtp_remote_host = Some(parsed.remote_ip.clone());
            session.rtp_remote_port = Some(parsed.remote_port);
            let remote_ip = parsed.remote_ip;
            let remote_port = parsed.remote_port;
            let arc = Arc::new(Mutex::new(session));
            self.calls.insert(id.clone(), arc);
            self.call_id_index.insert(call_id, id.clone());
            log_sip_diag(&format!(
                "inbound INVITE answered call_key={id} peer={peer} rtp={remote_ip}:{remote_port}"
            ));
            self.start_media_bridge(&id, remote_ip, remote_port)
                .await?;
        } else {
            // Keep dialog so ACK/BYE match; media waits until we have remote SDP.
            let arc = Arc::new(Mutex::new(session));
            self.calls.insert(id.clone(), arc);
            self.call_id_index.insert(call_id, id.clone());
            log_sip_warn(&format!(
                "inbound INVITE without SDP call_key={id} peer={peer} — answered, no media yet"
            ));
        }

        Ok(())
    }

    async fn handle_inbound_cancel(&self, raw: &str, peer: SocketAddr) -> EdgeResult<()> {
        let headers = parse_headers(raw);
        let call_id = headers.get("call-id").cloned().unwrap_or_default();
        let via = headers.get("via").cloned().unwrap_or_default();
        let from = headers.get("from").cloned().unwrap_or_default();
        let to = headers.get("to").cloned().unwrap_or_default();
        let cseq = headers.get("cseq").cloned().unwrap_or_default();

        if let Some(call_key) = self.call_id_index.get(&call_id) {
            let key = call_key.value().clone();
            self.mark_call_ended(&key, CallStatus::Canceled, "inbound CANCEL")
                .await?;
            log_sip_diag(&format!("CANCEL processed call_key={key} sip_call_id={call_id}"));
        } else {
            log_sip_unmatched_response(0, &call_id, peer, &self.list_known_call_ids());
            log_sip_warn(&format!("CANCEL for unknown Call-ID={call_id}"));
        }

        let ok = build_200_ok_transaction(&via, &from, &to, &call_id, &cseq);
        self.send_to(&ok, peer).await?;
        Ok(())
    }

    async fn handle_inbound_bye(&self, raw: &str, peer: SocketAddr) -> EdgeResult<()> {
        let headers = parse_headers(raw);
        let call_id = headers.get("call-id").cloned().unwrap_or_default();
        let via = headers.get("via").cloned().unwrap_or_default();
        let from = headers.get("from").cloned().unwrap_or_default();
        let to = headers.get("to").cloned().unwrap_or_default();
        let cseq = headers.get("cseq").cloned().unwrap_or_default();

        if let Some(call_key) = self.call_id_index.get(&call_id) {
            let key = call_key.value().clone();
            self.mark_call_ended(&key, CallStatus::Completed, "inbound BYE")
                .await?;
            log_sip_diag(&format!("BYE processed call_key={key} sip_call_id={call_id}"));
        } else {
            log_sip_warn(&format!("BYE for unknown Call-ID={call_id} from {peer}"));
        }

        let ok = build_200_ok_transaction(&via, &from, &to, &call_id, &cseq);
        self.send_to(&ok, peer).await?;
        Ok(())
    }

    async fn start_media_bridge(
        &self,
        call_id: &str,
        remote_host: String,
        remote_port: u16,
    ) -> EdgeResult<()> {
        let entry = self
            .calls
            .get(call_id)
            .ok_or_else(|| EdgeError::NotFound(call_id.to_string()))?;
        let session = entry.lock().await;
        let local_port = session
            .rtp_local_port
            .ok_or_else(|| EdgeError::Sip("missing local RTP port".into()))?;
        let node_media_url = session
            .node_media_url
            .clone()
            .or_else(|| self.config.node_media_base.clone());
        let from = session.from_number.clone();
        let to = session.to_number.clone();
        let direction = session.direction.clone();
        let sip_call_id = session.sip_call_id.clone();
        drop(session);

        let rtp = RtpSession::bind(local_port).await?;
        let remote: SocketAddr = format!("{remote_host}:{remote_port}")
            .parse()
            .map_err(|e| EdgeError::Sip(format!("invalid rtp addr: {e}")))?;

        let (shutdown_tx, shutdown_rx) = watch::channel(false);
        self.media_shutdown.insert(call_id.to_string(), shutdown_tx);

        let bridge = MediaBridge::new(rtp, remote, call_id.to_string());
        let started = if let Some(url) = node_media_url {
            bridge
                .start_with_node(
                    url,
                    call_id.to_string(),
                    from,
                    to,
                    match direction {
                        CallDirection::Inbound => "inbound",
                        CallDirection::Outbound => "outbound",
                    },
                    sip_call_id,
                    shutdown_rx,
                )
                .await
        } else {
            bridge.start_echo(shutdown_rx).await
        };
        if let Err(e) = started {
            self.media_shutdown.remove(call_id);
            return Err(e);
        }
        Ok(())
    }

    async fn send_to(&self, msg: &str, dest: SocketAddr) -> EdgeResult<()> {
        log_sip_tx(dest, msg);
        self.socket
            .send_to(msg.as_bytes(), dest)
            .await
            .map_err(EdgeError::Io)?;
        Ok(())
    }
}


fn build_200_ok_transaction(via: &str, from: &str, to: &str, call_id: &str, cseq: &str) -> String {
    format!(
        "SIP/2.0 200 OK\r\n\
         Via: {via}\r\n\
         From: {from}\r\n\
         To: {to}\r\n\
         Call-ID: {call_id}\r\n\
         CSeq: {cseq}\r\n\
         Content-Length: 0\r\n\
         \r\n"
    )
}

fn truncate_for_log(s: &str, max: usize) -> String {
    let flat: String = s.lines().take(8).collect::<Vec<_>>().join(" | ");
    if flat.len() <= max {
        flat
    } else {
        format!("{}…", &flat[..max])
    }
}

fn build_invite(config: &AppConfig, dialog: &SipDialog, request_uri: &str, sdp: &str) -> String {
    format!(
        "INVITE {request_uri} SIP/2.0\r\n\
         Via: SIP/2.0/UDP {via};branch={branch};rport\r\n\
         Max-Forwards: 70\r\n\
         From: \"{from_display}\" <{from_uri}>;tag={local_tag}\r\n\
         To: \"{to_display}\" <{to_uri}>\r\n\
         Call-ID: {call_id}\r\n\
         CSeq: {cseq} INVITE\r\n\
         Contact: {contact}\r\n\
         Supported: 100rel\r\n\
         Allow: INVITE, ACK, BYE, CANCEL, OPTIONS, PRACK\r\n\
         User-Agent: {ua}\r\n\
         Content-Type: application/sdp\r\n\
         Content-Length: {len}\r\n\
         \r\n\
         {sdp}",
        request_uri = request_uri,
        via = config.signaling_via(),
        branch = dialog.branch,
        from_display = dialog.from_display,
        from_uri = dialog.from_uri,
        local_tag = dialog.local_tag,
        to_display = dialog.to_display,
        to_uri = dialog.to_uri,
        call_id = dialog.call_id,
        cseq = dialog.cseq,
        contact = dialog.contact_uri,
        ua = config.user_agent,
        len = sdp.len(),
        sdp = sdp
    )
}

fn build_prack(
    config: &AppConfig,
    dialog: &SipDialog,
    request_uri: &str,
    rseq: u32,
    prack_cseq: u32,
) -> String {
    let to_tag = dialog
        .remote_tag
        .as_ref()
        .map(|t| format!(";tag={t}"))
        .unwrap_or_default();
    format!(
        "PRACK {request_uri} SIP/2.0\r\n\
         Via: SIP/2.0/UDP {via};branch={branch};rport\r\n\
         Max-Forwards: 70\r\n\
         From: \"{from_display}\" <{from_uri}>;tag={local_tag}\r\n\
         To: \"{to_display}\" <{to_uri}>{to_tag}\r\n\
         Call-ID: {call_id}\r\n\
         CSeq: {prack_cseq} PRACK\r\n\
         RAck: {rseq} {invite_cseq} INVITE\r\n\
         Contact: {contact}\r\n\
         User-Agent: {ua}\r\n\
         Content-Length: 0\r\n\
         \r\n",
        request_uri = request_uri,
        via = config.signaling_via(),
        branch = format!("z9hG4bK{}", random_token(10)),
        from_display = dialog.from_display,
        from_uri = dialog.from_uri,
        local_tag = dialog.local_tag,
        to_display = dialog.to_display,
        to_uri = dialog.to_uri,
        to_tag = to_tag,
        call_id = dialog.call_id,
        prack_cseq = prack_cseq,
        rseq = rseq,
        invite_cseq = dialog.cseq,
        contact = dialog.contact_uri,
        ua = config.user_agent
    )
}

fn build_ack(config: &AppConfig, dialog: &SipDialog) -> String {
    let to_tag = dialog
        .remote_tag
        .as_ref()
        .map(|t| format!(";tag={t}"))
        .unwrap_or_default();
    format!(
        "ACK {route} SIP/2.0\r\n\
         Via: SIP/2.0/UDP {via};branch={branch};rport\r\n\
         Max-Forwards: 70\r\n\
         From: \"{from_display}\" <{from_uri}>;tag={local_tag}\r\n\
         To: \"{to_display}\" <{to_uri}>{to_tag}\r\n\
         Call-ID: {call_id}\r\n\
         CSeq: {cseq} ACK\r\n\
         Contact: {contact}\r\n\
         User-Agent: {ua}\r\n\
         Content-Length: 0\r\n\
         \r\n",
        route = dialog.route_target,
        via = config.signaling_via(),
        branch = format!("z9hG4bK{}", random_token(10)),
        from_display = dialog.from_display,
        from_uri = dialog.from_uri,
        local_tag = dialog.local_tag,
        to_display = dialog.to_display,
        to_uri = dialog.to_uri,
        to_tag = to_tag,
        call_id = dialog.call_id,
        cseq = dialog.cseq,
        contact = dialog.contact_uri,
        ua = config.user_agent
    )
}

fn build_bye(config: &AppConfig, dialog: &SipDialog) -> String {
    let to_tag = dialog
        .remote_tag
        .as_ref()
        .map(|t| format!(";tag={t}"))
        .unwrap_or_default();
    let cseq = dialog.cseq + 1;
    format!(
        "BYE {route} SIP/2.0\r\n\
         Via: SIP/2.0/UDP {via};branch={branch};rport\r\n\
         Max-Forwards: 70\r\n\
         From: \"{from_display}\" <{from_uri}>;tag={local_tag}\r\n\
         To: \"{to_display}\" <{to_uri}>{to_tag}\r\n\
         Call-ID: {call_id}\r\n\
         CSeq: {cseq} BYE\r\n\
         Contact: {contact}\r\n\
         User-Agent: {ua}\r\n\
         Content-Length: 0\r\n\
         \r\n",
        route = dialog.route_target,
        via = config.signaling_via(),
        branch = format!("z9hG4bK{}", random_token(10)),
        from_display = dialog.from_display,
        from_uri = dialog.from_uri,
        local_tag = dialog.local_tag,
        to_display = dialog.to_display,
        to_uri = dialog.to_uri,
        to_tag = to_tag,
        call_id = dialog.call_id,
        cseq = cseq,
        contact = dialog.contact_uri,
        ua = config.user_agent
    )
}

fn build_cancel(config: &AppConfig, dialog: &SipDialog) -> String {
    format!(
        "CANCEL {route} SIP/2.0\r\n\
         Via: SIP/2.0/UDP {via};branch={branch};rport\r\n\
         Max-Forwards: 70\r\n\
         From: \"{from_display}\" <{from_uri}>;tag={local_tag}\r\n\
         To: \"{to_display}\" <{to_uri}>\r\n\
         Call-ID: {call_id}\r\n\
         CSeq: 1 CANCEL\r\n\
         User-Agent: {ua}\r\n\
         Content-Length: 0\r\n\
         \r\n",
        route = dialog.route_target,
        via = config.signaling_via(),
        branch = dialog.branch.clone(),
        from_display = dialog.from_display,
        from_uri = dialog.from_uri,
        local_tag = dialog.local_tag,
        to_display = dialog.to_display,
        to_uri = dialog.to_uri,
        call_id = dialog.call_id,
        ua = config.user_agent
    )
}

fn build_refer(config: &AppConfig, dialog: &SipDialog, refer_to: &str) -> String {
    let to_tag = dialog
        .remote_tag
        .as_ref()
        .map(|t| format!(";tag={t}"))
        .unwrap_or_default();
    let cseq = dialog.cseq + 1;
    format!(
        "REFER {route} SIP/2.0\r\n\
         Via: SIP/2.0/UDP {via};branch={branch};rport\r\n\
         Max-Forwards: 70\r\n\
         From: \"{from_display}\" <{from_uri}>;tag={local_tag}\r\n\
         To: \"{to_display}\" <{to_uri}>{to_tag}\r\n\
         Call-ID: {call_id}\r\n\
         CSeq: {cseq} REFER\r\n\
         Contact: {contact}\r\n\
         Refer-To: <{refer_to}>\r\n\
         Refer-Sub: true\r\n\
         Allow-Events: refer\r\n\
         User-Agent: {ua}\r\n\
         Content-Length: 0\r\n\
         \r\n",
        route = dialog.route_target,
        via = config.signaling_via(),
        branch = format!("z9hG4bK{}", random_token(10)),
        from_display = dialog.from_display,
        from_uri = dialog.from_uri,
        local_tag = dialog.local_tag,
        to_display = dialog.to_display,
        to_uri = dialog.to_uri,
        to_tag = to_tag,
        call_id = dialog.call_id,
        cseq = cseq,
        contact = dialog.contact_uri,
        refer_to = refer_to,
        ua = config.user_agent
    )
}

fn build_200_ok_invite(
    config: &AppConfig,
    dialog: &SipDialog,
    via: &str,
    from: &str,
    to: &str,
    cseq: &str,
    call_id: &str,
    local_tag: &str,
    sdp: &str,
) -> String {
    format!(
        "SIP/2.0 200 OK\r\n\
         Via: {via}\r\n\
         From: {from}\r\n\
         To: {to};tag={local_tag}\r\n\
         Call-ID: {call_id}\r\n\
         CSeq: {cseq}\r\n\
         Contact: {contact}\r\n\
         User-Agent: {ua}\r\n\
         Content-Type: application/sdp\r\n\
         Content-Length: {len}\r\n\
         \r\n\
         {sdp}",
        via = via,
        from = from,
        to = to,
        local_tag = local_tag,
        call_id = call_id,
        cseq = cseq,
        contact = dialog.contact_uri,
        ua = config.user_agent,
        len = sdp.len(),
        sdp = sdp
    )
}

fn build_200_ok_notify(
    config: &AppConfig,
    dialog: &SipDialog,
    req_headers: &HashMap<String, String>,
    cseq: &str,
) -> String {
    let via = req_headers.get("via").cloned().unwrap_or_default();
    let from = req_headers.get("from").cloned().unwrap_or_default();
    let to = req_headers.get("to").cloned().unwrap_or_default();
    let call_id = req_headers
        .get("call-id")
        .cloned()
        .unwrap_or_else(|| dialog.call_id.clone());
    format!(
        "SIP/2.0 200 OK\r\n\
         Via: {via}\r\n\
         From: {from}\r\n\
         To: {to}\r\n\
         Call-ID: {call_id}\r\n\
         CSeq: {cseq}\r\n\
         Contact: {contact}\r\n\
         User-Agent: {ua}\r\n\
         Content-Length: 0\r\n\
         \r\n",
        via = via,
        from = from,
        to = to,
        call_id = call_id,
        cseq = cseq,
        contact = dialog.contact_uri,
        ua = config.user_agent
    )
}

fn parse_headers(raw: &str) -> HashMap<String, String> {
    let mut map = HashMap::new();
    for line in raw.lines() {
        if line.is_empty() {
            break;
        }
        if let Some((k, v)) = line.split_once(':') {
            map.insert(k.trim().to_lowercase(), v.trim().to_string());
        }
    }
    map
}

fn extract_body(raw: &str) -> String {
    extract_sdp_body(raw)
}

fn apply_to_tag(session: &mut CallSession, headers: &HashMap<String, String>) {
    if let Some(to) = headers.get("to") {
        if let Some(tag) = extract_tag(to) {
            if let Some(mut dialog) = session.dialog.clone() {
                dialog.remote_tag = Some(tag);
                session.dialog = Some(dialog);
            }
        }
    }
}

fn requires_100rel(headers: &HashMap<String, String>) -> bool {
    headers
        .get("require")
        .map(|v| v.to_lowercase().contains("100rel"))
        .unwrap_or(false)
}

fn parse_rseq(headers: &HashMap<String, String>) -> Option<u32> {
    headers.get("rseq")?.trim().parse().ok()
}

fn extract_tag(header: &str) -> Option<String> {
    header
        .split(';')
        .find(|p| p.trim().starts_with("tag="))
        .map(|p| p.trim().trim_start_matches("tag=").to_string())
}

fn extract_branch(via: &str) -> Option<String> {
    via
        .split(';')
        .find(|p| p.trim().starts_with("branch="))
        .map(|p| p.trim().trim_start_matches("branch=").to_string())
}

fn extract_uri(header: &str) -> Option<String> {
    let start = header.find('<')? + 1;
    let end = header.find('>')?;
    Some(header[start..end].to_string())
}

fn extract_number(header: &str) -> String {
    let uri = extract_uri(header).unwrap_or_else(|| header.to_string());
    uri.trim_start_matches("sip:")
        .split('@')
        .next()
        .unwrap_or("")
        .chars()
        .filter(|c| c.is_ascii_digit() || *c == '+')
        .collect()
}

fn first_request_uri(raw: &str) -> String {
    raw.lines()
        .next()
        .unwrap_or_default()
        .split_whitespace()
        .nth(1)
        .unwrap_or_default()
        .to_string()
}
