from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path

from django.conf import settings

from shared_kernel.errors import DomainError

_ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}
_EXT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}
_MAX_BYTES = 5 * 1024 * 1024
_SAFE_NAME = re.compile(r"[^a-zA-Z0-9._-]+")


def proof_root() -> Path:
    configured = getattr(settings, "PAYOUT_PROOF_STORAGE_DIR", None)
    root = Path(configured) if configured else Path(settings.BASE_DIR) / "var" / "payout_proofs"
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def store_proof_file(
    *,
    payout_id: uuid.UUID,
    filename: str,
    content_type: str,
    content: bytes,
) -> tuple[str, str, str]:
    if not content:
        raise DomainError("validation_error", "Proof file is empty.")
    if len(content) > _MAX_BYTES:
        raise DomainError("validation_error", "Proof file must be 5MB or smaller.")
    ctype = (content_type or "").split(";")[0].strip().lower()
    if ctype not in _ALLOWED_TYPES:
        ext = Path(filename or "").suffix.lower()
        ctype = _EXT_TYPES.get(ext, "")
    if ctype not in _ALLOWED_TYPES:
        raise DomainError(
            "validation_error",
            "Proof must be a JPEG, PNG, WebP, or PDF file.",
        )
    stem = _SAFE_NAME.sub("-", Path(filename or "proof").stem)[:48] or "proof"
    ext = _ALLOWED_TYPES[ctype]
    object_ref = f"payout/{payout_id}/proof/{stem}{ext}"
    path = proof_root().joinpath(*Path(object_ref).parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    checksum = f"sha256:{hashlib.sha256(content).hexdigest()}"
    return object_ref, ctype, checksum


def resolve_proof_path(object_ref: str) -> Path:
    ref = (object_ref or "").strip().replace("\\", "/")
    if not ref or ref.startswith("/") or ".." in ref.split("/"):
        raise DomainError("not_found", "Resource not found.", http_status=404)
    path = proof_root().joinpath(*Path(ref).parts).resolve()
    root = proof_root()
    if not str(path).startswith(str(root)) or not path.is_file():
        raise DomainError("not_found", "Resource not found.", http_status=404)
    return path
