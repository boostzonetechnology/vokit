use std::net::SocketAddr;
use std::time::{Duration, Instant};

use futures_util::{SinkExt, StreamExt};
use tokio::sync::watch;
use tokio_tungstenite::{connect_async, tungstenite::Message};
use tracing::{info, warn};

use crate::error::{EdgeError, EdgeResult};
use crate::rtp::ulaw::ULAW_FRAME_BYTES;
use crate::rtp::RtpSession;

/// G.711 / PCMU frame duration — keep RTP egress real-time.
const ULAW_FRAME_MS: u64 = 20;

pub struct MediaBridge {
    rtp: RtpSession,
    remote: SocketAddr,
    call_id: String,
}

impl MediaBridge {
    pub fn new(rtp: RtpSession, remote: SocketAddr, call_id: String) -> Self {
        Self { rtp, remote, call_id }
    }

    pub async fn start_echo(self, mut shutdown: watch::Receiver<bool>) -> EdgeResult<()> {
        let rtp = self.rtp.clone_for_tasks();
        let remote = self.remote;
        tokio::spawn(async move {
            let mut buf = [0u8; ULAW_FRAME_BYTES];
            loop {
                tokio::select! {
                    _ = shutdown.changed() => {
                        if *shutdown.borrow() {
                            break;
                        }
                    }
                    result = rtp.recv_ulaw(&mut buf) => {
                        match result {
                            Ok((_addr, n)) if n > 0 => {
                                let _ = rtp.send_ulaw(remote, &buf[..n]).await;
                            }
                            Ok(_) => {}
                            Err(_) => break,
                        }
                    }
                }
            }
        });
        Ok(())
    }

    pub async fn start_with_node(
        self,
        ws_url: String,
        call_id: String,
        from: String,
        to: String,
        direction: &str,
        sip_call_id: String,
        mut shutdown: watch::Receiver<bool>,
    ) -> EdgeResult<()> {
        let url = append_query(&ws_url, &call_id, &from, &to);
        let (ws_stream, _) = connect_async(&url)
            .await
            .map_err(|e| EdgeError::Other(format!("node media ws connect failed: {e}")))?;
        info!("media bridge connected to node ws call_id={call_id}");

        let (mut ws_tx, mut ws_rx) = ws_stream.split();
        let start = serde_json::json!({
            "type": "start",
            "call_id": call_id,
            "sip_call_id": sip_call_id,
            "from": from,
            "to": to,
            "direction": direction,
        });
        ws_tx
            .send(Message::Text(start.to_string()))
            .await
            .map_err(|e| EdgeError::Other(e.to_string()))?;

        let rtp_to_node = self.rtp.clone_for_tasks();
        let remote = self.remote;
        let call_id_recv = call_id.clone();

        tokio::spawn(async move {
            let mut buf = [0u8; ULAW_FRAME_BYTES];
            let mut end_reason = "rtp_closed";
            loop {
                tokio::select! {
                    _ = shutdown.changed() => {
                        if *shutdown.borrow() {
                            end_reason = "call_ended";
                            break;
                        }
                    }
                    result = rtp_to_node.recv_ulaw(&mut buf) => {
                        match result {
                            Ok((_addr, n)) if n > 0 => {
                                if let Err(e) = ws_tx.send(Message::Binary(buf[..n].to_vec())).await {
                                    warn!("media ws send to node failed call_id={call_id_recv}: {e}");
                                    end_reason = "ws_send_failed";
                                    break;
                                }
                            }
                            Ok(_) => {}
                            Err(e) => {
                                warn!("rtp recv error call_id={call_id_recv}: {e}");
                                break;
                            }
                        }
                    }
                }
            }
            info!("media rtp->ws stopped call_id={call_id_recv} reason={end_reason}");
            // Tell Django to finalize CallRecord, then close the socket so the
            // consumer disconnect path cannot leave a zombie voice session.
            let stop = serde_json::json!({
                "type": "stop",
                "call_id": call_id_recv,
                "reason": end_reason,
            });
            let _ = ws_tx.send(Message::Text(stop.to_string())).await;
            let _ = ws_tx.send(Message::Close(None)).await;
            let _ = ws_tx.close().await;
        });

        let rtp_from_node = self.rtp.clone_for_tasks();
        tokio::spawn(async move {
            let mut next_send = Instant::now();
            while let Some(msg) = ws_rx.next().await {
                match msg {
                    Ok(Message::Binary(data)) => {
                        for chunk in data.chunks(ULAW_FRAME_BYTES) {
                            if chunk.is_empty() {
                                continue;
                            }
                            let now = Instant::now();
                            if next_send > now {
                                tokio::time::sleep(next_send - now).await;
                            }
                            let _ = rtp_from_node.send_ulaw(remote, chunk).await;
                            next_send = Instant::now() + Duration::from_millis(ULAW_FRAME_MS);
                        }
                    }
                    Ok(Message::Text(text)) => {
                        if text.contains("\"clear\"") {
                            // barge-in — reset pacing so next speech starts immediately
                            next_send = Instant::now();
                        }
                    }
                    Ok(Message::Close(_)) | Err(_) => break,
                    _ => {}
                }
            }
        });

        Ok(())
    }
}

fn append_query(base: &str, call_id: &str, from: &str, to: &str) -> String {
    let sep = if base.contains('?') { '&' } else { '?' };
    format!(
        "{base}{sep}call_id={}&from={}&to={}",
        urlencoding(call_id),
        urlencoding(from),
        urlencoding(to)
    )
}

fn urlencoding(s: &str) -> String {
    s.chars()
        .map(|c| match c {
            'A'..='Z' | 'a'..='z' | '0'..='9' | '-' | '_' | '.' | '~' => c.to_string(),
            _ => format!("%{:02X}", c as u8),
        })
        .collect()
}
