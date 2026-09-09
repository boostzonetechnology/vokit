"""Phone-path knowledge retrieve helpers (no Django hop)."""
from __future__ import annotations

import re

BACKCHANNELS = {
    "ok",
    "okay",
    "yes",
    "yeah",
    "yep",
    "no",
    "nope",
    "uh huh",
    "mm",
    "hmm",
    "mhm",
    "thanks",
    "thank you",
    "hi",
    "hello",
    "hey",
}

FACTUAL_HINTS = (
    "hour",
    "open",
    "close",
    "price",
    "cost",
    "policy",
    "faq",
    "address",
    "location",
    "when",
    "what time",
    "how much",
    "where",
)

REASONING_HINTS = (
    "should i",
    "book",
    "schedule",
    "transfer me",
    "help me decide",
    "what would you",
    "recommend",
    "can you call",
)

KNOWLEDGE_MARKER = "[Retrieved knowledge]"


def should_retrieve(text: str) -> bool:
    cleaned = (text or "").strip().lower()
    if not cleaned:
        return False
    if cleaned in BACKCHANNELS:
        return False
    words = re.findall(r"[a-z0-9']+", cleaned)
    if len(words) <= 2 and not cleaned.endswith("?"):
        return False
    if len(cleaned) < 8:
        return False
    return True


def looks_factual(text: str) -> bool:
    cleaned = (text or "").strip().lower()
    if any(hint in cleaned for hint in REASONING_HINTS):
        return False
    return cleaned.endswith("?") or any(hint in cleaned for hint in FACTUAL_HINTS)


def snippet_speakable(text: str, *, max_chars: int = 400) -> bool:
    body = (text or "").strip()
    return bool(body) and len(body) <= max_chars


def should_skip_llm(
    *,
    skip_llm_enabled: bool,
    query: str,
    top_score: float,
    snippet: str,
    score_threshold: float,
) -> bool:
    if not skip_llm_enabled:
        return False
    if top_score < score_threshold:
        return False
    if not looks_factual(query):
        return False
    if not snippet_speakable(snippet):
        return False
    return True
