import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { usePlatformSettings } from "./hooks/usePlatformSettings";
import { FEATURE_FLAGS, SETTING_GROUPS, type SettingRow } from "./types";

type Tab =
  | "currency"
  | "business"
  | "providers"
  | "flags"
  | "compliance"
  | "agency-flags";

function displayValue(row?: SettingRow): string {
  if (!row) return "—";
  if (row.secret) return row.has_value ? "•••••••• (masked)" : "Not set";
  if (typeof row.value === "boolean") return row.value ? "true" : "false";
  if (row.value == null || row.value === "") return "—";
  return String(row.value);
}

export function PlatformSettingsScreen() {
  const {
    agencyFlags,
    agencies,
    byKey,
    error,
    message,
    loading,
    busy,
    reload,
    updateSetting,
    setAgencyFlag,
  } = usePlatformSettings();

  const [tab, setTab] = useState<Tab>("currency");
  const [editKey, setEditKey] = useState("");

  async function onSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const key = String(form.get("key") || "");
    const raw = String(form.get("value") ?? "");
    const reason = String(form.get("reason") || "");
    const row = byKey.get(key);
    let value: unknown = raw;
    if (key.startsWith("flags.") || key === "compliance.kyc_gate" || key === "security.mfa_required_privileged") {
      value = raw === "true";
    } else if (
      key.includes("_minor") ||
      key.includes("_days") ||
      key.includes("_seconds") ||
      key === "payout.sla_business_days"
    ) {
      value = Number(raw);
    }
    if (row?.secret && !raw.trim()) {
      return;
    }
    try {
      await updateSetting(key, value, reason);
      setEditKey("");
    } catch {
      /* message in hook */
    }
  }

  async function onAgencyFlag(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await setAgencyFlag({
        agency_id: String(form.get("agency_id") || ""),
        flag: String(form.get("flag") || ""),
        enabled: form.get("enabled") === "true",
        reason: String(form.get("reason") || ""),
      });
      event.currentTarget.reset();
    } catch {
      /* message in hook */
    }
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "currency", label: "Currency" },
    { id: "business", label: "Business days" },
    { id: "providers", label: "Providers" },
    { id: "flags", label: "Feature flags" },
    { id: "agency-flags", label: "Agency flags" },
    { id: "compliance", label: "Compliance" },
  ];

  const activeGroup = SETTING_GROUPS.find((group) => group.id === tab);

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            App settings
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA19-001–005 · Permission: settings.manage
          </p>
        </div>
        <ActionButton variant="secondary" onClick={() => void reload()}>
          Refresh
        </ActionButton>
      </div>

      {error ? (
        <p className="mb-4 text-danger" role="alert">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="mb-4 text-body text-text-brand" role="status">
          {message}
        </p>
      ) : null}

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map((item) => (
          <button
            key={item.id}
            type="button"
            className={
              tab === item.id
                ? "rounded-xl bg-brand px-3.5 py-2 text-body font-semibold text-text-inverse"
                : "rounded-xl border border-border-default bg-canvas px-3.5 py-2 text-body font-semibold text-text-secondary"
            }
            onClick={() => {
              setTab(item.id);
              setEditKey("");
            }}
          >
            {item.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="m-0 text-body text-text-muted">Loading settings…</p>
      ) : null}

      {activeGroup ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">{activeGroup.label}</h2>
          <div className="grid gap-3">
            {activeGroup.keys.map((key) => {
              const row = byKey.get(key);
              return (
                <div
                  key={key}
                  className="rounded-xl border border-border-default bg-canvas px-4 py-3"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="m-0 font-mono text-body-sm text-text-muted">{key}</p>
                      <p className="mt-1 mb-0 font-semibold text-text-primary">
                        {displayValue(row)}
                      </p>
                      {row?.secret ? (
                        <StatusBadge tone="warning">secret · masked</StatusBadge>
                      ) : null}
                    </div>
                    <ActionButton
                      variant="outline"
                      onClick={() => setEditKey(editKey === key ? "" : key)}
                    >
                      {editKey === key ? "Cancel" : "Edit"}
                    </ActionButton>
                  </div>
                  {editKey === key ? (
                    <form className="mt-3 grid gap-3" onSubmit={(event) => void onSave(event)}>
                      <input type="hidden" name="key" value={key} />
                      {key.startsWith("flags.") || key === "compliance.kyc_gate" ? (
                        <label className="m-0 grid gap-1.5 font-normal">
                          <span className="text-body-sm text-text-muted">Value</span>
                          <select
                            name="value"
                            defaultValue={String(row?.value ?? false)}
                            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                          >
                            <option value="true">true</option>
                            <option value="false">false</option>
                          </select>
                        </label>
                      ) : (
                        <label className="m-0 grid gap-1.5 font-normal">
                          <span className="text-body-sm text-text-muted">
                            {row?.secret ? "New secret value (stored server-side)" : "Value"}
                          </span>
                          <input
                            name="value"
                            required={!row?.secret}
                            defaultValue={row?.secret ? "" : String(row?.value ?? "")}
                            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                          />
                        </label>
                      )}
                      <label className="m-0 grid gap-1.5 font-normal">
                        <span className="text-body-sm text-text-muted">Reason (required)</span>
                        <input
                          name="reason"
                          required
                          className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                        />
                      </label>
                      <div>
                        <ActionButton type="submit" disabled={busy}>
                          Save setting
                        </ActionButton>
                      </div>
                    </form>
                  ) : null}
                </div>
              );
            })}
          </div>

          {tab === "currency" ? (
            <div className="mt-4">
              <ApiNote>
                SA19-001: V1 exposes commercial.base_currency (and withdrawal bounds). Separate
                supported/display currency lists are not in the settings catalog yet.
              </ApiNote>
            </div>
          ) : null}
          {tab === "business" ? (
            <div className="mt-4">
              <ApiNote>
                SA19-002 (Should): payout.hold_days and payout.sla_business_days are configurable.
                Holiday calendar configuration is not available yet.
              </ApiNote>
            </div>
          ) : null}
          {tab === "providers" ? (
            <div className="mt-4">
              <ApiNote>
                SA19-003: telephony/AI provider names and secret refs plus email sender are
                configurable. Secrets are write-only (GET returns masked). Dedicated payment
                processor settings are not in this catalog yet.
              </ApiNote>
            </div>
          ) : null}
          {tab === "compliance" ? (
            <div className="mt-4">
              <ApiNote>
                SA19-005 (Should): recording disclosure, retention days, and KYC gate are
                configurable. Number-country allowlists are not in the settings catalog yet.
              </ApiNote>
            </div>
          ) : null}
        </article>
      ) : null}

      {tab === "agency-flags" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">Agency feature flags</h2>
          {agencyFlags.length === 0 ? (
            <p className="mb-4 mt-0 text-body text-text-muted">No agency overrides yet.</p>
          ) : (
            <div className="mb-4 overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="text-label uppercase text-text-muted">
                    <th className="border-0 px-2 py-2 text-left">Agency</th>
                    <th className="border-0 px-2 py-2 text-left">Flag</th>
                    <th className="border-0 px-2 py-2 text-left">Enabled</th>
                  </tr>
                </thead>
                <tbody>
                  {agencyFlags.map((row) => (
                    <tr key={`${row.agency_id}-${row.flag}`}>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.agency_id?.slice(0, 8) || "—"}
                      </td>
                      <td className="px-2 py-3 font-semibold text-text-primary">{row.flag}</td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.enabled ? "true" : "false"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <form className="grid max-w-lg gap-3" onSubmit={(event) => void onAgencyFlag(event)}>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Agency</span>
              <select
                name="agency_id"
                required
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="">Select agency</option>
                {agencies.map((agency) => (
                  <option key={agency.id} value={agency.id}>
                    {agency.display_name || agency.id.slice(0, 8)}
                  </option>
                ))}
              </select>
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Flag</span>
              <select
                name="flag"
                required
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                {FEATURE_FLAGS.map((flag) => (
                  <option key={flag} value={flag}>
                    {flag}
                  </option>
                ))}
              </select>
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Enabled</span>
              <select
                name="enabled"
                defaultValue="true"
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="true">true</option>
                <option value="false">false</option>
              </select>
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Reason</span>
              <input
                name="reason"
                required
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <ActionButton type="submit" disabled={busy}>
              Set agency flag
            </ActionButton>
          </form>
          <div className="mt-4">
            <ApiNote>
              SA19-004 (Should): global flags live under flags.* settings; per-agency overrides use
              POST /api/v1/platform/settings/flags.
            </ApiNote>
          </div>
        </article>
      ) : null}
    </section>
  );
}
