"use client";

import * as React from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/Input";
import {
  SegmentedControl,
  type SegmentedOption,
} from "@/components/ui/SegmentedControl";
import { Select, type SelectOption } from "@/components/ui/Select";
import { THERAPEUTIC_CATEGORIES } from "@/lib/constants";

export type AbcFilterValue = "ALL" | "A" | "B" | "C";

export interface InventoryToolbarProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  category: string;
  onCategoryChange: (cat: string) => void;
  abcClass: AbcFilterValue;
  onAbcClassChange: (abc: AbcFilterValue) => void;
}

const ABC_OPTIONS: readonly SegmentedOption<AbcFilterValue>[] = [
  { value: "ALL", label: "All tiers" },
  { value: "A", label: "Class A" },
  { value: "B", label: "Class B" },
  { value: "C", label: "Class C" },
];

export function InventoryToolbar({
  searchQuery,
  onSearchChange,
  category,
  onCategoryChange,
  abcClass,
  onAbcClassChange,
}: InventoryToolbarProps): React.ReactElement {
  const categoryOptions = React.useMemo<SelectOption[]>(
    () => [
      { value: "", label: "All therapeutic categories" },
      ...THERAPEUTIC_CATEGORIES.map((c) => ({ value: c, label: c })),
    ],
    []
  );

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
      <div className="flex flex-1 flex-wrap items-center gap-3">
        <div className="w-full sm:w-72">
          <Input
            aria-label="Search medicine brand or generic salt"
            placeholder="Search brand or generic salt"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            prefixIcon={<Search className="h-4 w-4" strokeWidth={1.5} />}
          />
        </div>
        <div className="w-full sm:w-56">
          <Select
            aria-label="Filter by therapeutic category"
            options={categoryOptions}
            value={category}
            onChange={onCategoryChange}
          />
        </div>
      </div>

      <SegmentedControl
        ariaLabel="Filter by Pareto ABC class"
        options={ABC_OPTIONS}
        value={abcClass}
        onChange={onAbcClassChange}
      />
    </div>
  );
}
