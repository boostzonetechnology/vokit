from __future__ import annotations

CURRENT_VERSION = "0010_integrations"

SCHEMA_STATEMENTS: dict[str, tuple[str, ...]] = {
    "0001_isolation": (
        """
        CREATE TABLE IF NOT EXISTS tenant_schema_migrations (
            version VARCHAR(64) PRIMARY KEY,
            applied_at DATETIME(6) NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tenant_isolation_records (
            object_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            payload VARCHAR(255) NOT NULL,
            created_at DATETIME(6) NOT NULL
        )
        """,
    ),
    "0002_lifecycle": (
        """
        CREATE TABLE IF NOT EXISTS agency_profiles (
            tenant_id CHAR(36) PRIMARY KEY,
            display_name VARCHAR(255) NOT NULL,
            legal_name VARCHAR(255) NOT NULL,
            status VARCHAR(32) NOT NULL,
            currency CHAR(3) NOT NULL,
            create_customers TINYINT(1) NOT NULL,
            create_agents TINYINT(1) NOT NULL,
            purchase_numbers TINYINT(1) NOT NULL,
            request_payouts TINYINT(1) NOT NULL,
            existing_customer_services TINYINT(1) NOT NULL,
            updated_at DATETIME(6) NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            display_name VARCHAR(255) NOT NULL,
            status VARCHAR(32) NOT NULL,
            created_at DATETIME(6) NOT NULL,
            updated_at DATETIME(6) NOT NULL,
            INDEX idx_customers_tenant (tenant_id)
        )
        """,
    ),
    "0003_billing": (
        """
        CREATE TABLE IF NOT EXISTS subscriptions (
            subscription_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            customer_id CHAR(36) NOT NULL,
            plan_id CHAR(36) NOT NULL,
            plan_version_id CHAR(36) NOT NULL,
            status VARCHAR(32) NOT NULL,
            cycle VARCHAR(16) NOT NULL,
            created_at DATETIME(6) NOT NULL,
            updated_at DATETIME(6) NOT NULL,
            INDEX idx_sub_tenant_customer (tenant_id, customer_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            customer_id CHAR(36) NOT NULL,
            subscription_id CHAR(36) NULL,
            status VARCHAR(32) NOT NULL,
            currency CHAR(3) NOT NULL,
            total_minor BIGINT NOT NULL,
            created_at DATETIME(6) NOT NULL,
            updated_at DATETIME(6) NOT NULL,
            paid_at DATETIME(6) NULL,
            INDEX idx_inv_tenant_customer (tenant_id, customer_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS invoice_lines (
            line_id CHAR(36) PRIMARY KEY,
            invoice_id CHAR(36) NOT NULL,
            tenant_id CHAR(36) NOT NULL,
            kind VARCHAR(32) NOT NULL,
            description VARCHAR(255) NOT NULL,
            amount_minor BIGINT NOT NULL,
            currency CHAR(3) NOT NULL,
            minutes INT NOT NULL,
            commissionable TINYINT(1) NOT NULL,
            INDEX idx_lines_invoice (invoice_id, tenant_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS payments (
            payment_id CHAR(36) PRIMARY KEY,
            invoice_id CHAR(36) NOT NULL,
            tenant_id CHAR(36) NOT NULL,
            customer_id CHAR(36) NOT NULL,
            processor VARCHAR(32) NOT NULL,
            processor_event_id VARCHAR(128) NOT NULL,
            amount_minor BIGINT NOT NULL,
            currency CHAR(3) NOT NULL,
            status VARCHAR(32) NOT NULL,
            created_at DATETIME(6) NOT NULL,
            UNIQUE KEY uq_pay_processor_event (processor, processor_event_id),
            INDEX idx_pay_invoice (invoice_id, tenant_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS minute_lots (
            lot_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            customer_id CHAR(36) NOT NULL,
            invoice_id CHAR(36) NOT NULL,
            kind VARCHAR(32) NOT NULL,
            granted_minutes INT NOT NULL,
            remaining_minutes INT NOT NULL,
            created_at DATETIME(6) NOT NULL,
            INDEX idx_lots_customer (tenant_id, customer_id)
        )
        """,
    ),
    "0004_risk": (
        """
        CREATE TABLE IF NOT EXISTS agents (
            agent_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            customer_id CHAR(36) NOT NULL,
            display_name VARCHAR(128) NOT NULL,
            status VARCHAR(32) NOT NULL,
            created_at DATETIME(6) NOT NULL,
            updated_at DATETIME(6) NOT NULL,
            INDEX idx_agents_customer (tenant_id, customer_id)
        )
        """,
    ),
    "0005_agents": (
        """
        ALTER TABLE agents
            ADD COLUMN config_json TEXT NULL,
            ADD COLUMN published_version INT NULL,
            ADD COLUMN draft_version INT NOT NULL DEFAULT 1,
            ADD COLUMN template_id CHAR(36) NULL,
            ADD COLUMN customer_can_edit TINYINT(1) NOT NULL DEFAULT 0
        """,
        """
        CREATE TABLE IF NOT EXISTS agent_versions (
            version_id CHAR(36) PRIMARY KEY,
            agent_id CHAR(36) NOT NULL,
            tenant_id CHAR(36) NOT NULL,
            version INT NOT NULL,
            published TINYINT(1) NOT NULL,
            snapshot TEXT NOT NULL,
            created_at DATETIME(6) NOT NULL,
            INDEX idx_agent_versions (tenant_id, agent_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS instruction_layers (
            tenant_id CHAR(36) NOT NULL,
            scope VARCHAR(16) NOT NULL,
            owner_id CHAR(36) NOT NULL,
            body TEXT NOT NULL,
            updated_at DATETIME(6) NOT NULL,
            PRIMARY KEY (tenant_id, scope, owner_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS knowledge_sources (
            source_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            scope VARCHAR(16) NOT NULL,
            owner_id CHAR(36) NOT NULL,
            kind VARCHAR(16) NOT NULL,
            title VARCHAR(128) NOT NULL,
            body TEXT NOT NULL,
            object_ref VARCHAR(128) NOT NULL,
            checksum VARCHAR(128) NOT NULL,
            status VARCHAR(16) NOT NULL,
            group_id VARCHAR(128) NOT NULL,
            customer_can_edit TINYINT(1) NOT NULL DEFAULT 0,
            created_at DATETIME(6) NOT NULL,
            updated_at DATETIME(6) NOT NULL,
            INDEX idx_knowledge_scope (tenant_id, scope)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS knowledge_attachments (
            agent_id CHAR(36) NOT NULL,
            source_id CHAR(36) NOT NULL,
            tenant_id CHAR(36) NOT NULL,
            scope VARCHAR(16) NOT NULL,
            group_id VARCHAR(128) NOT NULL,
            PRIMARY KEY (tenant_id, agent_id, source_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS agent_test_sessions (
            session_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            customer_id CHAR(36) NOT NULL,
            agent_id CHAR(36) NOT NULL,
            kind VARCHAR(16) NOT NULL,
            status VARCHAR(16) NOT NULL,
            created_at DATETIME(6) NOT NULL,
            ended_at DATETIME(6) NULL,
            INDEX idx_sessions_agent (tenant_id, agent_id)
        )
        """,
    ),
    "0006_numbers": (
        """
        CREATE TABLE IF NOT EXISTS number_assignments (
            assignment_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            customer_id CHAR(36) NOT NULL,
            agent_id CHAR(36) NOT NULL,
            phone_number_id CHAR(36) NOT NULL,
            e164 VARCHAR(16) NOT NULL,
            status VARCHAR(32) NOT NULL,
            invoice_id CHAR(36) NULL,
            assigned_at DATETIME(6) NOT NULL,
            released_at DATETIME(6) NULL,
            INDEX idx_assign_tenant_agent (tenant_id, agent_id),
            INDEX idx_assign_number (phone_number_id, tenant_id)
        )
        """,
    ),
    "0007_calls": (
        """
        CREATE TABLE IF NOT EXISTS calls (
            call_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            customer_id CHAR(36) NOT NULL,
            agent_id CHAR(36) NOT NULL,
            phone_number_id CHAR(36) NULL,
            e164 VARCHAR(16) NOT NULL,
            edge_call_id VARCHAR(128) NOT NULL,
            sip_call_id VARCHAR(128) NOT NULL,
            direction VARCHAR(16) NOT NULL,
            status VARCHAR(32) NOT NULL,
            billed_minutes INT NOT NULL DEFAULT 0,
            duration_seconds INT NOT NULL DEFAULT 0,
            end_reason VARCHAR(64) NOT NULL,
            started_at DATETIME(6) NOT NULL,
            ended_at DATETIME(6) NULL,
            UNIQUE KEY uq_calls_edge (tenant_id, edge_call_id),
            INDEX idx_calls_customer (tenant_id, customer_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS call_events (
            event_id CHAR(36) PRIMARY KEY,
            call_id CHAR(36) NOT NULL,
            tenant_id CHAR(36) NOT NULL,
            event_type VARCHAR(64) NOT NULL,
            role VARCHAR(16) NOT NULL,
            reason VARCHAR(64) NOT NULL,
            created_at DATETIME(6) NOT NULL,
            INDEX idx_call_events_call (tenant_id, call_id)
        )
        """,
    ),
    "0008_media": (
        """
        ALTER TABLE calls
            ADD COLUMN remote_e164 VARCHAR(16) NOT NULL DEFAULT '',
            ADD COLUMN transfer_destination_id CHAR(36) NULL,
            ADD COLUMN voicemail_status VARCHAR(16) NOT NULL DEFAULT ''
        """,
        """
        CREATE TABLE IF NOT EXISTS transfer_destinations (
            destination_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            customer_id CHAR(36) NOT NULL,
            kind VARCHAR(16) NOT NULL,
            label VARCHAR(128) NOT NULL,
            target VARCHAR(64) NOT NULL,
            members_json TEXT NOT NULL,
            no_answer_seconds INT NOT NULL DEFAULT 25,
            status VARCHAR(16) NOT NULL,
            created_at DATETIME(6) NOT NULL,
            updated_at DATETIME(6) NOT NULL,
            INDEX idx_xfer_tenant_customer (tenant_id, customer_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS voicemail_messages (
            message_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            customer_id CHAR(36) NOT NULL,
            agent_id CHAR(36) NOT NULL,
            call_id CHAR(36) NOT NULL,
            direction VARCHAR(16) NOT NULL,
            status VARCHAR(16) NOT NULL,
            object_ref VARCHAR(255) NOT NULL,
            duration_seconds INT NOT NULL DEFAULT 0,
            created_at DATETIME(6) NOT NULL,
            updated_at DATETIME(6) NOT NULL,
            INDEX idx_vm_call (tenant_id, call_id),
            INDEX idx_vm_customer (tenant_id, customer_id)
        )
        """,
    ),
    "0009_recordings": (
        """
        CREATE TABLE IF NOT EXISTS recording_artifacts (
            artifact_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            customer_id CHAR(36) NOT NULL,
            call_id CHAR(36) NOT NULL,
            kind VARCHAR(32) NOT NULL,
            object_key VARCHAR(255) NOT NULL,
            content_type VARCHAR(128) NOT NULL,
            size_bytes BIGINT NOT NULL,
            checksum VARCHAR(80) NOT NULL,
            status VARCHAR(16) NOT NULL,
            legal_hold TINYINT(1) NOT NULL DEFAULT 0,
            retention_until DATETIME(6) NOT NULL,
            provider_ref VARCHAR(128) NOT NULL,
            created_at DATETIME(6) NOT NULL,
            available_at DATETIME(6) NULL,
            deleted_at DATETIME(6) NULL,
            UNIQUE KEY uq_artifact_object (tenant_id, object_key),
            INDEX idx_artifact_call (tenant_id, call_id),
            INDEX idx_artifact_customer (tenant_id, customer_id)
        )
        """,
    ),
    "0010_integrations": (
        """
        CREATE TABLE IF NOT EXISTS integration_connections (
            connection_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            customer_id CHAR(36) NOT NULL,
            provider VARCHAR(32) NOT NULL,
            status VARCHAR(16) NOT NULL,
            secret_ref VARCHAR(128) NOT NULL,
            display_name VARCHAR(128) NOT NULL,
            created_at DATETIME(6) NOT NULL,
            updated_at DATETIME(6) NOT NULL,
            revoked_at DATETIME(6) NULL,
            UNIQUE KEY uq_int_customer_provider (tenant_id, customer_id, provider),
            INDEX idx_int_customer (tenant_id, customer_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS integration_settings (
            customer_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            self_service TINYINT(1) NOT NULL DEFAULT 0,
            updated_at DATETIME(6) NOT NULL,
            INDEX idx_int_settings_tenant (tenant_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS webhook_endpoints (
            endpoint_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            customer_id CHAR(36) NOT NULL,
            url VARCHAR(512) NOT NULL,
            secret_ref VARCHAR(128) NOT NULL,
            status VARCHAR(16) NOT NULL,
            events_json TEXT NOT NULL,
            created_at DATETIME(6) NOT NULL,
            updated_at DATETIME(6) NOT NULL,
            INDEX idx_wh_customer (tenant_id, customer_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS webhook_deliveries (
            delivery_id CHAR(36) PRIMARY KEY,
            tenant_id CHAR(36) NOT NULL,
            customer_id CHAR(36) NOT NULL,
            endpoint_id CHAR(36) NOT NULL,
            event_id CHAR(36) NOT NULL,
            event_type VARCHAR(64) NOT NULL,
            object_id CHAR(36) NOT NULL,
            status VARCHAR(16) NOT NULL,
            attempt_count INT NOT NULL DEFAULT 0,
            response_code INT NULL,
            last_error VARCHAR(255) NOT NULL,
            created_at DATETIME(6) NOT NULL,
            next_attempt_at DATETIME(6) NULL,
            delivered_at DATETIME(6) NULL,
            INDEX idx_whd_customer (tenant_id, customer_id),
            INDEX idx_whd_endpoint (tenant_id, endpoint_id)
        )
        """,
    ),
}

VERSION_ORDER = (
    "0001_isolation",
    "0002_lifecycle",
    "0003_billing",
    "0004_risk",
    "0005_agents",
    "0006_numbers",
    "0007_calls",
    "0008_media",
    "0009_recordings",
    "0010_integrations",
)
