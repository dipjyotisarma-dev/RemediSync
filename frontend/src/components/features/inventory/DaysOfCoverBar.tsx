import * as React from "react";
import { formatDaysOfCover } from "@/lib/format";
import { cn } from "@/lib/cn";

export interface DaysOfCoverBarProps {
  days: number;
}

export function DaysOfCoverBar({
  days,
}: DaysOfCoverBarProps): React.ReactElement {
  const clampedPct = Math.max(6, Math.min(100, (days / 21) * 100));
  const fillClass =
    days <= 2.0
      ? "bg-status-critical-ink"
      : days < 7.0
        ? "bg-status-warning-ink"
        : "bg-status-healthy-ink";

  return (
    <div className="inline-flex items-center justify-end gap-2.5">
      <span className="font-mono-tabular text-[13px] font-medium text-ink-primary">
        {formatDaysOfCover(days)}
      </span>
      <span
        aria-hidden="true"
        className="h-1.5 w-12 overflow-hidden rounded-full bg-subtle"
      >
        <span
          className={cn("block h-full rounded-full", fillClass)}
          style={{ width: `${clampedPct}%` }}
        />
      </span>
    </div>
  );
}
