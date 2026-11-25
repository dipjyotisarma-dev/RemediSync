"use client";

import * as React from "react";
import { usePathname } from "next/navigation";
import { Menu, RefreshCw, X } from "lucide-react";
import { BranchSelector } from "@/components/layout/BranchSelector";
import { Sidebar } from "@/components/layout/Sidebar";
import { Button } from "@/components/ui/Button";
import { useBranchContext } from "@/context/BranchContext";
import { useToast } from "@/context/ToastContext";

const ROUTE_TITLES: Record<string, string> = {
  "/overview": "Network overview",
  "/inventory": "Shelf inventory",
  "/replenishment": "Replenishment workbench",
  "/expiry": "Batch expiry audit",
};

export function AppShell({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  const pathname = usePathname();
  const { triggerRefresh } = useBranchContext();
  const { pushToast } = useToast();
  const [mobileNavOpen, setMobileNavOpen] = React.useState<boolean>(false);

  const pageTitle = ROUTE_TITLES[pathname] ?? "RemediSync";

  const handleRefresh = (): void => {
    triggerRefresh();
    pushToast({
      title: "Data updated",
      description: "Reloaded latest branch telemetry from FastAPI.",
      tone: "neutral",
    });
  };

  return (
    <div className="flex min-h-screen bg-canvas">
      {/* Desktop Fixed Rail */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:z-30 lg:block">
        <Sidebar />
      </div>

      {/* Mobile Navigation Drawer */}
      {mobileNavOpen ? (
        <div className="fixed inset-0 z-50 flex lg:hidden">
          <div
            aria-hidden="true"
            onClick={() => setMobileNavOpen(false)}
            className="fixed inset-0"
            style={{ backgroundColor: "var(--backdrop-scrim)" }}
          />
          <div className="relative z-10 flex h-full">
            <Sidebar onNavigate={() => setMobileNavOpen(false)} />
            <button
              type="button"
              onClick={() => setMobileNavOpen(false)}
              aria-label="Close navigation menu"
              className="ml-2 mt-3 flex h-9 w-9 items-center justify-center rounded-control bg-surface text-ink-primary shadow-overlay"
            >
              <X className="h-4 w-4" strokeWidth={1.5} aria-hidden="true" />
            </button>
          </div>
        </div>
      ) : null}

      {/* Main Column */}
      <div className="flex min-w-0 flex-1 flex-col lg:pl-[240px]">
        <header className="sticky top-0 z-20 flex h-[56px] items-center justify-between gap-4 border-b border-hairline bg-surface px-4 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileNavOpen(true)}
              aria-label="Open navigation menu"
              className="flex h-9 w-9 items-center justify-center rounded-control border border-hairline text-ink-secondary cursor-pointer hover:bg-subtle lg:hidden"
            >
              <Menu className="h-4 w-4" strokeWidth={1.5} aria-hidden="true" />
            </button>
            <h1 className="truncate text-[20px] leading-7 font-medium tracking-[-0.015em] text-ink-primary">
              {pageTitle}
            </h1>
          </div>

          <div className="flex items-center gap-2.5">
            <BranchSelector />
            <Button
              variant="secondary"
              size="md"
              onClick={handleRefresh}
              aria-label="Refresh data"
            >
              <RefreshCw
                className="h-4 w-4 text-ink-secondary"
                strokeWidth={1.5}
                aria-hidden="true"
              />
              <span className="hidden sm:inline">Refresh data</span>
            </Button>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1440px] flex-1 px-4 py-6 sm:px-6">
          {children}
        </main>
      </div>
    </div>
  );
}
