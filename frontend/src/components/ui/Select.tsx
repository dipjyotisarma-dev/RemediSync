"use client";

import * as React from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/cn";

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps
  extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "onChange"> {
  label?: string;
  options: readonly SelectOption[];
  value: string;
  onChange: (value: string) => void;
}

export function Select({
  label,
  options,
  value,
  onChange,
  id,
  className,
  ...props
}: SelectProps): React.ReactElement {
  const generatedId = React.useId();
  const selectId = id ?? generatedId;

  return (
    <div className="flex flex-col gap-1">
      {label ? (
        <label
          htmlFor={selectId}
          className="text-[12px] leading-4 font-medium text-ink-secondary"
        >
          {label}
        </label>
      ) : null}
      <div className="relative inline-flex items-center">
        <select
          id={selectId}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={cn(
            "h-9 w-full appearance-none rounded-control border border-hairline bg-surface py-1.5 pl-3 pr-8 text-[13.5px] text-ink-primary cursor-pointer transition-colors duration-150 hover:border-strong",
            className
          )}
          {...props}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown
          className="pointer-events-none absolute right-2.5 h-4 w-4 text-ink-muted"
          strokeWidth={1.5}
          aria-hidden="true"
        />
      </div>
    </div>
  );
}
