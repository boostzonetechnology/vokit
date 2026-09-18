import { FormEvent, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { mapAcceptInviteError } from "@/features/auth/lib/mapAcceptInviteError";
import { validateAcceptInviteForm } from "@/features/auth/lib/validateAcceptInviteForm";
import { acceptInvitation } from "@/features/auth/services/invitation.service";

export function useAcceptInvite() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = useMemo(() => (params.get("token") || "").trim(), [params]);

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [acceptPlatformTerms, setAcceptPlatformTerms] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");

    const validationError = validateAcceptInviteForm({
      token,
      password,
      confirm,
      acceptPlatformTerms,
    });
    if (validationError) {
      setError(validationError);
      return;
    }

    setBusy(true);
    try {
      await acceptInvitation({
        token,
        password,
        accept_platform_terms: true,
      });
      setMessage("Invitation accepted. Redirecting to sign in…");
      window.setTimeout(() => navigate("/login", { replace: true }), 900);
    } catch (cause) {
      setError(mapAcceptInviteError(cause));
    } finally {
      setBusy(false);
    }
  }

  return {
    token,
    password,
    confirm,
    acceptPlatformTerms,
    showPassword,
    error,
    message,
    busy,
    setPassword,
    setConfirm,
    setAcceptPlatformTerms,
    setShowPassword,
    onSubmit,
  };
}
