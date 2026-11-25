"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  CalendarClock,
  ClipboardCheck,
  LayoutGrid,
  Package,
} from "lucide-react";
import { SystemHealthBadge } from "@/components/layout/SystemHealthBadge";
import { cn } from "@/lib/cn";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
}

const NAV_ITEMS: readonly NavItem[] = [
  { href: "/overview", label: "Overview", icon: LayoutGrid },
  { href: "/inventory", label: "Shelf inventory", icon: Package },
  { href: "/replenishment", label: "Replenishment", icon: ClipboardCheck },
  { href: "/expiry", label: "Expiry audit", icon: CalendarClock },
];

export interface SidebarProps {
  onNavigate?: () => void;
}

export function Sidebar({ onNavigate }: SidebarProps): React.ReactElement {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-[240px] flex-col border-r border-hairline bg-subtle">
      <div className="flex h-[56px] items-center gap-2.5 border-b border-hairline px-4">
        <svg
          width="22"
          height="22"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
          className="shrink-0 text-accent"
        >
          <rect
            x="2.5"
            y="2.5"
            width="19"
            height="19"
            rx="5"
            stroke="currentColor"
            strokeWidth="1.75"
          />
          <path
            d="M12 7.5V16.5M7.5 12H16.5"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
          />
        </svg>
        <div className="min-w-0">
          <span className="block truncate text-[15px] font-semibold tracking-[-0.015em] text-ink-primary">
            RemediSync
          </span>
        </div>
      </div>

      <nav
        aria-label="Primary navigation"
        className="flex flex-1 flex-col gap-1 px-3 py-4"
      >
        <p className="mb-1 px-2.5 text-[12px] font-medium text-ink-muted">
          Dispensary operations
        </p>
        {NAV_ITEMS.map((item) => {
          const active =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex h-[34px] items-center gap-2.5 rounded-control px-2.5 text-[13.5px] transition-colors duration-150",
                active
                  ? "border border-hairline bg-surface font-medium text-ink-primary"
                  : "border border-transparent text-ink-secondary hover:bg-surface/60 hover:text-ink-primary"
              )}
            >
              <span className="flex w-5 shrink-0 items-center justify-center">
                <Icon
                  className={cn(
                    "h-4 w-4",
                    active ? "text-accent" : "text-ink-muted"
                  )}
                  strokeWidth={1.5}
                />
              </span>
              <span className="truncate">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-hairline p-3">
        <SystemHealthBadge />
      </div>
    </div>
  );
}
