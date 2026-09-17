import { useEffect, useState } from "react";

import { WEEKDAY_LABELS, type BusinessHoursWindow } from "@/features/agents/types";

const HHMM = /^([01]\d|2[0-3]):([0-5]\d)$/;

export function isValidHhMm(value: string): boolean {
  return HHMM.test(value.trim());
}

function windowsToEditorState(windows: BusinessHoursWindow[] | undefined): {
  selected: boolean[];
  start: string;
  end: string;
} {
  const selected = Array.from({ length: 7 }, () => false);
  let start = "09:00";
  let end = "17:00";
  if (windows?.length) {
    start = windows[0].start || start;
    end = windows[0].end || end;
    for (const row of windows) {
      if (row.weekday >= 0 && row.weekday <= 6) {
        selected[row.weekday] = true;
      }
    }
  }
  return { selected, start, end };
}

export function editorStateToWindows(
  selected: boolean[],
  start: string,
  end: string,
): BusinessHoursWindow[] {
  const s = start.trim();
  const e = end.trim();
  if (!isValidHhMm(s) || !isValidHhMm(e)) {
    return [];
  }
  const out: BusinessHoursWindow[] = [];
  selected.forEach((on, weekday) => {
    if (on) out.push({ weekday, start: s, end: e });
  });
  return out;
}

export function BusinessHoursEditor({
  value,
  onChange,
  disabled,
  resetKey,
}: {
  value: BusinessHoursWindow[];
  onChange: (next: BusinessHoursWindow[]) => void;
  disabled?: boolean;
  /** Re-sync local editor when agent detail reloads. */
  resetKey?: string;
}) {
  const initial = windowsToEditorState(value);
  const [selected, setSelected] = useState(initial.selected);
  const [start, setStart] = useState(initial.start);
  const [end, setEnd] = useState(initial.end);

  useEffect(() => {
    const next = windowsToEditorState(value);
    setSelected(next.selected);
    setStart(next.start);
    setEnd(next.end);
  }, [resetKey]);

  function push(nextSelected: boolean[], nextStart: string, nextEnd: string) {
    setSelected(nextSelected);
    setStart(nextStart);
    setEnd(nextEnd);
    onChange(editorStateToWindows(nextSelected, nextStart, nextEnd));
  }

  const alwaysOpen = !selected.some(Boolean);

  return (
    <div className="grid gap-3 rounded-xl border border-border-default bg-canvas px-3 py-3">
      <div>
        <p className="m-0 text-body-sm font-semibold text-text-primary">Business hours</p>
        <p className="mt-1 mb-0 text-sm text-text-muted">
          Empty (no days) means always open. Times use HH:MM in the agent timezone. Weekday 0 =
          Monday.
        </p>
      </div>
      <div className="flex flex-wrap gap-3">
        {WEEKDAY_LABELS.map((label, weekday) => (
          <label key={label} className="m-0 flex items-center gap-2 text-body font-normal">
            <input
              type="checkbox"
              checked={selected[weekday]}
              disabled={disabled}
              onChange={(event) => {
                const next = [...selected];
                next[weekday] = event.target.checked;
                push(next, start, end);
              }}
            />
            {label.slice(0, 3)}
          </label>
        ))}
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="m-0 grid gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">Start (HH:MM)</span>
          <input
            type="text"
            value={start}
            disabled={disabled || alwaysOpen}
            placeholder="09:00"
            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body disabled:opacity-60"
            onChange={(event) => push(selected, event.target.value, end)}
          />
        </label>
        <label className="m-0 grid gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">End (HH:MM)</span>
          <input
            type="text"
            value={end}
            disabled={disabled || alwaysOpen}
            placeholder="17:00"
            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body disabled:opacity-60"
            onChange={(event) => push(selected, start, event.target.value)}
          />
        </label>
      </div>
      {!alwaysOpen && (!isValidHhMm(start) || !isValidHhMm(end)) ? (
        <p className="m-0 text-sm text-danger" role="alert">
          Start and end must be valid HH:MM (00:00–23:59).
        </p>
      ) : null}
      {alwaysOpen ? (
        <p className="m-0 text-sm text-text-secondary" role="status">
          Always open — no weekday windows selected.
        </p>
      ) : null}
    </div>
  );
}
