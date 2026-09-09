use thiserror::Error;

#[derive(Debug, Error)]
pub enum EdgeError {
    #[error("invalid configuration: {0}")]
    Config(String),
    #[error("sip error: {0}")]
    Sip(String),
    #[error("call not found: {0}")]
    NotFound(String),
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),
    #[error("{0}")]
    Other(String),
}

pub type EdgeResult<T> = Result<T, EdgeError>;
