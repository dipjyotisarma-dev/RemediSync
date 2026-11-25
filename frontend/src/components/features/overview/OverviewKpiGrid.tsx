"use client";

import * as React from "react";
import { Card } from "@/components/ui/Card";
import { CountUpValue } from "@/components/ui/CountUpValue";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  formatINR,
  formatPercent,
  formatPerformanceDelta,
} from "@/lib/format";
import type { AnalyticsOverviewResponse } from "@/types/api";
import { cn } from "@/lib/cn";

export interface OverviewKpiGridProps {
  data: AnalyticsOverviewResponse | null;
  isLoading: boolean;
}

export function OverviewKpiGrid({
  data,
  isLoading,
}: OverviewKpiGridProps): React.ReactElement {
  if (isLoading || !data) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, idx) => (
          <Card key={idx} className="p-5">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="mt-3 h-8 w-40" />
            <Skeleton className="mt-2.5 h-4 w-28" />
          </Card>
        ))}
      </div>
    );
  }

  const perfAboveTarget = data.performance_ratio >= 1;
  const lowStockout = data.network_stockout_rate <= 0.025;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Card className="p-5">
        <p className="text-[12.5px] font-medium text-ink-secondary">
          Daily gross revenue
        </p>
        <p className="mt-2 font-mono-tabular text-[26px] leading-8 font-semibold tracking-[-0.02em] text-ink-primary">
          <CountUpValue
            value={data.network_daily_revenue_inr}
            formatter={(v) => formatINR(v, 0)}
          />
        </p>
        <p
          className={cn(
            "mt-1.5 text-[12.5px] font-medium",
            perfAboveTarget
              ? "text-status-healthy-ink"
              : "text-status-warning-ink"
          )}
        >
          {formatPerformanceDelta(data.performance_ratio)} (
          <span className="font-mono-tabular">
            {formatINR(data.target_daily_revenue_inr, 0)}
          </span>
          )
        </p>
      </Card>

      <Card className="p-5">
        <p className="text-[12.5px] font-medium text-ink-secondary">
          Network stockout rate
        </p>
        <p className="mt-2 font-mono-tabular text-[26px] leading-8 font-semibold tracking-[-0.02em] text-ink-primary">
          <CountUpValue
            value={data.network_stockout_rate}
            formatter={(v) => formatPercent(v, 1)}
          />
        </p>
        <p
          className={cn(
            "mt-1.5 text-[12.5px]",
            lowStockout ? "text-status-healthy-ink" : "text-status-critical-ink"
          )}
        >
          Across 30-day dispensing window
        </p>
      </Card>

      <Card className="p-5">
        <p className="text-[12.5px] font-medium text-ink-secondary">
          Critical stockouts
        </p>
        <p className="mt-2 font-mono-tabular text-[26px] leading-8 font-semibold tracking-[-0.02em] text-ink-primary">
          {data.critical_stockouts_count}{" "}
          <span className="font-sans text-[15px] font-normal text-ink-secondary">
            SKUs
          </span>
        </p>
        <p className="mt-1.5 text-[12.5px] text-ink-muted">
          <span className="font-mono-tabular">
            {data.active_branches_count}
          </span>{" "}
          {data.active_branches_count === 1 ? "branch" : "branches"} ·{" "}
          <span className="font-mono-tabular">{data.total_skus_tracked}</span>{" "}
          catalog SKUs
        </p>
      </Card>

      <Card className="p-5">
        <p className="text-[12.5px] font-medium text-ink-secondary">
          Near-expiry exposure
        </p>
        <p className="mt-2 font-mono-tabular text-[26px] leading-8 font-semibold tracking-[-0.02em] text-ink-primary">
          <CountUpValue
            value={data.estimated_near_expiry_value_inr}
            formatter={(v) => formatINR(v, 0)}
          />
        </p>
        <p className="mt-1.5 text-[12.5px] text-status-warning-ink">
          <span className="font-mono-tabular">
            {data.near_expiry_batches_count}
          </span>{" "}
          lots within 90-day return cutoff
        </p>
      </Card>
    </div>
  );
}
