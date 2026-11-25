"use client";

import * as React from "react";
import { OverviewKpiGrid } from "@/components/features/overview/OverviewKpiGrid";
import { OverviewWorkspacePanels } from "@/components/features/overview/OverviewWorkspacePanels";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { useBranchContext } from "@/context/BranchContext";
import { getBranchLabel } from "@/lib/constants";
import { apiClient } from "@/services/apiClient";
import type { AnalyticsOverviewResponse } from "@/types/api";

export default function OverviewPage(): React.ReactElement {
  const { selectedBranchId, refreshNonce } = useBranchContext();
  const [data, setData] = React.useState<AnalyticsOverviewResponse | null>(
    null
  );
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<unknown>(null);

  const loadOverview = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.getAnalyticsOverview({
        branchId: selectedBranchId,
        days: 30,
      });
      setData(res);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [selectedBranchId, refreshNonce]);

  React.useEffect(() => {
    void loadOverview();
  }, [loadOverview]);

  return (
    <div className="space-y-6">
      <div>
        <p className="text-[13.5px] text-ink-secondary">
          30-day revenue performance, shelf stockout telemetry, and near-expiry
          exposure for{" "}
          <span className="font-medium text-ink-primary">
            {getBranchLabel(selectedBranchId)}
          </span>
          .
        </p>
      </div>

      {error ? <ErrorBanner error={error} onRetry={loadOverview} /> : null}

      <OverviewKpiGrid data={data} isLoading={loading} />

      <OverviewWorkspacePanels overview={data} isLoading={loading} />
    </div>
  );
}
