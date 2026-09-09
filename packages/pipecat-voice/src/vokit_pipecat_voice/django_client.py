"""HTTP client for Django internal voice-session APIs (OQ-034 / OQ-035)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from vokit_pipecat_voice.config import PipecatVoiceConfig

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10.0
TRANSFER_POLL_INTERVAL_SECONDS = 2.0


class DjangoUnreachable(Exception):
    """Django control plane could not be reached — fail closed (OQ-035)."""


class DjangoVoiceClient:
    def __init__(self, config: PipecatVoiceConfig) -> None:
        self._config = config
        self._headers = {
            "Content-Type": "application/json",
            "X-Vokit-Internal-Token": config.internal_telephony_token,
        }

    def _url(self, path: str) -> str:
        return f"{self._config.django_base}{path}"

    async def bootstrap(
        self,
        *,
        did: str,
        edge_call_id: str,
        from_number: str,
        sip_call_id: str,
        direction: str,
    ) -> dict[str, Any]:
        return await self._post(
            "/internal/telephony/v1/voice-session/bootstrap/",
            {
                "did": did,
                "edge_call_id": edge_call_id,
                "from_number": from_number,
                "sip_call_id": sip_call_id,
                "direction": direction,
            },
        )

    async def send_event(
        self,
        *,
        edge_call_id: str,
        event_type: str,
        role: str = "",
        text: str = "",
        reason: str = "",
    ) -> dict[str, Any]:
        return await self._post(
            "/internal/telephony/v1/voice-session/events/",
            {
                "edge_call_id": edge_call_id,
                "event_type": event_type,
                "role": role,
                "text": text,
                "reason": reason,
            },
        )

    async def end_session(
        self,
        *,
        edge_call_id: str,
        reason: str = "",
        status: str = "",
    ) -> dict[str, Any]:
        try:
            return await self._post(
                "/internal/telephony/v1/voice-session/end/",
                {
                    "edge_call_id": edge_call_id,
                    "reason": reason,
                    "status": status,
                },
            )
        except DjangoUnreachable:
            logger.error(
                "django unreachable at session end edge_call_id=%s — cannot finalize",
                edge_call_id,
            )
            raise

    async def request_transfer(self, *, edge_call_id: str) -> dict[str, Any]:
        return await self._post(
            "/internal/telephony/v1/voice-session/transfer/",
            {"edge_call_id": edge_call_id},
        )

    async def get_transfer_status(self, *, edge_call_id: str) -> dict[str, Any]:
        return await self._get(
            "/internal/telephony/v1/voice-session/transfer/status/",
            {"edge_call_id": edge_call_id},
        )

    async def poll_transfer_until_terminal(
        self,
        *,
        edge_call_id: str,
        poll_interval: float = TRANSFER_POLL_INTERVAL_SECONDS,
    ) -> dict[str, Any]:
        while True:
            result = await self.get_transfer_status(edge_call_id=edge_call_id)
            if result.get("status") != "pending":
                return result
            await asyncio.sleep(poll_interval)

    async def training_bootstrap(self, *, session_token: str) -> dict[str, Any]:
        return await self._post(
            "/internal/telephony/v1/training-session/bootstrap/",
            {"session_token": session_token},
        )

    async def training_propose(
        self,
        *,
        session_token: str,
        kind: str,
        name: str,
        body: str,
        scope: str = "",
    ) -> dict[str, Any]:
        return await self._post(
            "/internal/telephony/v1/training-session/propose/",
            {
                "session_token": session_token,
                "kind": kind,
                "name": name,
                "body": body,
                "scope": scope,
            },
        )

    async def training_confirm(self, *, session_token: str) -> dict[str, Any]:
        return await self._post(
            "/internal/telephony/v1/training-session/confirm/",
            {"session_token": session_token},
        )

    async def training_end(self, *, session_token: str) -> dict[str, Any]:
        return await self._post(
            "/internal/telephony/v1/training-session/end/",
            {"session_token": session_token},
        )

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = self._url(path)
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.post(url, headers=self._headers, json=payload)
        except httpx.HTTPError as exc:
            logger.error("django control request failed path=%s: %s", path, exc)
            raise DjangoUnreachable(str(exc)) from exc

        if response.status_code in {401, 403}:
            raise DjangoUnreachable(f"django auth failed status={response.status_code}")
        if response.status_code >= 500:
            raise DjangoUnreachable(f"django error status={response.status_code}")
        if response.status_code >= 400:
            raise DjangoUnreachable(
                f"django rejected path={path} status={response.status_code}"
            )
        try:
            body = response.json()
        except ValueError as exc:
            raise DjangoUnreachable("django returned non-json") from exc
        if not isinstance(body, dict):
            raise DjangoUnreachable("django returned unexpected body")
        data = body.get("data", body)
        if not isinstance(data, dict):
            raise DjangoUnreachable("django returned unexpected data")
        return data

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = self._url(path)
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.get(url, headers=self._headers, params=params)
        except httpx.HTTPError as exc:
            logger.error("django control request failed path=%s: %s", path, exc)
            raise DjangoUnreachable(str(exc)) from exc

        if response.status_code in {401, 403}:
            raise DjangoUnreachable(f"django auth failed status={response.status_code}")
        if response.status_code >= 500:
            raise DjangoUnreachable(f"django error status={response.status_code}")
        if response.status_code >= 400:
            raise DjangoUnreachable(
                f"django rejected path={path} status={response.status_code}"
            )
        try:
            body = response.json()
        except ValueError as exc:
            raise DjangoUnreachable("django returned non-json") from exc
        if not isinstance(body, dict):
            raise DjangoUnreachable("django returned unexpected body")
        data = body.get("data", body)
        if not isinstance(data, dict):
            raise DjangoUnreachable("django returned unexpected data")
        return data
