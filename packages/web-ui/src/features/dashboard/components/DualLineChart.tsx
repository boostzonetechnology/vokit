import { useMemo } from "react";

type SeriesPoint = { day: string; a: number; b: number };

function toPath(points: number[], width: number, height: number, max: number): string {
  if (points.length === 0) {
    return "";
  }
  return points
    .map((value, index) => {
      const x = points.length === 1 ? 0 : (index / (points.length - 1)) * width;
      const y = height - (max === 0 ? 0 : (value / max) * height);
      return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

export function DualLineChart({
  title,
  series,
  emptyLabel,
  legendA,
  legendB,
  yFormatter,
}: {
  title: string;
  series: SeriesPoint[];
  emptyLabel: string;
  legendA: string;
  legendB: string;
  yFormatter?: (value: number) => string;
}) {
  const width = 560;
  const height = 180;
  const a = series.map((p) => p.a);
  const b = series.map((p) => p.b);
  const max = Math.max(1, ...a, ...b);
  const pathA = toPath(a, width, height, max);
  const pathB = toPath(b, width, height, max);
  const first = series[0]?.day;
  const mid = series[Math.floor(series.length / 2)]?.day;
  const last = series[series.length - 1]?.day;
  const formatY = yFormatter ?? ((value: number) => String(value));

  return (
    <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h3 className="m-0 text-section text-text-primary">{title}</h3>
        <span className="rounded-md border border-border-default bg-canvas px-2.5 py-1 text-body-sm text-text-secondary">
          Daily
        </span>
      </div>

      {series.length === 0 ? (
        <p className="m-0 py-16 text-center text-body text-text-muted">{emptyLabel}</p>
      ) : (
        <>
          <div className="mb-1 flex justify-between text-body-sm text-text-muted">
            <span>{formatY(max)}</span>
            <span>{formatY(0)}</span>
          </div>
          <svg
            viewBox={`0 0 ${width} ${height}`}
            className="h-[200px] w-full"
            role="img"
            aria-label={title}
          >
            {[0, 0.5, 1].map((ratio) => (
              <line
                key={ratio}
                x1="0"
                x2={width}
                y1={height - ratio * height}
                y2={height - ratio * height}
                stroke="var(--vokit-border-default)"
                strokeWidth="1"
              />
            ))}
            {pathA ? (
              <path d={pathA} fill="none" stroke="var(--vokit-brand)" strokeWidth="2.5" />
            ) : null}
            {pathB ? (
              <path
                d={pathB}
                fill="none"
                stroke="var(--vokit-success)"
                strokeWidth="2.5"
                strokeDasharray="6 4"
              />
            ) : null}
          </svg>
          <div className="mt-2 flex justify-between text-body-sm text-text-muted">
            <span>{first ?? "—"}</span>
            <span>{mid ?? ""}</span>
            <span>{last ?? "—"}</span>
          </div>
          <div className="mt-3 flex gap-4 text-body-sm">
            <span className="inline-flex items-center gap-1.5 text-text-secondary">
              <span className="size-2 rounded-full bg-brand" aria-hidden />
              {legendA}
            </span>
            <span className="inline-flex items-center gap-1.5 text-text-secondary">
              <span className="size-2 rounded-full bg-success" aria-hidden />
              {legendB}
            </span>
          </div>
        </>
      )}
    </article>
  );
}

export function useCallSeries(calls: Array<{ started_at?: string | null; ended_at?: string | null; status?: string }>) {
  return useMemo(() => {
    const map = new Map<string, SeriesPoint>();
    for (const call of calls) {
      const iso = call.started_at ?? call.ended_at;
      if (!iso) continue;
      const day = iso.slice(0, 10);
      const point = map.get(day) ?? { day, a: 0, b: 0 };
      point.a += 1;
      if (call.status === "completed" || call.status === "ended") {
        point.b += 1;
      }
      map.set(day, point);
    }
    return [...map.values()].sort((x, y) => x.day.localeCompare(y.day)).slice(-30);
  }, [calls]);
}

export function useInvoiceSeries(
  invoices: Array<{ paid_at?: string | null; created_at?: string; total_minor?: number; amount_minor?: number; status?: string }>,
) {
  return useMemo(() => {
    const map = new Map<string, SeriesPoint>();
    for (const invoice of invoices) {
      if ((invoice.status ?? "").toLowerCase() !== "paid") continue;
      const iso = invoice.paid_at ?? invoice.created_at;
      if (!iso) continue;
      const day = iso.slice(0, 10);
      const amount = Number(invoice.total_minor ?? invoice.amount_minor ?? 0);
      const point = map.get(day) ?? { day, a: 0, b: 0 };
      point.a += amount;
      point.b += Math.round(amount * 0.3);
      map.set(day, point);
    }
    return [...map.values()].sort((x, y) => x.day.localeCompare(y.day)).slice(-30);
  }, [invoices]);
}
