pub fn sanitize_number(input: &str) -> String {
    let trimmed = input.trim();
    if trimmed.starts_with('+') {
        format!("+{}", trimmed.chars().skip(1).filter(|c| c.is_ascii_digit()).collect::<String>())
    } else {
        trimmed.chars().filter(|c| c.is_ascii_digit()).collect()
    }
}

pub fn sip_uri(number: &str, host: &str, port: u16) -> String {
    let n = sanitize_number(number);
    if port == 5060 {
        format!("sip:{n}@{host}")
    } else {
        format!("sip:{n}@{host}:{port}")
    }
}

pub fn random_token(len: usize) -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let seed = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    format!("{:x}", seed)[..len.min(32)].to_string()
}
