use std::time::Instant;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum TransferStatus {
    Idle,
    Pending,
    InProgress,
    Succeeded,
    Failed,
}

impl TransferStatus {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Idle => "idle",
            Self::Pending => "pending",
            Self::InProgress => "in_progress",
            Self::Succeeded => "succeeded",
            Self::Failed => "failed",
        }
    }
}

#[derive(Clone, Debug)]
pub struct TransferState {
    pub status: TransferStatus,
    pub to: String,
    /// Consultation outbound call key (edge UUID), if any.
    pub consult_call_key: Option<String>,
    pub refer_cseq: u32,
    pub sip_code: Option<u16>,
    pub reason: Option<String>,
    pub started_at: Instant,
}

impl TransferState {
    pub fn new_pending(to: String, consult_call_key: Option<String>) -> Self {
        Self {
            status: TransferStatus::Pending,
            to,
            consult_call_key,
            refer_cseq: 0,
            sip_code: None,
            reason: None,
            started_at: Instant::now(),
        }
    }
}

/// Parse SIP status code from a message/sipfrag NOTIFY body (e.g. "SIP/2.0 200 OK").
pub fn parse_sipfrag_status_code(body: &str) -> Option<u16> {
    let line = body.lines().next()?.trim();
    let mut parts = line.split_whitespace();
    if parts.next()? != "SIP/2.0" {
        return None;
    }
    parts.next()?.parse().ok()
}

/// Map terminal SIP codes from referred/consult leg to machine reason strings.
pub fn map_sip_code_to_reason(code: u16) -> &'static str {
    match code {
        200 => "answered",
        408 | 480 | 487 => "no_answer",
        486 | 600 | 603 => "no_answer",
        _ if (400..600).contains(&code) => "sip_error",
        _ => "sip_error",
    }
}

/// Build `Refer-To` URI with RFC 3891 Replaces (consult dialog).
///
/// Example: `sip:+1555@host:5070?Replaces=cid%3Bto-tag%3Dx%3Bfrom-tag%3Dy`
pub fn format_refer_to_with_replaces(
    base_uri: &str,
    replaces_call_id: &str,
    to_tag: &str,
    from_tag: &str,
) -> String {
    let replaces_raw = format!("{replaces_call_id};to-tag={to_tag};from-tag={from_tag}");
    let encoded = encode_replaces_param(&replaces_raw);
    format!("{base_uri}?Replaces={encoded}")
}

fn encode_replaces_param(value: &str) -> String {
    let mut out = String::with_capacity(value.len() * 2);
    for c in value.chars() {
        match c {
            ';' => out.push_str("%3B"),
            '=' => out.push_str("%3D"),
            '@' => out.push_str("%40"),
            ',' => out.push_str("%2C"),
            '?' => out.push_str("%3F"),
            ' ' => out.push_str("%20"),
            _ => out.push(c),
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_sipfrag_200() {
        assert_eq!(
            parse_sipfrag_status_code("SIP/2.0 200 OK\r\n"),
            Some(200)
        );
    }

    #[test]
    fn parse_sipfrag_486() {
        assert_eq!(
            parse_sipfrag_status_code("SIP/2.0 486 Busy Here"),
            Some(486)
        );
    }

    #[test]
    fn parse_sipfrag_invalid() {
        assert_eq!(parse_sipfrag_status_code("not sip"), None);
    }

    #[test]
    fn map_reason_codes() {
        assert_eq!(map_sip_code_to_reason(200), "answered");
        assert_eq!(map_sip_code_to_reason(408), "no_answer");
        assert_eq!(map_sip_code_to_reason(486), "no_answer");
        assert_eq!(map_sip_code_to_reason(503), "sip_error");
    }

    #[test]
    fn transfer_status_strings() {
        assert_eq!(TransferStatus::InProgress.as_str(), "in_progress");
        assert_eq!(TransferStatus::Succeeded.as_str(), "succeeded");
    }

    #[test]
    fn refer_to_replaces_encoding() {
        let uri = format_refer_to_with_replaces(
            "sip:+15550001002@192.168.56.100:5070",
            "abc@vokit",
            "remote",
            "local",
        );
        assert!(uri.starts_with("sip:+15550001002@192.168.56.100:5070?Replaces="));
        assert!(uri.contains("%40")); // @ in call-id
        assert!(uri.contains("%3B")); // ;
        assert!(uri.contains("to-tag%3Dremote"));
        assert!(uri.contains("from-tag%3Dlocal"));
    }

    #[test]
    fn new_pending_has_consult_key() {
        let t = TransferState::new_pending("+15550001002".into(), Some("consult-1".into()));
        assert_eq!(t.status, TransferStatus::Pending);
        assert_eq!(t.consult_call_key.as_deref(), Some("consult-1"));
        assert_eq!(t.refer_cseq, 0);
    }
}
