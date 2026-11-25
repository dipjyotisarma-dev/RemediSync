import * as React from "react";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatINR } from "@/lib/format";
import type { BatchExpiryItem } from "@/types/api";

export interface ExpirySummaryStripProps {
  batches: readonly BatchExpiryItem[];
  totalExposureInr: number;
  horizonDays: number;
  isLoading: boolean;
}

export function ExpirySummaryStrip({
  batches,
  totalExposureInr,
  horizonDays,
  isLoading,
}: ExpirySummaryStripProps): React.ReactElement {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {Array.from({ length: 3 }).map((_, idx) => (
          <Card key={idx} className="p-5">
            <Skeleton className="h-4 w-36" />
            <Skeleton className="mt-3 h-8 w-32" />
            <Skeleton className="mt-2 h-4 w-28" />
          </Card>
        ))}
      </div>
    );
  }

  const totalUnsoldUnits = batches.reduce(
    (sum, b) => sum + b.projected_unsold_units,
    0
  );

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <Card className="p-5">
        <p className="text-[12.5px] font-medium text-ink-secondary">
          Lots within horizon
        </p>
        <p className="mt-2 font-mono-tabular text-[26px] leading-8 font-semibold tracking-[-0.02em] text-ink-primary">
          {batches.length}{" "}
          <span className="font-sans text-[15px] font-normal text-ink-secondary">
            batches
          </span>
        </p>
        <p className="mt-1.5 text-[12.5px] text-ink-muted">
          Expiring within{" "}
          <span className="font-mono-tabular">{horizonDays}</span> days
        </p>
      </Card>

      <Card className="p-5">
        <p className="text-[12.5px] font-medium text-ink-secondary">
          Projected unsold volume
        </p>
        <p className="mt-2 font-mono-tabular text-[26px] leading-8 font-semibold tracking-[-0.02em] text-ink-primary">
          {totalUnsoldUnits.toFixed(0)}{" "}
          <span className="font-sans text-[15px] font-normal text-ink-secondary">
            units
          </span>
        </p>
        <p className="mt-1.5 text-[12.5px] text-ink-muted">
          Net of forward dispensing velocity
        </p>
      </Card>

      <Card className="p-5">
        <p className="text-[12.5px] font-medium text-ink-secondary">
          Write-off exposure
        </p>
        <p className="mt-2 font-mono-tabular text-[26px] leading-8 font-semibold tracking-[-0.02em] text-ink-primary">
          {formatINR(totalExposureInr, 2)}
        </p>
        <p className="mt-1.5 text-[12.5px] text-status-warning-ink">
          Eligible for distributor credit return (&le; 90d)
        </p>
      </Card>
    </div>
  );
}
