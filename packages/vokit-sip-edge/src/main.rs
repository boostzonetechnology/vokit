mod api;
mod config;
mod error;
mod media;
mod rtp;
mod sip;

use std::sync::Arc;

use tracing::info;
use tracing_subscriber::EnvFilter;

use crate::api::AppState;
use crate::config::AppConfig;
use crate::sip::SipStack;

fn load_dotenv() {
    let paths = [".env", "packages/vokit-sip-edge/.env"];
    for path in paths {
        if dotenvy::from_filename(path).is_ok() {
            eprintln!("[vokit-sip-edge] loaded environment from {path}");
            return;
        }
    }
    let _ = dotenvy::dotenv();
}

#[tokio::main]
async fn main() {
    load_dotenv();

    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::from_default_env()
                .add_directive("vokit_sip_edge=info".parse().unwrap())
                .add_directive("sip=info".parse().unwrap()),
        )
        .init();

    let config = AppConfig::from_env();
    let stack = SipStack::start(config.clone())
        .await
        .expect("failed to start SIP stack");

    let state = AppState::new(stack);
    let app = api::build_router(state);

    let addr = format!("0.0.0.0:{}", config.http_port);
    info!("vokit-sip-edge HTTP listening on {addr}");
    let listener = tokio::net::TcpListener::bind(&addr)
        .await
        .expect("bind http port");
    axum::serve(listener, app)
        .await
        .expect("http server error");
}
