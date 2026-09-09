mod rest;
mod types;

pub use rest::build_router;
pub use types::{CallView, HealthResponse, OriginateRequest};

use std::sync::Arc;

use crate::sip::StackHandle;

#[derive(Clone)]
pub struct AppState {
    pub stack: StackHandle,
}

impl AppState {
    pub fn new(stack: StackHandle) -> Arc<Self> {
        Arc::new(Self { stack })
    }
}
