"use client";

import * as React from "react";

interface BranchContextValue {
  selectedBranchId: string;
  activeStoreBranchId: string;
  setSelectedBranchId: (branchId: string) => void;
  refreshNonce: number;
  triggerRefresh: () => void;
}

const BranchContext = React.createContext<BranchContextValue | null>(null);

export function BranchProvider({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  const [selectedBranchId, setSelectedBranchId] =
    React.useState<string>("BR001");
  const [refreshNonce, setRefreshNonce] = React.useState<number>(0);

  const activeStoreBranchId =
    selectedBranchId === "ALL" ? "BR001" : selectedBranchId;

  const triggerRefresh = React.useCallback(() => {
    setRefreshNonce((prev) => prev + 1);
  }, []);

  const value = React.useMemo<BranchContextValue>(
    () => ({
      selectedBranchId,
      activeStoreBranchId,
      setSelectedBranchId,
      refreshNonce,
      triggerRefresh,
    }),
    [selectedBranchId, activeStoreBranchId, refreshNonce, triggerRefresh]
  );

  return (
    <BranchContext.Provider value={value}>{children}</BranchContext.Provider>
  );
}

export function useBranchContext(): BranchContextValue {
  const ctx = React.useContext(BranchContext);
  if (!ctx) {
    throw new Error("useBranchContext must be used inside BranchProvider");
  }
  return ctx;
}
