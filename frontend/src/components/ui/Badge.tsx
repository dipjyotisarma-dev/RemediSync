import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-badge border px-2 py-0.5 text-[12px] leading-4 font-medium whitespace-nowrap",
  {
    variants: {
      tone: {
        critical:
          "bg-status-critical-bg text-status-critical-ink border-status-critical-border",
        warning:
          "bg-status-warning-bg text-status-warning-ink border-status-warning-border",
        healthy:
          "bg-status-healthy-bg text-status-healthy-ink border-status-healthy-border",
        neutral: "bg-subtle text-ink-secondary border-hairline",
        accent: "bg-accent-subtle text-accent border-accent-border",
      },
    },
    defaultVariants: {
      tone: "neutral",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  mono?: boolean;
}

export function Badge({
  className,
  tone,
  mono = false,
  children,
  ...props
}: BadgeProps): React.ReactElement {
  return (
    <span
      className={cn(
        badgeVariants({ tone }),
        mono && "font-mono-tabular",
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
