"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/cn";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-control font-medium cursor-pointer select-none transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed",
  {
    variants: {
      variant: {
        primary: "bg-accent text-ink-inverse hover:bg-accent-hover",
        secondary:
          "bg-surface text-ink-primary border border-hairline hover:bg-subtle hover:border-strong",
        danger:
          "bg-status-critical-ink text-ink-inverse hover:opacity-90",
        ghost:
          "bg-transparent text-ink-secondary hover:bg-subtle hover:text-ink-primary",
      },
      size: {
        sm: "h-8 px-3 text-[13px]",
        md: "h-9 px-3.5 text-[13.5px]",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      loading = false,
      disabled,
      children,
      type = "button",
      ...props
    },
    ref
  ) => {
    const isDisabled = Boolean(disabled || loading);
    return (
      <button
        ref={ref}
        type={type}
        disabled={isDisabled}
        aria-busy={loading ? "true" : undefined}
        className={cn(buttonVariants({ variant, size }), className)}
        {...props}
      >
        {loading ? (
          <Loader2
            className="h-4 w-4 shrink-0 animate-spin"
            strokeWidth={1.5}
            aria-hidden="true"
          />
        ) : null}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
