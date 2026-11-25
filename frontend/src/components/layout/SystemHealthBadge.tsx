"use client";

import * as React from "react";
import { useBranchContext } from "@/context/BranchContext";
import { apiClient } from "@/services/apiClient";
import type { HealthResponse } from "@/types/api";
import { cn } from "@/lib/cn";

export function SystemHealthBadge(): React.ReactElement {
  const { refreshNonce } = useBranchContext();
  const [health, setHealth] = React.useState<HealthResponse | null>(null);
  const [offline, setOffline] = React.useState<boolean>(false);

  React.useEffect(() => {
    let active = true;
    apiClient
      .getHealth()
      .then((res) => {
        if (active) {
          setHealth(res);
          setOffline(false);
        }
      })
      .catch(() => {
        if (active) {
          setOffline(true);
        }
      });
    return () => {
      active = false;
    };
  }, [refreshNonce]);

  const isHealthy =
    !offline && health?.status === "HEALTHY" && health.database === "CONNECTED";

  return (
    <div className="rounded-control border border-hairline bg-surface px-3 py-2.5">
      <div className="flex items-center gap-2">
        <span
          aria-hidden="true"
          className={cn(
            "h-2 w-2 shrink-0 rounded-full",
            offline
              ? "bg-status-critical-ink"
              : isHealthy
                ? "bg-status-healthy-ink"
                : "bg-status-warning-ink"
          )}
        />
        <span className="text-[12.5px] font-medium text-ink-primary">
          {offline
            ? "API unreachable"
            : isHealthy
              ? "API connected"
              : "Service degraded"}
        </span>
      </div>
      <p className="mt-1 truncate font-mono-tabular text-[12px] text-ink-muted">
        {health
          ? `${health.active_model.name.replace("Forecaster", "")} ${health.active_model.version}`
          : "FastAPI · localhost:8000"}
      </p>
    </div>
  );
}
