"use client";

import * as React from "react";
import { cn } from "@/lib/cn";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  prefixIcon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, prefixIcon, id, ...props }, ref) => {
    const generatedId = React.useId();
    const inputId = id ?? generatedId;
    const errorId = `${inputId}-error`;

    return (
      <div className="flex flex-col gap-1">
        {label ? (
          <label
            htmlFor={inputId}
            className="text-[12px] leading-4 font-medium text-ink-secondary"
          >
            {label}
          </label>
        ) : null}
        <div className="relative flex items-center">
          {prefixIcon ? (
            <span
              className="pointer-events-none absolute left-3 flex items-center text-ink-muted"
              aria-hidden="true"
            >
              {prefixIcon}
            </span>
          ) : null}
          <input
            ref={ref}
            id={inputId}
            aria-invalid={error ? "true" : undefined}
            aria-describedby={error ? errorId : undefined}
            className={cn(
              "h-9 w-full rounded-control border bg-surface px-3 text-[13.5px] text-ink-primary placeholder:text-ink-muted transition-colors duration-150",
              prefixIcon ? "pl-9" : "",
              error
                ? "border-status-critical-ink"
                : "border-hairline hover:border-strong",
              className
            )}
            {...props}
          />
        </div>
        {error ? (
          <p
            id={errorId}
            role="alert"
            className="text-[12px] leading-4 text-status-critical-ink"
          >
            {error}
          </p>
        ) : null}
      </div>
    );
  }
);

Input.displayName = "Input";
