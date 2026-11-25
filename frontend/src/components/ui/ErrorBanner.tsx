"use client";

import * as React from "react";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { RemediSyncApiError } from "@/services/apiClient";

export interface ErrorBannerProps {
  error: unknown;
  onRetry?: () => void;
}

export function ErrorBanner({
  error,
  onRetry,
}: ErrorBannerProps): React.ReactElement {
  const isApiErr = error instanceof RemediSyncApiError;
  const message = isApiErr
    ? error.message
    : error instanceof Error
      ? error.message
      : "Unable to load operational telemetry.";
  const correlationId = isApiErr ? error.correlationId : undefined;

  return (
    <div
      role="alert"
      className="flex flex-wrap items-center justify-between gap-4 rounded-panel border border-status-critical-border bg-status-critical-bg px-4 py-3"
    >
      <div className="flex items-start gap-3">
        <AlertCircle
          className="mt-0.5 h-4 w-4 shrink-0 text-status-critical-ink"
          strokeWidth={1.5}
          aria-hidden="true"
        />
        <div className="text-[13.5px] leading-5 text-status-critical-ink">
          <p className="font-medium">{message}</p>
          {correlationId && correlationId !== "offline" ? (
            <p className="mt-0.5 text-[12px]">
              Reference:{" "}
              <span className="font-mono-tabular">{correlationId}</span>
            </p>
          ) : null}
        </div>
      </div>
      {onRetry ? (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Retry connection
        </Button>
      ) : null}
    </div>
  );
}
