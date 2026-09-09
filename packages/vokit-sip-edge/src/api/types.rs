use serde::{Deserialize, Serialize};

use crate::sip::{CallDirection, CallSession, CallStatus, TransferStatus};

#[derive(Debug, Deserialize)]
pub struct OriginateRequest {
    pub to: String,
    pub from: Option<String>,
    pub node_media_url: Option<String>,
    pub direction: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct HealthResponse {
    pub ok: bool,
    pub service: &'static str,
    pub codec: &'static str,
}

#[derive(Debug, Serialize)]
pub struct TransferView {
    pub status: String,
    pub to: Option<String>,
    pub reason: Option<String>,
    pub sip_code: Option<u16>,
}

impl TransferView {
    pub fn idle() -> Self {
        Self {
            status: TransferStatus::Idle.as_str().to_string(),
            to: None,
            reason: None,
            sip_code: None,
        }
    }
}

#[derive(Debug, Serialize)]
pub struct CallView {
    pub id: String,
    pub status: String,
    pub direction: String,
    pub from: String,
    pub to: String,
    pub sip_call_id: String,
    pub rtp_local_port: Option<u16>,
    pub rtp_remote_host: Option<String>,
    pub rtp_remote_port: Option<u16>,
    pub error: Option<String>,
    pub transfer: TransferView,
}

impl From<CallSession> for CallView {
    fn from(s: CallSession) -> Self {
        let transfer = s
            .transfer
            .map(|t| TransferView {
                status: t.status.as_str().to_string(),
                to: Some(t.to),
                reason: t.reason,
                sip_code: t.sip_code,
            })
            .unwrap_or_else(TransferView::idle);

        Self {
            id: s.id,
            status: s.status.as_str().to_string(),
            direction: match s.direction {
                CallDirection::Inbound => "inbound".into(),
                CallDirection::Outbound => "outbound".into(),
            },
            from: s.from_number,
            to: s.to_number,
            sip_call_id: s.sip_call_id,
            rtp_local_port: s.rtp_local_port,
            rtp_remote_host: s.rtp_remote_host,
            rtp_remote_port: s.rtp_remote_port,
            error: s.error,
            transfer,
        }
    }
}

#[derive(Debug, Serialize)]
pub struct CallResponse {
    pub call: CallView,
}
