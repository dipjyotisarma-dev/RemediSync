import * as React from "react";
import { cn } from "@/lib/cn";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export function Skeleton({
  className,
  ...props
}: SkeletonProps): React.ReactElement {
  return (
    <div
      aria-hidden="true"
      className={cn("animate-pulse rounded-badge bg-subtle", className)}
      {...props}
    />
  );
}
