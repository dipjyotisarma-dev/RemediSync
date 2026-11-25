"use client";

import * as React from "react";
import { cn } from "@/lib/cn";

export interface SegmentedOption<T extends string = string> {
  value: T;
  label: string;
  count?: number;
}

export interface SegmentedControlProps<T extends string = string> {
  options: readonly SegmentedOption<T>[];
  value: T;
  onChange: (next: T) => void;
  ariaLabel: string;
  className?: string;
}

export function SegmentedControl<T extends string = string>({
  options,
  value,
  onChange,
  ariaLabel,
  className,
}: SegmentedControlProps<T>): React.ReactElement {
  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      className={cn(
        "inline-flex flex-wrap items-center gap-1 rounded-control border border-hairline bg-subtle p-1",
        className
      )}
    >
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(option.value)}
            className={cn(
              "inline-flex h-7 items-center gap-1.5 rounded-badge px-2.5 text-[13px] cursor-pointer transition-colors duration-150",
              active
                ? "bg-surface font-semibold text-ink-primary border border-hairline"
                : "border border-transparent font-normal text-ink-secondary hover:text-ink-primary"
            )}
          >
            <span>{option.label}</span>
            {typeof option.count === "number" ? (
              <span
                className={cn(
                  "font-mono-tabular text-[12px]",
                  active ? "text-accent" : "text-ink-muted"
                )}
              >
                {option.count}
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
