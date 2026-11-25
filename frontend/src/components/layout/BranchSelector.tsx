"use client";

import * as React from "react";
import { usePathname } from "next/navigation";
import { Select, type SelectOption } from "@/components/ui/Select";
import { useBranchContext } from "@/context/BranchContext";
import { ASSAM_BRANCHES } from "@/lib/constants";

export function BranchSelector(): React.ReactElement {
  const pathname = usePathname();
  const { selectedBranchId, activeStoreBranchId, setSelectedBranchId } =
    useBranchContext();

  const supportsNetworkScope =
    pathname === "/overview" || pathname === "/expiry";

  const options = React.useMemo<SelectOption[]>(() => {
    const branchOpts = ASSAM_BRANCHES.map((b) => ({
      value: b.id,
      label: `${b.name} (${b.id})`,
    }));
    if (supportsNetworkScope) {
      return [
        { value: "ALL", label: "All branches (Assam network)" },
        ...branchOpts,
      ];
    }
    return branchOpts;
  }, [supportsNetworkScope]);

  const currentValue = supportsNetworkScope
    ? selectedBranchId
    : activeStoreBranchId;

  return (
    <Select
      aria-label="Select pharmacy branch"
      options={options}
      value={currentValue}
      onChange={setSelectedBranchId}
      className="min-w-[236px]"
    />
  );
}
