from __future__ import annotations

import json
import logging
import secrets
import uuid
from dataclasses import replace
from datetime import timedelta

from control_plane.customers.application.ports import CustomerIndexRepository
from control_plane.integrations.application.ports import (
    ConnectionIndexRecord,
    ConnectionIndexRepository,
    EndpointIndexRecord,
    EndpointIndexRepository,
    IntegrationAdapter,
    SecretVault,
    WebhookTransport,
)
from control_plane.integrations.domain.policies import (
    assert_action,
    assert_events,
    assert_provider,
    assert_same_customer,
    assert_usable,
    assert_webhook_url,
    provider_supports_action,
    sanitized_tool_error,
)
from control_plane.integrations.domain.types import (
    ALLOWED_EVENT_TYPES,
    MAX_WEBHOOK_ATTEMPTS,
    PROVIDER_CATEGORY,
    ConnectionStatus,
    DeliveryStatus,
    EndpointStatus,
    ProviderKind,
)
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.hmac import sign_hmac_raw
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.agents.service import TenantAgentService
from tenant.integrations.domain import (
    TenantConnectionRecord,
    TenantIntegrationSettings,
    TenantWebhookDelivery,
    TenantWebhookEndpoint,
)
from tenant.integrations.service import TenantIntegrationService

logger = logging.getLogger("vokit.integrations")


class IntegrationControl:
    def __init__(
        self,
        customers: CustomerIndexRepository,
        store: TenantIntegrationService,
        agents: TenantAgentService,
        connections: ConnectionIndexRepository,
        endpoints: EndpointIndexRepository,
        vault: SecretVault,
        adapter: IntegrationAdapter,
        transport: WebhookTransport,
        clock: Clock,
        *,
        allow_http: bool,
    ) -> None:
        self._customers = customers
        self._store = store
        self._agents = agents
        self._connections = connections
        self._endpoints = endpoints
        self._vault = vault
        self._adapter = adapter
        self._transport = transport
        self._clock = clock
        self._allow_http = allow_http

    def providers(self) -> list[dict[str, str]]:
        return [
            {
                "provider": kind.value,
                "category": PROVIDER_CATEGORY[kind].value,
            }
            for kind in ProviderKind
        ]

    def connect(
        self,
        *,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        provider: str,
        credential: str,
        display_name: str = "",
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> dict[str, object]:
        self._authorize_customer(
            tenant_id=tenant_id,
            customer_id=customer_id,
            actor_customer_id=actor_customer_id,
            privileged=privileged,
        )
        if not privileged and actor_customer_id is not None:
            settings = self._store.get_settings(tenant_id, customer_id)
            if settings is None or not settings.self_service:
                raise DomainError("forbidden", "Not permitted.", http_status=403)
        kind = assert_provider(provider)
        secret = (credential or "").strip()
        if len(secret) < 8:
            raise DomainError("validation_error", "credential is required.")
        existing = next(
            (
                row
                for row in self._store.list_connections(tenant_id, customer_id=customer_id)
                if row.provider is kind
            ),
            None,
        )
        now = self._clock.now()
        if existing is not None and existing.status is ConnectionStatus.CONNECTED:
            raise DomainError(
                "conflict_state",
                "Customer already has this provider connection.",
                http_status=409,
            )
        connection_id = existing.connection_id if existing else new_uuid7()
        secret_ref = existing.secret_ref if existing else f"INTOK_{connection_id}"
        self._vault.put(secret_ref, secret)
        row = TenantConnectionRecord(
            connection_id=connection_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            provider=kind,
            status=ConnectionStatus.CONNECTED,
            secret_ref=secret_ref,
            display_name=(display_name or kind.value)[:128],
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        stored = self._store.put_connection(tenant_id, row)
        self._connections.save(self._to_index(stored))
        log_event(
            logger,
            "integration.connected",
            outcome="success",
            tenant_id=str(tenant_id),
            customer_id=str(customer_id),
            provider=kind.value,
        )
        return self._connection_payload(stored)

    def disconnect(
        self,
        *,
        tenant_id: uuid.UUID,
        connection_id: uuid.UUID,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> dict[str, object]:
        row = self._require_connection(
            tenant_id, connection_id, actor_customer_id, privileged
        )
        now = self._clock.now()
        self._vault.delete(row.secret_ref)
        stored = self._store.put_connection(
            tenant_id,
            replace(
                row,
                status=ConnectionStatus.REVOKED,
                revoked_at=now,
                updated_at=now,
            ),
        )
        self._connections.save(self._to_index(stored))
        log_event(
            logger,
            "integration.revoked",
            outcome="success",
            customer_id=str(row.customer_id),
            connection_id=str(connection_id),
        )
        return self._connection_payload(stored)

    def disable(
        self, *, connection_id: uuid.UUID
    ) -> dict[str, object]:
        indexed = self._connections.get(connection_id)
        if indexed is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        row = self._store.get_connection(indexed.tenant_id, connection_id)
        if row is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        stored = self._store.put_connection(
            indexed.tenant_id,
            replace(row, status=ConnectionStatus.DISABLED, updated_at=self._clock.now()),
        )
        self._connections.save(self._to_index(stored))
        log_event(
            logger,
            "integration.disabled",
            outcome="success",
            connection_id=str(connection_id),
        )
        return self._connection_payload(stored)

    def set_self_service(
        self, *, tenant_id: uuid.UUID, customer_id: uuid.UUID, enabled: bool
    ) -> dict[str, object]:
        self._require_customer(tenant_id, customer_id)
        stored = self._store.put_settings(
            tenant_id,
            TenantIntegrationSettings(
                customer_id=customer_id,
                tenant_id=tenant_id,
                self_service=enabled,
                updated_at=self._clock.now(),
            ),
        )
        return {"customer_id": str(customer_id), "self_service": stored.self_service}

    def list_connections(
        self,
        *,
        tenant_id: uuid.UUID | None,
        customer_id: uuid.UUID | None,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> list[dict[str, object]]:
        if actor_customer_id is not None:
            customer_id = actor_customer_id
        if tenant_id is None:
            rows = self._connections.list(customer_id=customer_id)
            return [
                self._connection_payload(item)
                for item in (
                    self._store.get_connection(row.tenant_id, row.connection_id)
                    for row in rows
                )
                if item is not None
            ]
        if customer_id is not None:
            self._authorize_customer(
                tenant_id=tenant_id,
                customer_id=customer_id,
                actor_customer_id=actor_customer_id,
                privileged=privileged,
            )
        rows = self._store.list_connections(tenant_id, customer_id=customer_id)
        if actor_customer_id is not None:
            rows = [row for row in rows if row.customer_id == actor_customer_id]
        return [self._connection_payload(row) for row in rows]

    def test_connection(
        self,
        *,
        tenant_id: uuid.UUID,
        connection_id: uuid.UUID,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> dict[str, object]:
        row = self._require_connection(
            tenant_id, connection_id, actor_customer_id, privileged
        )
        assert_usable(row.status)
        credential = self._vault.get(row.secret_ref)
        action = next(
            (
                name
                for name in ("lookup_customer", "check_order", "invoke_webhook")
                if provider_supports_action(row.provider, name)
            ),
            "invoke_webhook",
        )
        arguments = (
            {"query": "ping"}
            if action == "lookup_customer"
            else {"order_id": "ping"}
            if action == "check_order"
            else {}
        )
        result = self._adapter.execute(
            provider=row.provider,
            action=action,
            customer_id=str(row.customer_id),
            arguments=arguments,
            credential=credential,
        )
        return {"ok": bool(result.get("ok")), "status": row.status.value}

    def create_endpoint(
        self,
        *,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        url: str,
        events: list,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> dict[str, object]:
        self._authorize_customer(
            tenant_id=tenant_id,
            customer_id=customer_id,
            actor_customer_id=actor_customer_id,
            privileged=privileged,
        )
        now = self._clock.now()
        endpoint_id = new_uuid7()
        secret = secrets.token_urlsafe(32)
        secret_ref = f"WHSEC_{endpoint_id}"
        self._vault.put(secret_ref, secret)
        stored = self._store.put_endpoint(
            tenant_id,
            TenantWebhookEndpoint(
                endpoint_id=endpoint_id,
                tenant_id=tenant_id,
                customer_id=customer_id,
                url=assert_webhook_url(url, allow_http=self._allow_http),
                secret_ref=secret_ref,
                status=EndpointStatus.ACTIVE,
                events=assert_events(events),
                created_at=now,
                updated_at=now,
            ),
        )
        self._endpoints.save(
            EndpointIndexRecord(
                endpoint_id=stored.endpoint_id,
                tenant_id=stored.tenant_id,
                customer_id=stored.customer_id,
                status=stored.status.value,
            )
        )
        payload = self._endpoint_payload(stored)
        payload["secret"] = secret
        return payload

    def rotate_secret(
        self,
        *,
        tenant_id: uuid.UUID,
        endpoint_id: uuid.UUID,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> dict[str, object]:
        row = self._require_endpoint(
            tenant_id, endpoint_id, actor_customer_id, privileged
        )
        secret = secrets.token_urlsafe(32)
        self._vault.put(row.secret_ref, secret)
        stored = self._store.put_endpoint(
            tenant_id, replace(row, updated_at=self._clock.now())
        )
        payload = self._endpoint_payload(stored)
        payload["secret"] = secret
        return payload

    def list_endpoints(
        self,
        *,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID | None,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> list[dict[str, object]]:
        if customer_id is not None:
            self._authorize_customer(
                tenant_id=tenant_id,
                customer_id=customer_id,
                actor_customer_id=actor_customer_id,
                privileged=privileged,
            )
        rows = self._store.list_endpoints(tenant_id, customer_id=customer_id)
        if actor_customer_id is not None:
            rows = [row for row in rows if row.customer_id == actor_customer_id]
        return [self._endpoint_payload(row) for row in rows]

    def list_deliveries(
        self,
        *,
        tenant_id: uuid.UUID | None,
        customer_id: uuid.UUID | None,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> list[dict[str, object]]:
        if tenant_id is None:
            raise DomainError("validation_error", "agency scope is required.")
        if customer_id is not None:
            self._authorize_customer(
                tenant_id=tenant_id,
                customer_id=customer_id,
                actor_customer_id=actor_customer_id,
                privileged=privileged,
            )
        rows = self._store.list_deliveries(tenant_id, customer_id=customer_id)
        if actor_customer_id is not None:
            rows = [row for row in rows if row.customer_id == actor_customer_id]
        return [self._delivery_payload(row) for row in rows]

    def emit(
        self,
        *,
        event_type: str,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        object_id: uuid.UUID,
        data: dict[str, object],
    ) -> None:
        name = (event_type or "").strip()
        if name not in ALLOWED_EVENT_TYPES:
            return
        event_id = new_uuid7()
        for endpoint in self._store.list_endpoints(tenant_id, customer_id=customer_id):
            if endpoint.status is not EndpointStatus.ACTIVE:
                continue
            if name not in endpoint.events:
                continue
            self._deliver(
                endpoint,
                event_id=event_id,
                event_type=name,
                object_id=object_id,
                data=data,
            )

    def replay(
        self,
        *,
        tenant_id: uuid.UUID,
        delivery_id: uuid.UUID,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> dict[str, object]:
        prior = self._store.get_delivery(tenant_id, delivery_id)
        if prior is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        self._authorize_customer(
            tenant_id=tenant_id,
            customer_id=prior.customer_id,
            actor_customer_id=actor_customer_id,
            privileged=privileged,
        )
        endpoint = self._store.get_endpoint(tenant_id, prior.endpoint_id)
        if endpoint is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return self._delivery_payload(
            self._deliver(
                endpoint,
                event_id=prior.event_id,
                event_type=prior.event_type,
                object_id=prior.object_id,
                data={"replayed": True, "object_id": str(prior.object_id)},
            )
        )

    def retry_pending(self) -> int:
        retried = 0
        for indexed in self._endpoints.list():
            rows = self._store.list_deliveries(
                indexed.tenant_id, endpoint_id=indexed.endpoint_id
            )
            endpoint = self._store.get_endpoint(indexed.tenant_id, indexed.endpoint_id)
            if endpoint is None:
                continue
            now = self._clock.now()
            for row in rows:
                if row.status is not DeliveryStatus.FAILED:
                    continue
                if row.next_attempt_at is not None and row.next_attempt_at > now:
                    continue
                self._deliver(
                    endpoint,
                    event_id=row.event_id,
                    event_type=row.event_type,
                    object_id=row.object_id,
                    data={"retry": True, "object_id": str(row.object_id)},
                    prior=row,
                )
                retried += 1
        return retried

    def invoke(
        self, *, call, tool: str, arguments: dict | None
    ) -> dict[str, object]:
        name = (tool or "").strip()
        if name == "transfer_call" or name == "request_call_transfer":
            return sanitized_tool_error("invalid_tool")
        try:
            action = assert_action(name)
        except DomainError:
            return sanitized_tool_error("invalid_tool")
        agent = self._agents.get_agent(call.tenant_id, call.agent_id)
        if agent is None or action not in agent.tools:
            return sanitized_tool_error("invalid_tool")
        payload = arguments if isinstance(arguments, dict) else {}
        raw_id = str(payload.get("connection_id") or "").strip()
        try:
            connection = self._resolve_connection(
                tenant_id=call.tenant_id,
                customer_id=call.customer_id,
                action=action,
                connection_id=uuid.UUID(raw_id) if raw_id else None,
            )
            assert_usable(connection.status)
            credential = self._vault.get(connection.secret_ref)
            result = self._adapter.execute(
                provider=connection.provider,
                action=action,
                customer_id=str(call.customer_id),
                arguments=payload,
                credential=credential,
            )
        except DomainError as exc:
            code = "not_found" if exc.http_status == 404 else exc.code
            log_event(
                logger,
                "integration.invoke.failed",
                outcome="denied",
                tool=action,
                call_id=str(call.call_id),
                error=code,
            )
            self.emit(
                event_type="agent.action.failed",
                tenant_id=call.tenant_id,
                customer_id=call.customer_id,
                object_id=call.call_id,
                data={"tool": action, "error": code},
            )
            return sanitized_tool_error(code)
        log_event(
            logger,
            "integration.invoked",
            outcome="success" if result.get("ok") else "failed",
            tool=action,
            customer_id=str(call.customer_id),
            call_id=str(call.call_id),
        )
        self.emit(
            event_type="agent.action.completed"
            if result.get("ok")
            else "agent.action.failed",
            tenant_id=call.tenant_id,
            customer_id=call.customer_id,
            object_id=call.call_id,
            data={"tool": action},
        )
        return {
            "ok": bool(result.get("ok")),
            "error": result.get("error") or None,
            "result": result.get("result") if result.get("ok") else None,
            "continue_call": True,
        }

    def _resolve_connection(
        self,
        *,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        action: str,
        connection_id: uuid.UUID | None,
    ) -> TenantConnectionRecord:
        if connection_id is not None:
            row = self._store.get_connection(tenant_id, connection_id)
            if row is None or row.customer_id != customer_id:
                raise DomainError("not_found", "Resource not found.", http_status=404)
            if not provider_supports_action(row.provider, action):
                raise DomainError("invalid_tool", "Action is not mapped to this connection.")
            return row
        for row in self._store.list_connections(tenant_id, customer_id=customer_id):
            if row.status is ConnectionStatus.CONNECTED and provider_supports_action(
                row.provider, action
            ):
                return row
        raise DomainError(
            "connection_required",
            "No customer connection is available for this action.",
            http_status=409,
        )

    def _deliver(
        self,
        endpoint: TenantWebhookEndpoint,
        *,
        event_id: uuid.UUID,
        event_type: str,
        object_id: uuid.UUID,
        data: dict[str, object],
        prior: TenantWebhookDelivery | None = None,
    ) -> TenantWebhookDelivery:
        delivery_id = new_uuid7()
        now = self._clock.now()
        body = json.dumps(
            {
                "event_id": str(event_id),
                "event_type": event_type,
                "event_version": "1",
                "occurred_at": now.isoformat(),
                "agency_id": str(endpoint.tenant_id),
                "customer_id": str(endpoint.customer_id),
                "object_id": str(object_id),
                "data": data,
                "delivery_id": str(delivery_id),
            },
            default=str,
        ).encode("utf-8")
        secret = self._vault.get(endpoint.secret_ref)
        headers = {
            "Content-Type": "application/json",
            "X-Vokit-Signature": sign_hmac_raw(secret=secret, raw_body=body)
            if secret
            else "",
        }
        attempts = (prior.attempt_count + 1) if prior else 1
        if not secret:
            status = DeliveryStatus.DEAD
            code = None
            error = "signing_secret_missing"
        else:
            code, error = self._transport.post(
                url=endpoint.url, headers=headers, body=body
            )
            if 200 <= code < 300:
                status = DeliveryStatus.DELIVERED
                error = ""
            elif attempts >= MAX_WEBHOOK_ATTEMPTS:
                status = DeliveryStatus.DEAD
            else:
                status = DeliveryStatus.FAILED
        stored = self._store.put_delivery(
            endpoint.tenant_id,
            TenantWebhookDelivery(
                delivery_id=delivery_id,
                tenant_id=endpoint.tenant_id,
                customer_id=endpoint.customer_id,
                endpoint_id=endpoint.endpoint_id,
                event_id=event_id,
                event_type=event_type,
                object_id=object_id,
                status=status,
                attempt_count=attempts,
                response_code=code,
                last_error=error[:255],
                created_at=now,
                next_attempt_at=(
                    now + timedelta(seconds=2**attempts)
                    if status is DeliveryStatus.FAILED
                    else None
                ),
                delivered_at=now if status is DeliveryStatus.DELIVERED else None,
            ),
        )
        log_event(
            logger,
            "webhook.delivered" if status is DeliveryStatus.DELIVERED else "webhook.failed",
            outcome=status.value,
            customer_id=str(endpoint.customer_id),
            event_type=event_type,
            attempt_count=attempts,
            response_code=code,
        )
        return stored

    def _require_customer(self, tenant_id: uuid.UUID, customer_id: uuid.UUID):
        customer = self._customers.get(customer_id)
        if customer is None or customer.tenant_id != tenant_id:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return customer

    def _authorize_customer(
        self,
        *,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> None:
        self._require_customer(tenant_id, customer_id)
        if privileged:
            return
        if actor_customer_id is None:
            return
        assert_same_customer(
            connection_customer=customer_id, actor_customer=actor_customer_id
        )

    def _require_connection(
        self,
        tenant_id: uuid.UUID,
        connection_id: uuid.UUID,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> TenantConnectionRecord:
        row = self._store.get_connection(tenant_id, connection_id)
        if row is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        self._authorize_customer(
            tenant_id=tenant_id,
            customer_id=row.customer_id,
            actor_customer_id=actor_customer_id,
            privileged=privileged,
        )
        return row

    def _require_endpoint(
        self,
        tenant_id: uuid.UUID,
        endpoint_id: uuid.UUID,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> TenantWebhookEndpoint:
        row = self._store.get_endpoint(tenant_id, endpoint_id)
        if row is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        self._authorize_customer(
            tenant_id=tenant_id,
            customer_id=row.customer_id,
            actor_customer_id=actor_customer_id,
            privileged=privileged,
        )
        return row

    def _to_index(self, row: TenantConnectionRecord) -> ConnectionIndexRecord:
        return ConnectionIndexRecord(
            connection_id=row.connection_id,
            tenant_id=row.tenant_id,
            customer_id=row.customer_id,
            provider=row.provider,
            status=row.status,
        )

    def _connection_payload(self, row: TenantConnectionRecord) -> dict[str, object]:
        return {
            "id": str(row.connection_id),
            "agency_id": str(row.tenant_id),
            "customer_id": str(row.customer_id),
            "provider": row.provider.value,
            "status": row.status.value,
            "display_name": row.display_name,
            "has_secret": bool(row.secret_ref),
        }

    def _endpoint_payload(self, row: TenantWebhookEndpoint) -> dict[str, object]:
        return {
            "id": str(row.endpoint_id),
            "agency_id": str(row.tenant_id),
            "customer_id": str(row.customer_id),
            "url": row.url,
            "status": row.status.value,
            "events": list(row.events),
        }

    def _delivery_payload(self, row: TenantWebhookDelivery) -> dict[str, object]:
        return {
            "id": str(row.delivery_id),
            "endpoint_id": str(row.endpoint_id),
            "event_id": str(row.event_id),
            "event_type": row.event_type,
            "object_id": str(row.object_id),
            "customer_id": str(row.customer_id),
            "status": row.status.value,
            "attempt_count": row.attempt_count,
            "response_code": row.response_code,
        }
