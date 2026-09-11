import { useMemo } from "react";

import type { PlatformCallRow } from "../hooks/usePlatformDashboard";

type Point = { day: string; connected: number; completed: number };

function bucketCalls(calls: PlatformCallRow[]): Point[] {
  const map = new Map<string, Point>();
  for (const call of calls) {
    const iso = call.started_at ?? call.ended_at;
    if (!iso) {
      continue;
    }
    const day = iso.slice(0, 10);
    const point = map.get(day) ?? { day, connected: 0, completed: 0 };
    point.connected += 1;
    if (call.status === "completed" || call.status === "ended") {
      point.completed += 1;
    }
    map.set(day, point);
  }
  return [...map.values()].sort((a, b) => a.day.localeCompare(b.day)).slice(-30);
}

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

export function CallVolumeChart({ calls }: { calls: PlatformCallRow[] }) {
  const series = useMemo(() => bucketCalls(calls), [calls]);
  const width = 560;
  const height = 180;
  const connected = series.map((p) => p.connected);
  const completed = series.map((p) => p.completed);
  const max = Math.max(1, ...connected, ...completed);
  const connectedPath = toPath(connected, width, height, max);
  const completedPath = toPath(completed, width, height, max);
  const first = series[0]?.day;
  const mid = series[Math.floor(series.length / 2)]?.day;
  const last = series[series.length - 1]?.day;

  return (
    <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h3 className="m-0 text-section text-text-primary">Call volume</h3>
        <span className="rounded-md border border-border-default bg-canvas px-2.5 py-1 text-body-sm text-text-secondary">
          Daily
        </span>
      </div>

      {series.length === 0 ? (
        <p className="m-0 py-16 text-center text-body text-text-muted">
          No call volume in this period yet.
        </p>
      ) : (
        <>
          <svg
            viewBox={`0 0 ${width} ${height}`}
            className="h-[200px] w-full"
            role="img"
            aria-label="Call volume chart"
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
            {connectedPath ? (
              <path d={connectedPath} fill="none" stroke="var(--vokit-brand)" strokeWidth="2.5" />
            ) : null}
            {completedPath ? (
              <path
                d={completedPath}
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
              Connected
            </span>
            <span className="inline-flex items-center gap-1.5 text-text-secondary">
              <span className="size-2 rounded-full bg-success" aria-hidden />
              Completed
            </span>
          </div>
        </>
      )}
    </article>
  );
}
