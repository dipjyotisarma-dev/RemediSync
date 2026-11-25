"use client";

import * as React from "react";
import { BatchExpiryTable } from "@/components/features/expiry/BatchExpiryTable";
import { ExpirySummaryStrip } from "@/components/features/expiry/ExpirySummaryStrip";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import {
  SegmentedControl,
  type SegmentedOption,
} from "@/components/ui/SegmentedControl";
import { useBranchContext } from "@/context/BranchContext";
import { getBranchLabel } from "@/lib/constants";
import { apiClient } from "@/services/apiClient";
import type { BatchExpiryItem } from "@/types/api";

type HorizonValue = "30" | "60" | "90" | "180";

const HORIZON_OPTIONS: readonly SegmentedOption<HorizonValue>[] = [
  { value: "30", label: "30 days" },
  { value: "60", label: "60 days" },
  { value: "90", label: "90 days (statutory)" },
  { value: "180", label: "180 days" },
];

export default function ExpiryAuditPage(): React.ReactElement {
  const { selectedBranchId, refreshNonce } = useBranchContext();
  const [horizon, setHorizon] = React.useState<HorizonValue>("90");
  const [batches, setBatches] = React.useState<BatchExpiryItem[]>([]);
  const [totalExposureInr, setTotalExposureInr] = React.useState<number>(0);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<unknown>(null);

  const loadBatches = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.getExpiringBatches({
        branchId: selectedBranchId,
        maxDaysToExpiry: Number(horizon),
      });
      setBatches(res.batches);
      setTotalExposureInr(res.total_write_off_exposure_inr);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [selectedBranchId, horizon, refreshNonce]);

  React.useEffect(() => {
    void loadBatches();
  }, [loadBatches]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
        <p className="text-[13.5px] text-ink-secondary">
          FEFO lot-level expiration audit and distributor return eligibility for{" "}
          <span className="font-medium text-ink-primary">
            {getBranchLabel(selectedBranchId)}
          </span>
          .
        </p>

        <SegmentedControl
          ariaLabel="Select expiry horizon in days"
          options={HORIZON_OPTIONS}
          value={horizon}
          onChange={setHorizon}
        />
      </div>

      {error ? <ErrorBanner error={error} onRetry={loadBatches} /> : null}

      <ExpirySummaryStrip
        batches={batches}
        totalExposureInr={totalExposureInr}
        horizonDays={Number(horizon)}
        isLoading={loading}
      />

      <BatchExpiryTable batches={batches} isLoading={loading} />
    </div>
  );
}
