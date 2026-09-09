use std::net::SocketAddr;
use std::sync::Arc;

use tokio::net::UdpSocket;
use tokio::sync::Mutex;

use crate::error::{EdgeError, EdgeResult};

const RTP_HEADER_LEN: usize = 12;
const FRAME_SAMPLES: u32 = 160; // 20 ms @ 8 kHz
const PT_PCMU: u8 = 0;

pub struct RtpSession {
    socket: Arc<UdpSocket>,
    seq: Arc<Mutex<u16>>,
    timestamp: Arc<Mutex<u32>>,
    ssrc: u32,
}

impl RtpSession {
    pub async fn bind(local_port: u16) -> EdgeResult<Self> {
        let addr = SocketAddr::from(([0, 0, 0, 0], local_port));
        let socket = UdpSocket::bind(addr).await?;
        Ok(Self {
            socket: Arc::new(socket),
            seq: Arc::new(Mutex::new(1)),
            timestamp: Arc::new(Mutex::new(0)),
            ssrc: rand_ssrc(),
        })
    }

    pub fn socket(&self) -> Arc<UdpSocket> {
        self.socket.clone()
    }

    pub async fn send_ulaw(&self, remote: SocketAddr, payload: &[u8]) -> EdgeResult<()> {
        let mut seq = self.seq.lock().await;
        let mut ts = self.timestamp.lock().await;
        let packet = build_rtp_packet(*seq, *ts, self.ssrc, PT_PCMU, payload);
        self.socket.send_to(&packet, remote).await?;
        *seq = seq.wrapping_add(1);
        *ts = ts.wrapping_add(FRAME_SAMPLES);
        Ok(())
    }

    pub async fn recv_ulaw(&self, buf: &mut [u8]) -> EdgeResult<(SocketAddr, usize)> {
        let mut packet = vec![0u8; 1720];
        let (n, addr) = self.socket.recv_from(&mut packet).await?;
        if n <= RTP_HEADER_LEN {
            return Ok((addr, 0));
        }
        let payload_len = n - RTP_HEADER_LEN;
        let copy_len = payload_len.min(buf.len());
        buf[..copy_len].copy_from_slice(&packet[RTP_HEADER_LEN..RTP_HEADER_LEN + copy_len]);
        Ok((addr, copy_len))
    }

    pub fn clone_for_tasks(&self) -> RtpSession {
        RtpSession {
            socket: self.socket.clone(),
            seq: self.seq.clone(),
            timestamp: self.timestamp.clone(),
            ssrc: self.ssrc,
        }
    }
}

fn build_rtp_packet(seq: u16, timestamp: u32, ssrc: u32, pt: u8, payload: &[u8]) -> Vec<u8> {
    let mut out = Vec::with_capacity(RTP_HEADER_LEN + payload.len());
    out.push(0x80);
    out.push(pt & 0x7F);
    out.extend_from_slice(&seq.to_be_bytes());
    out.extend_from_slice(&timestamp.to_be_bytes());
    out.extend_from_slice(&ssrc.to_be_bytes());
    out.extend_from_slice(payload);
    out
}

fn rand_ssrc() -> u32 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .subsec_nanos()
}
