use std::net::{IpAddr, Ipv4Addr};

use crate::config::Codec;

#[derive(Clone, Debug)]
pub struct SdpSession {
    pub local_ip: String,
    pub local_port: u16,
    pub codec: Codec,
}

impl SdpSession {
    pub fn new(local_ip: &str, local_port: u16, codec: Codec) -> Self {
        Self {
            local_ip: local_ip.to_string(),
            local_port,
            codec,
        }
    }

    pub fn to_sdp(&self) -> String {
        let rtpmap = match self.codec {
            Codec::Pcmu => "a=rtpmap:0 PCMU/8000\r\na=sendrecv",
        };
        format!(
            "v=0\r\n\
             o=vokit 0 0 IN IP4 {ip}\r\n\
             s=vokit-sip-edge\r\n\
             c=IN IP4 {ip}\r\n\
             t=0 0\r\n\
             m=audio {port} RTP/AVP 0\r\n\
             {rtpmap}\r\n",
            ip = self.local_ip,
            port = self.local_port,
            rtpmap = rtpmap
        )
    }
}

#[derive(Clone, Debug)]
pub struct ParsedSdp {
    pub remote_ip: String,
    pub remote_port: u16,
    pub payload_type: u8,
}

pub fn parse_sdp(body: &str) -> Option<ParsedSdp> {
    let body = body.trim();
    if body.is_empty() {
        return None;
    }

    let mut audio_port = None;
    let mut connection_ip = None;
    let mut session_ip = None;
    let mut payload_type = 0u8;

    for line in body.lines() {
        let line = line.trim();
        if line.starts_with("m=audio ") {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 2 {
                audio_port = parts[1].parse().ok();
            }
            if parts.len() >= 4 {
                payload_type = parts[3].parse().unwrap_or(0);
            }
        }
        if line.starts_with("c=IN IP4 ") {
            let ip = line.replace("c=IN IP4 ", "").trim().to_string();
            connection_ip = Some(ip);
        }
        if line.starts_with("o=") {
            // o=- 0 0 IN IP4 1.2.3.4 — fallback connection address
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 7 && parts[5] == "IP4" {
                session_ip = Some(parts[6].to_string());
            }
        }
    }

    let remote_ip = connection_ip
        .or(session_ip)
        .filter(|ip| ip != "0.0.0.0" && !ip.is_empty())?;

    Some(ParsedSdp {
        remote_ip,
        remote_port: audio_port?,
        payload_type,
    })
}

pub fn extract_sdp_body(raw: &str) -> String {
    if let Some((_, body)) = raw.split_once("\r\n\r\n") {
        return body.trim_matches('\0').trim().to_string();
    }
    if let Some((_, body)) = raw.split_once("\n\n") {
        return body.trim_matches('\0').trim().to_string();
    }
    String::new()
}

pub fn pick_local_rtp_port(min: u16, max: u16) -> u16 {
    use std::net::UdpSocket;
    for port in min..=max {
        if UdpSocket::bind((Ipv4Addr::UNSPECIFIED, port)).is_ok() {
            return port;
        }
    }
    min
}

pub fn normalize_ip_for_sdp(ip: &str) -> String {
    ip.parse::<IpAddr>()
        .map(|a| a.to_string())
        .unwrap_or_else(|_| ip.to_string())
}
