import { FormEvent, useCallback, useEffect, useState } from "react";

import { mapPayoutError } from "@/features/payouts/lib/mapPayoutError";
import {
  createAgencyPayoutMethod,
  disableAgencyPayoutMethod,
  enableAgencyPayoutMethod,
  listAgencyPayoutMethods,
} from "@/features/payouts/services/payoutMethod.service";
import type { PayoutMethodInput, PayoutMethodRecord } from "@/features/payouts/types";

const EMPTY_FORM: PayoutMethodInput = {
  beneficiary_name: "",
  account_identifier: "",
  bank_name: "",
  country: "",
  currency: "USD",
  is_default: true,
};

export function useAgencyPayoutMethods() {
  const [methods, setMethods] = useState<PayoutMethodRecord[]>([]);
  const [usableMethods, setUsableMethods] = useState<PayoutMethodRecord[]>([]);
  const [form, setForm] = useState<PayoutMethodInput>(EMPTY_FORM);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [all, usable] = await Promise.all([
        listAgencyPayoutMethods(),
        listAgencyPayoutMethods({ usable: true }),
      ]);
      setMethods(all);
      setUsableMethods(usable);
      setError("");
    } catch (cause) {
      setError(mapPayoutError(cause, "Failed to load payout methods."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  function updateField<K extends keyof PayoutMethodInput>(key: K, value: PayoutMethodInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      await createAgencyPayoutMethod({
        beneficiary_name: form.beneficiary_name.trim(),
        account_identifier: form.account_identifier.trim(),
        bank_name: form.bank_name.trim(),
        country: form.country.trim().toUpperCase(),
        currency: (form.currency || "USD").trim().toUpperCase(),
        is_default: Boolean(form.is_default),
      });
      setForm(EMPTY_FORM);
      setMessage("Payout method saved.");
      await reload();
    } catch (cause) {
      setMessage(mapPayoutError(cause, "Could not save payout method."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function onDisable(methodId: string) {
    setBusy(true);
    setMessage("");
    try {
      await disableAgencyPayoutMethod(methodId);
      setMessage("Payout method disabled. You can enable it again anytime.");
      await reload();
    } catch (cause) {
      setMessage(mapPayoutError(cause, "Could not disable payout method."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function onEnable(methodId: string) {
    setBusy(true);
    setMessage("");
    try {
      await enableAgencyPayoutMethod(methodId);
      setMessage("Payout method enabled.");
      await reload();
    } catch (cause) {
      setMessage(mapPayoutError(cause, "Could not enable payout method."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    methods,
    usableMethods,
    form,
    updateField,
    error,
    message,
    loading,
    busy,
    reload,
    onSubmit,
    onDisable,
    onEnable,
  };
}
