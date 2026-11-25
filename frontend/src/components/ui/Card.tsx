import * as React from "react";
import { cn } from "@/lib/cn";

export function Card({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>): React.ReactElement {
  return (
    <div
      className={cn(
        "rounded-panel border border-hairline bg-surface",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>): React.ReactElement {
  return (
    <div
      className={cn(
        "flex items-center justify-between gap-4 border-b border-hairline px-5 py-3.5",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardTitle({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>): React.ReactElement {
  return (
    <h2
      className={cn(
        "text-[15px] leading-[22px] font-medium tracking-[-0.01em] text-ink-primary",
        className
      )}
      {...props}
    >
      {children}
    </h2>
  );
}

export function CardContent({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>): React.ReactElement {
  return (
    <div className={cn("p-5", className)} {...props}>
      {children}
    </div>
  );
}
