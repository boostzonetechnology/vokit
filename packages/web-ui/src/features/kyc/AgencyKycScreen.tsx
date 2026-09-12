import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useAgencyKyc } from "./hooks/useAgencyKyc";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "verified") return "success";
  if (
    value === "submitted" ||
    value === "under_review" ||
    value === "incomplete" ||
    value === "more_information_required"
  ) {
    return "warning";
  }
  if (value === "rejected" || value === "suspended" || value === "expired") return "danger";
  return "neutral";
}

export function AgencyKycScreen() {
  const { status, session, error, message, loading, busy, reload, startSession } = useAgencyKyc();

  const caseRow = status?.case;
  const currentStatus = caseRow?.status || status?.status || "not_started";
  const needsResubmit = currentStatus === "more_information_required";
  const verified = currentStatus === "verified";

  return (
    <section className="mx-auto max-w-[900px]">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            KYC
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Application, status, payout gate · AG12
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

      {loading ? (
        <p className="text-body text-text-muted" role="status">
          Loading…
        </p>
      ) : (
        <div className="grid gap-4">
          <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <h2 className="m-0 text-[1.05rem] font-semibold text-text-primary">Status</h2>
              <StatusBadge tone={statusTone(currentStatus)}>{currentStatus}</StatusBadge>
            </div>
            <dl className="m-0 grid gap-2 text-sm">
              <div>
                <dt className="text-text-muted">Visible review note</dt>
                <dd className="m-0 text-text-primary">
                  {caseRow?.external_note || caseRow?.reason_code || "No notes yet"}
                </dd>
              </div>
              <div>
                <dt className="text-text-muted">Next step</dt>
                <dd className="m-0 text-text-primary">{status?.next_step || "—"}</dd>
              </div>
            </dl>
            <ApiNote>AG12-002 — only agency-visible notes are shown; internal notes stay hidden.</ApiNote>
          </article>

          <article
            className={`rounded-xl border p-5 shadow-subtle ${
              verified
                ? "border-border-default bg-surface"
                : "border-danger/40 bg-surface"
            }`}
          >
            <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
              Payout gate
            </h2>
            {status?.payout_eligible ? (
              <p className="m-0 text-body text-text-muted">
                Payouts are eligible while KYC remains Verified.
              </p>
            ) : (
              <p className="m-0 text-body text-danger" role="status">
                Payouts are restricted until KYC is Verified
                {status?.payout_block_reason ? `: ${status.payout_block_reason}` : "."}
              </p>
            )}
            <ApiNote>AG12-004 — payout restriction is shown clearly until Verified.</ApiNote>
          </article>

          <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
              {needsResubmit ? "Resubmit information" : "Complete application"}
            </h2>
            <p className="mt-0 mb-3 text-body text-text-muted">
              KYC evidence is collected through the external hosted provider session. Documents are
              not uploaded into the Vokit portal as the system of record.
            </p>
            <div className="flex flex-wrap gap-2">
              <ActionButton disabled={busy} onClick={() => void startSession()}>
                {needsResubmit ? "Resume / resubmit session" : "Start KYC session"}
              </ActionButton>
              {session?.hosted_url ? (
                <ActionButton
                  variant="outline"
                  onClick={() => window.open(session.hosted_url, "_blank", "noopener,noreferrer")}
                >
                  Open hosted verification
                </ActionButton>
              ) : null}
            </div>
            <ApiNote>
              AG12-001 / AG12-003 — start or resume the provider session to submit or provide
              requested information.
            </ApiNote>
          </article>
        </div>
      )}
    </section>
  );
}
