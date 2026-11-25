"use client";

import * as React from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/cn";

export interface SlideOverProps {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
}

export function SlideOver({
  open,
  onClose,
  title,
  subtitle,
  children,
  className,
}: SlideOverProps): React.ReactElement | null {
  const titleId = React.useId();

  React.useEffect(() => {
    if (!open) {
      return;
    }
    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div
        aria-hidden="true"
        onClick={onClose}
        className="fixed inset-0 transition-opacity duration-150"
        style={{ backgroundColor: "var(--backdrop-scrim)" }}
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className={cn(
          "relative z-10 flex h-full w-full max-w-[480px] flex-col bg-surface shadow-overlay",
          className
        )}
      >
        <div className="flex items-start justify-between gap-4 border-b border-hairline px-6 py-4">
          <div className="min-w-0">
            <h2
              id={titleId}
              className="truncate text-[16px] leading-6 font-medium text-ink-primary"
            >
              {title}
            </h2>
            {subtitle ? (
              <p className="mt-0.5 truncate text-[13px] text-ink-secondary">
                {subtitle}
              </p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close panel"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-control text-ink-secondary cursor-pointer transition-colors duration-150 hover:bg-subtle hover:text-ink-primary"
          >
            <X className="h-4 w-4" strokeWidth={1.5} aria-hidden="true" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-6">{children}</div>
      </aside>
    </div>
  );
}
