use std::net::SocketAddr;
use std::sync::OnceLock;

use tracing::{debug, info, warn};

fn sip_trace_raw_enabled() -> bool {
    static ENABLED: OnceLock<bool> = OnceLock::new();
    *ENABLED.get_or_init(|| {
        matches!(
            std::env::var("SIP_TRACE_RAW").ok().as_deref(),
            Some("1") | Some("true") | Some("yes") | Some("on")
        )
    })
}

pub fn log_sip_rx(peer: SocketAddr, raw: &str) {
    let summary = summarize_sip(raw);
    info!(target: "sip", "RX from {peer} | {summary}");
    if sip_trace_raw_enabled() {
        info!(target: "sip", "RX raw from {peer}:\n{}", raw.trim_end());
    } else {
        debug!(target: "sip", "RX raw from {peer}:\n{}", raw.trim_end());
    }
}

pub fn log_sip_tx(peer: SocketAddr, raw: &str) {
    let summary = summarize_sip(raw);
    info!(target: "sip", "TX to {peer} | {summary}");
    if sip_trace_raw_enabled() {
        info!(target: "sip", "TX raw to {peer}:\n{}", raw.trim_end());
    } else {
        debug!(target: "sip", "TX raw to {peer}:\n{}", raw.trim_end());
    }
}

pub fn summarize_sip(raw: &str) -> String {
    let first = raw.lines().next().unwrap_or("").trim();
    let (call_id, cseq, from, to, require, rseq, reason) = parse_summary_headers(raw);
    format!(
        "{first} | Call-ID={call_id} CSeq={cseq} From={from} To={to} Require={require} RSeq={rseq} Reason={reason}"
    )
}

fn parse_summary_headers(raw: &str) -> (String, String, String, String, String, String, String) {
    let mut call_id = "-".to_string();
    let mut cseq = "-".to_string();
    let mut from = "-".to_string();
    let mut to = "-".to_string();
    let mut require = "-".to_string();
    let mut rseq = "-".to_string();
    let mut reason = "-".to_string();

    for line in raw.lines() {
        if line.is_empty() {
            break;
        }
        if let Some((k, v)) = line.split_once(':') {
            match k.trim().to_lowercase().as_str() {
                "call-id" => call_id = v.trim().to_string(),
                "cseq" => cseq = v.trim().to_string(),
                "from" => from = truncate(v.trim(), 72),
                "to" => to = truncate(v.trim(), 72),
                "require" => require = v.trim().to_string(),
                "rseq" => rseq = v.trim().to_string(),
                "reason" => reason = truncate(v.trim(), 48),
                _ => {}
            }
        }
    }

    (call_id, cseq, from, to, require, rseq, reason)
}

fn truncate(s: &str, max: usize) -> String {
    if s.len() <= max {
        s.to_string()
    } else {
        format!("{}…", &s[..max])
    }
}

pub fn log_sip_unmatched_response(status_code: u16, call_id: &str, peer: SocketAddr, known_ids: &[String]) {
    warn!(
        target: "sip",
        "UNMATCHED SIP response {status_code} Call-ID=\"{call_id}\" from {peer} — active Call-IDs: {known_ids:?}"
    );
}

pub fn log_sip_state(call_key: &str, from_status: &str, to_status: &str, detail: &str) {
    info!(
        target: "sip",
        "call {call_key} status {from_status} -> {to_status} ({detail})"
    );
}

pub fn log_sip_diag(detail: &str) {
    info!(target: "sip", "{detail}");
}

pub fn log_sip_warn(detail: &str) {
    warn!(target: "sip", "{detail}");
}
