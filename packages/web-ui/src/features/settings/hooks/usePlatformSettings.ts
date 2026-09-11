import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { safeGetList } from "@/features/platform/lib/list";
import type { AgencyFlag, SettingRow, SettingsSnapshot } from "@/features/settings/types";

export function usePlatformSettings() {
  const [settings, setSettings] = useState<SettingRow[]>([]);
  const [agencyFlags, setAgencyFlags] = useState<AgencyFlag[]>([]);
  const [agencies, setAgencies] = useState<Array<{ id: string; display_name?: string }>>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [snap, agencyRows] = await Promise.all([
        apiGet<SettingsSnapshot>("/api/v1/platform/settings"),
        safeGetList<{ id: string; display_name?: string }>("/api/v1/platform/agencies", (path) =>
          apiGet(path),
        ),
      ]);
      setSettings(Array.isArray(snap.settings) ? snap.settings : []);
      setAgencyFlags(Array.isArray(snap.agency_flags) ? snap.agency_flags : []);
      setAgencies(agencyRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load settings.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const byKey = useMemo(() => {
    const map = new Map<string, SettingRow>();
    for (const row of settings) map.set(row.key, row);
    return map;
  }, [settings]);

  async function updateSetting(key: string, value: unknown, reason: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend("/api/v1/platform/settings", "PATCH", { key, value, reason });
      setMessage(`Updated ${key}.`);
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Update failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function setAgencyFlag(input: {
    agency_id: string;
    flag: string;
    enabled: boolean;
    reason: string;
  }) {
    setBusy(true);
    setMessage("");
    try {
      const snap = await apiSend<SettingsSnapshot>("/api/v1/platform/settings/flags", "POST", input);
      if (Array.isArray(snap.agency_flags)) setAgencyFlags(snap.agency_flags);
      setMessage(`Agency flag ${input.flag} updated.`);
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Flag update failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    settings,
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
  };
}
