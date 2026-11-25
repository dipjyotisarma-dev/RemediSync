"use client";

import * as React from "react";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { cn } from "@/lib/cn";

export interface DataColumn<T> {
  key: string;
  header: string;
  align?: "left" | "right";
  mono?: boolean;
  headerClassName?: string;
  cellClassName?: string;
  render: (row: T) => React.ReactNode;
}

export interface DataTableProps<T> {
  columns: readonly DataColumn<T>[];
  data: readonly T[];
  rowKey: (row: T) => string;
  isLoading?: boolean;
  skeletonRowCount?: number;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyAction?: React.ReactNode;
  onRowClick?: (row: T) => void;
  className?: string;
}

export function DataTable<T>({
  columns,
  data,
  rowKey,
  isLoading = false,
  skeletonRowCount = 6,
  emptyTitle = "No records found",
  emptyDescription = "Adjust your filters or select a different pharmacy branch.",
  emptyAction,
  onRowClick,
  className,
}: DataTableProps<T>): React.ReactElement {
  return (
    <div
      className={cn(
        "overflow-x-auto rounded-panel border border-hairline bg-surface",
        className
      )}
    >
      <table className="w-full border-collapse text-left">
        <thead>
          <tr className="border-b border-hairline bg-subtle">
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={cn(
                  "h-9 px-4 text-[12px] leading-4 font-medium text-ink-muted whitespace-nowrap",
                  col.align === "right" ? "text-right" : "text-left",
                  col.headerClassName
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-hairline">
          {isLoading ? (
            Array.from({ length: skeletonRowCount }).map((_, idx) => (
              <tr
                key={`skeleton-${idx}`}
                data-testid="skeleton-row"
                className="h-[42px]"
              >
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-2">
                    <Skeleton
                      className={cn(
                        "h-4 w-24",
                        col.align === "right" && "ml-auto"
                      )}
                    />
                  </td>
                ))}
              </tr>
            ))
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length}>
                <EmptyState
                  title={emptyTitle}
                  description={emptyDescription}
                  action={emptyAction}
                />
              </td>
            </tr>
          ) : (
            data.map((row) => {
              const interactive = Boolean(onRowClick);
              return (
                <tr
                  key={rowKey(row)}
                  tabIndex={interactive ? 0 : undefined}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  onKeyDown={
                    onRowClick
                      ? (e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            onRowClick(row);
                          }
                        }
                      : undefined
                  }
                  className={cn(
                    "min-h-[42px] transition-colors duration-150",
                    interactive
                      ? "cursor-pointer hover:bg-subtle focus-visible:bg-subtle"
                      : "hover:bg-canvas"
                  )}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn(
                        "px-4 py-2.5 text-[13.5px] leading-5 text-ink-primary align-middle",
                        col.align === "right" ? "text-right" : "text-left",
                        col.mono && "font-mono-tabular",
                        col.cellClassName
                      )}
                    >
                      {col.render(row)}
                    </td>
                  ))}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
