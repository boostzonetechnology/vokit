use axum::extract::{Path, State};
use axum::http::StatusCode;
use axum::response::IntoResponse;
use axum::routing::{delete, get, post};
use axum::{Json, Router};
use serde::Deserialize;
use std::sync::Arc;
use tracing::info;

use crate::api::types::{CallResponse, CallView, HealthResponse, OriginateRequest};
use crate::api::AppState;
use crate::error::EdgeError;

pub fn build_router(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/health", get(health))
        .route("/v1/calls", post(originate).get(list_calls))
        .route("/v1/calls/:id", get(get_call).delete(hangup))
        .route("/v1/calls/:id/transfer", post(transfer))
        .with_state(state)
}

async fn health(State(state): State<Arc<AppState>>) -> Json<HealthResponse> {
    let _ = state.stack.config();
    Json(HealthResponse {
        ok: true,
        service: "vokit-sip-edge",
        codec: "pcmu",
    })
}

async fn originate(
    State(state): State<Arc<AppState>>,
    Json(body): Json<OriginateRequest>,
) -> Result<impl IntoResponse, AppError> {
    let cfg = state.stack.config();
    let from = body
        .from
        .filter(|s| !s.trim().is_empty())
        .unwrap_or_else(|| cfg.default_from.clone());
    if from.trim().is_empty() {
        return Err(AppError(EdgeError::Config(
            "from number is required (SIP_DEFAULT_FROM)".into(),
        )));
    }
    let to = body.to.trim().to_string();
    if to.is_empty() {
        return Err(AppError(EdgeError::Config("to number is required".into())));
    }

    let node_media = body
        .node_media_url
        .filter(|s| !s.trim().is_empty())
        .or_else(|| cfg.node_media_base.clone());

    info!("originate to={to} from={from}");
    let session = state
        .stack
        .create_outbound(&from, &to, node_media)
        .await
        .map_err(AppError)?;
    Ok((StatusCode::CREATED, Json(CallResponse { call: session.into() })))
}

async fn list_calls(State(state): State<Arc<AppState>>) -> Json<Vec<CallView>> {
    let calls = state.stack.list_calls().await;
    Json(calls.into_iter().map(Into::into).collect())
}

async fn get_call(
    State(state): State<Arc<AppState>>,
    Path(id): Path<String>,
) -> Result<Json<CallResponse>, AppError> {
    let call = state
        .stack
        .get_call(&id)
        .await
        .ok_or_else(|| AppError(EdgeError::NotFound(id.clone())))?;
    Ok(Json(CallResponse { call: call.into() }))
}

async fn hangup(
    State(state): State<Arc<AppState>>,
    Path(id): Path<String>,
) -> Result<StatusCode, AppError> {
    state.stack.hangup(&id).await.map_err(AppError)?;
    Ok(StatusCode::NO_CONTENT)
}

#[derive(Debug, Deserialize)]
struct TransferBody {
    to: String,
    max_timeout_seconds: Option<u32>,
}

async fn transfer(
    State(state): State<Arc<AppState>>,
    Path(id): Path<String>,
    Json(body): Json<TransferBody>,
) -> Result<StatusCode, AppError> {
    let to = body.to.trim().to_string();
    if to.is_empty() {
        return Err(AppError(EdgeError::Config("to number is required".into())));
    }
    state
        .stack
        .transfer(&id, &to, body.max_timeout_seconds)
        .await
        .map_err(AppError)?;
    Ok(StatusCode::ACCEPTED)
}

struct AppError(EdgeError);

impl IntoResponse for AppError {
    fn into_response(self) -> axum::response::Response {
        let status = match &self.0 {
            EdgeError::NotFound(_) => StatusCode::NOT_FOUND,
            EdgeError::Config(_) => StatusCode::BAD_REQUEST,
            _ => StatusCode::INTERNAL_SERVER_ERROR,
        };
        (
            status,
            Json(serde_json::json!({ "error": self.0.to_string() })),
        )
            .into_response()
    }
}
