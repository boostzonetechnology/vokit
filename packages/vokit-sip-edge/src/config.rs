use std::net::SocketAddr;

#[derive(Clone, Debug)]
pub struct AppConfig {
    pub trunk_host: String,
    pub trunk_port: u16,
    pub transport: Transport,
    pub local_bind: SocketAddr,
    pub public_ip: String,
    pub default_from: String,
    pub domain: String,
    pub codec: Codec,
    pub rtp_port_min: u16,
    pub rtp_port_max: u16,
    pub http_port: u16,
    pub node_media_base: Option<String>,
    pub node_events_url: Option<String>,
    pub user_agent: String,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Transport {
    Udp,
    Tcp,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Codec {
    Pcmu,
}

impl AppConfig {
    pub fn from_env() -> Self {
        let trunk_host = std::env::var("SIP_TRUNK_HOST").unwrap_or_default();
        let trunk_port = std::env::var("SIP_TRUNK_PORT")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(5060);
        let transport = match std::env::var("SIP_TRUNK_TRANSPORT")
            .unwrap_or_else(|_| "udp".into())
            .to_lowercase()
            .as_str()
        {
            "tcp" => Transport::Tcp,
            _ => Transport::Udp,
        };
        let local_bind = std::env::var("SIP_LOCAL_BIND")
            .unwrap_or_else(|_| "0.0.0.0:5060".into())
            .parse()
            .unwrap_or_else(|_| "0.0.0.0:5060".parse().unwrap());
        let public_ip = std::env::var("SIP_PUBLIC_IP").unwrap_or_else(|_| "127.0.0.1".into());
        let default_from = std::env::var("SIP_DEFAULT_FROM").unwrap_or_default();
        let domain = std::env::var("SIP_DOMAIN").unwrap_or_else(|_| public_ip.clone());
        let codec = match std::env::var("SIP_CODECS")
            .unwrap_or_else(|_| "pcmu".into())
            .to_lowercase()
            .as_str()
        {
            _ => Codec::Pcmu,
        };
        let rtp_port_min = std::env::var("RTP_PORT_MIN")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(10000);
        let rtp_port_max = std::env::var("RTP_PORT_MAX")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(20000);
        let http_port = std::env::var("SIP_EDGE_HTTP_PORT")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(8090);
        let node_media_base = std::env::var("SIP_NODE_MEDIA_BASE_URL").ok();
        let node_events_url = std::env::var("SIP_NODE_EVENTS_URL").ok();
        Self {
            trunk_host,
            trunk_port,
            transport,
            local_bind,
            public_ip,
            default_from,
            domain,
            codec,
            rtp_port_min,
            rtp_port_max,
            http_port,
            node_media_base,
            node_events_url,
            user_agent: "vokit-sip-edge/0.1".into(),
        }
    }

    pub fn trunk_addr(&self) -> String {
        format!("{}:{}", self.trunk_host, self.trunk_port)
    }

    /// Public routable address for Via / Contact (never 0.0.0.0).
    pub fn signaling_via(&self) -> String {
        format!("{}:{}", self.public_ip.trim(), self.local_bind.port())
    }

    pub fn trunk_socket_addr(&self) -> Result<SocketAddr, String> {
        self.trunk_addr()
            .parse()
            .map_err(|e| format!("invalid SIP_TRUNK_HOST/SIP_TRUNK_PORT: {e}"))
    }
}
