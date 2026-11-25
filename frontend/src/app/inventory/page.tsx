"use client";

import * as React from "react";
import { InventoryTable } from "@/components/features/inventory/InventoryTable";
import {
  InventoryToolbar,
  type AbcFilterValue,
} from "@/components/features/inventory/InventoryToolbar";
import { SkuSalesDrawer } from "@/components/features/inventory/SkuSalesDrawer";
import { Button } from "@/components/ui/Button";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { useBranchContext } from "@/context/BranchContext";
import { getBranchLabel } from "@/lib/constants";
import { apiClient } from "@/services/apiClient";
import type { InventoryItem } from "@/types/api";

const PAGE_LIMIT = 50;

export default function InventoryPage(): React.ReactElement {
  const { activeStoreBranchId, refreshNonce } = useBranchContext();
  const [items, setItems] = React.useState<InventoryItem[]>([]);
  const [totalRecords, setTotalRecords] = React.useState<number>(0);
  const [branchName, setBranchName] = React.useState<string>("");
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<unknown>(null);

  const [searchQuery, setSearchQuery] = React.useState<string>("");
  const [category, setCategory] = React.useState<string>("");
  const [abcClass, setAbcClass] = React.useState<AbcFilterValue>("ALL");
  const [offset, setOffset] = React.useState<number>(0);
  const [selectedSku, setSelectedSku] = React.useState<InventoryItem | null>(
    null
  );

  React.useEffect(() => {
    setOffset(0);
  }, [activeStoreBranchId, category, abcClass]);

  const loadInventory = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.getBranchInventory({
        branchId: activeStoreBranchId,
        category: category || undefined,
        abcClass: abcClass === "ALL" ? undefined : abcClass,
        limit: PAGE_LIMIT,
        offset,
      });
      setItems(res.items);
      setTotalRecords(res.total_records);
      setBranchName(res.branch_name);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [activeStoreBranchId, category, abcClass, offset, refreshNonce]);

  React.useEffect(() => {
    void loadInventory();
  }, [loadInventory]);

  const filteredItems = React.useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) {
      return items;
    }
    return items.filter(
      (item) =>
        item.brand_name.toLowerCase().includes(q) ||
        item.generic_salt.toLowerCase().includes(q) ||
        item.medicine_id.toLowerCase().includes(q)
    );
  }, [items, searchQuery]);

  const handleClearFilters = (): void => {
    setSearchQuery("");
    setCategory("");
    setAbcClass("ALL");
    setOffset(0);
  };

  const canPrev = offset > 0;
  const canNext = offset + PAGE_LIMIT < totalRecords;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-[13.5px] text-ink-secondary">
          Live shelf positions, statistical reorder points, and days of cover at{" "}
          <span className="font-medium text-ink-primary">
            {branchName || getBranchLabel(activeStoreBranchId)}
          </span>
          . Select any medicine row to inspect 30-day dispensing history.
        </p>
        <p className="font-mono-tabular text-[12.5px] text-ink-muted">
          {totalRecords} catalog SKUs
        </p>
      </div>

      {error ? <ErrorBanner error={error} onRetry={loadInventory} /> : null}

      <InventoryToolbar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        category={category}
        onCategoryChange={setCategory}
        abcClass={abcClass}
        onAbcClassChange={setAbcClass}
      />

      <InventoryTable
        items={filteredItems}
        isLoading={loading}
        onSelectItem={setSelectedSku}
        onClearFilters={handleClearFilters}
      />

      {totalRecords > PAGE_LIMIT ? (
        <div className="flex items-center justify-between pt-1">
          <p className="font-mono-tabular text-[12.5px] text-ink-secondary">
            Showing {offset + 1}–{Math.min(offset + PAGE_LIMIT, totalRecords)}{" "}
            of {totalRecords}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={!canPrev || loading}
              onClick={() => setOffset((prev) => Math.max(0, prev - PAGE_LIMIT))}
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={!canNext || loading}
              onClick={() => setOffset((prev) => prev + PAGE_LIMIT)}
            >
              Next
            </Button>
          </div>
        </div>
      ) : null}

      <SkuSalesDrawer
        branchId={activeStoreBranchId}
        item={selectedSku}
        onClose={() => setSelectedSku(null)}
      />
    </div>
  );
}
