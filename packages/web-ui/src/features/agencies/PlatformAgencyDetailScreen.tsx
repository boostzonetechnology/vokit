import { useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

import { FormSectionSkeleton } from "@/components/ui/FormSectionSkeleton";
import { MetricGridSkeleton } from "@/components/ui/MetricCardSkeleton";
import { Skeleton } from "@/components/ui/Skeleton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { AgencyCapabilitiesPanel } from "@/features/agencies/components/AgencyCapabilitiesPanel";
import { AgencyCommissionPanel } from "@/features/agencies/components/AgencyCommissionPanel";
import { AgencyDetailTabBar } from "@/features/agencies/components/AgencyDetailTabBar";
import { AgencyFinancePanel } from "@/features/agencies/components/AgencyFinancePanel";
import { AgencyNotesPanel } from "@/features/agencies/components/AgencyNotesPanel";
import {
  AgencyOverviewPanel,
  AgencyProfilePanel,
} from "@/features/agencies/components/AgencyOverviewProfilePanels";
import { AgencyResourcesPanel } from "@/features/agencies/components/AgencyResourcesPanel";
import { AgencyStatusPanel } from "@/features/agencies/components/AgencyStatusPanel";
import { usePlatformAgencyDetail } from "@/features/agencies/hooks/usePlatformAgencyDetail";
import { agenciesListHref } from "@/features/agencies/lib/routes";
import {
  agencyStatusTone,
  formatAgencyStatus,
} from "@/features/agencies/lib/status";
import type { AgencyDetailTab } from "@/features/agencies/types";

export function PlatformAgencyDetailScreen({ agencyId }: { agencyId: string }) {
  const {
    detail,
    finance,
    customers,
    agents,
    numbers,
    calls,
    integrations,
    team,
    knowledge,
    notes,
    error,
    message,
    loading,
    busy,
    saveProfile,
    setCommission,
    setStatus,
    setCapabilities,
    addNote,
  } = usePlatformAgencyDetail(agencyId);

  const [tab, setTab] = useState<AgencyDetailTab>("overview");

  if (loading && !detail) {
    return (
      <section className="mx-auto max-w-[1200px]">
        <div className="mb-6">
          <Link
            to={agenciesListHref()}
            className="mb-3 inline-flex items-center gap-2 text-body font-semibold text-text-secondary no-underline hover:text-text-primary"
          >
            <ArrowLeft className="size-4" aria-hidden />
            Back to agencies
          </Link>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="mt-2 h-4 w-64 max-w-full" />
        </div>
        <MetricGridSkeleton count={4} />
        <article className="mt-6 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <FormSectionSkeleton fields={5} />
        </article>
      </section>
    );
  }

  if (error || !detail) {
    return (
      <section className="mx-auto max-w-[1200px]">
        <Link
          to={agenciesListHref()}
          className="mb-3 inline-flex items-center gap-2 text-body font-semibold text-text-secondary no-underline hover:text-text-primary"
        >
          <ArrowLeft className="size-4" aria-hidden />
          Back to agencies
        </Link>
        <p className="text-danger" role="alert">
          {error || "Agency not found."}
        </p>
      </section>
    );
  }

  const title = detail.display_name || detail.legal_name || "Agency";
  const subtitle =
    detail.legal_name && detail.legal_name !== detail.display_name
      ? detail.legal_name
      : "Platform agency workspace";
  const currency = detail.currency || finance?.buckets?.currency || "USD";

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6">
        <Link
          to={agenciesListHref()}
          className="mb-3 inline-flex items-center gap-2 text-body font-semibold text-text-secondary no-underline hover:text-text-primary"
        >
          <ArrowLeft className="size-4" aria-hidden />
          Back to agencies
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-3 rounded-2xl border border-border-default bg-surface px-5 py-4 shadow-subtle">
          <div>
            <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
              {title}
            </h1>
            <p className="mt-1 mb-0 text-body text-text-muted">{subtitle}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge tone={agencyStatusTone(detail.status)}>
              {formatAgencyStatus(detail.status)}
            </StatusBadge>
            <StatusBadge tone={agencyStatusTone(detail.tenant_status)}>
              {`DB ${formatAgencyStatus(detail.tenant_status)}`}
            </StatusBadge>
          </div>
        </div>
      </div>

      {message ? (
        <p className="mb-4 text-body text-text-brand" role="status">
          {message}
        </p>
      ) : null}

      <AgencyDetailTabBar tab={tab} onChange={setTab} />

      <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        {tab === "overview" ? <AgencyOverviewPanel detail={detail} /> : null}
        {tab === "profile" ? (
          <AgencyProfilePanel detail={detail} busy={busy} onSave={saveProfile} />
        ) : null}
        {tab === "commission" ? (
          <AgencyCommissionPanel detail={detail} busy={busy} onSave={setCommission} />
        ) : null}
        {tab === "status" ? (
          <AgencyStatusPanel detail={detail} busy={busy} onSave={setStatus} />
        ) : null}
        {tab === "capabilities" ? (
          <AgencyCapabilitiesPanel detail={detail} busy={busy} onSave={setCapabilities} />
        ) : null}
        {tab === "financial" ? (
          <AgencyFinancePanel finance={finance} currency={currency} />
        ) : null}
        {tab === "resources" ? (
          <AgencyResourcesPanel
            customers={customers}
            agents={agents}
            numbers={numbers}
            calls={calls}
            integrations={integrations}
            team={team}
            knowledge={knowledge}
          />
        ) : null}
        {tab === "notes" ? (
          <AgencyNotesPanel notes={notes} busy={busy} onAdd={addNote} />
        ) : null}
      </article>
    </section>
  );
}
