use std::net::SocketAddr;
use std::time::{Duration, Instant};

use super::transfer::TransferState;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CallDirection {
    Inbound,
    Outbound,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CallStatus {
    Pending,
    Ringing,
    Answered,
    Completed,
    Failed,
    Canceled,
}

impl CallStatus {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Pending => "pending",
            Self::Ringing => "ringing",
            Self::Answered => "answered",
            Self::Completed => "completed",
            Self::Failed => "failed",
            Self::Canceled => "canceled",
        }
    }
}

#[derive(Clone, Debug)]
pub struct SipDialog {
    pub call_id: String,
    pub local_tag: String,
    pub remote_tag: Option<String>,
    pub branch: String,
    pub cseq: u32,
    pub from_uri: String,
    pub from_display: String,
    pub to_uri: String,
    pub to_display: String,
    pub contact_uri: String,
    pub route_target: String,
}

#[derive(Clone, Debug)]
pub struct CallSession {
    pub id: String,
    pub direction: CallDirection,
    pub status: CallStatus,
    pub from_number: String,
    pub to_number: String,
    pub sip_call_id: String,
    pub dialog: Option<SipDialog>,
    pub rtp_local_port: Option<u16>,
    pub rtp_remote_host: Option<String>,
    pub rtp_remote_port: Option<u16>,
    pub node_media_url: Option<String>,
    pub remote_signaling: Option<SocketAddr>,
    pub error: Option<String>,
    pub created_at: Instant,
    pub answered_at: Option<Instant>,
    pub ended_at: Option<Instant>,
    pub transfer: Option<TransferState>,
    /// When set, this outbound session is a transfer consultation leg for the parent inbound call.
    pub parent_call_key: Option<String>,
}

impl CallSession {
    pub fn new_outbound(id: String, from_number: String, to_number: String, node_media_url: Option<String>) -> Self {
        let sip_call_id = format!("{}@vokit", uuid::Uuid::new_v4());
        Self {
            id,
            direction: CallDirection::Outbound,
            status: CallStatus::Pending,
            from_number,
            to_number,
            sip_call_id,
            dialog: None,
            rtp_local_port: None,
            rtp_remote_host: None,
            rtp_remote_port: None,
            node_media_url,
            remote_signaling: None,
            error: None,
            created_at: Instant::now(),
            answered_at: None,
            ended_at: None,
            transfer: None,
            parent_call_key: None,
        }
    }

    pub fn new_inbound(id: String, from_number: String, to_number: String, sip_call_id: String) -> Self {
        Self {
            id,
            direction: CallDirection::Inbound,
            status: CallStatus::Ringing,
            from_number,
            to_number,
            sip_call_id,
            dialog: None,
            rtp_local_port: None,
            rtp_remote_host: None,
            rtp_remote_port: None,
            node_media_url: None,
            remote_signaling: None,
            error: None,
            created_at: Instant::now(),
            answered_at: None,
            ended_at: None,
            transfer: None,
            parent_call_key: None,
        }
    }

    pub fn is_consult_leg(&self) -> bool {
        self.parent_call_key.is_some()
    }

    pub fn age(&self) -> Duration {
        self.created_at.elapsed()
    }
}
