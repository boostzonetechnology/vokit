"""Payout method display helpers (AG11-004)."""

from __future__ import annotations


def mask_account_identifier(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    if "*" in text or len(text) <= 4:
        return text
    return f"{'*' * (len(text) - 4)}{text[-4:]}"


def build_method_label(*, bank_name: str, account_identifier: str) -> str:
    bank = (bank_name or "").strip() or "Bank"
    masked = mask_account_identifier(account_identifier) or "****"
    label = f"{bank} · {masked}"
    return label[:64]
