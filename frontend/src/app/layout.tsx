import type { Metadata } from "next";
import { Figtree, JetBrains_Mono } from "next/font/google";
import { AppShell } from "@/components/layout/AppShell";
import { BranchProvider } from "@/context/BranchContext";
import { ToastProvider } from "@/context/ToastContext";
import "./globals.css";

const figtree = Figtree({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "RemediSync · Pharmacy Replenishment Workbench",
  description:
    "Predictive demand forecasting, FEFO batch expiry auditing, and automated purchase order replenishment for retail pharmacy chains.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>): React.ReactElement {
  return (
    <html
      lang="en"
      className={`${figtree.variable} ${jetbrainsMono.variable}`}
    >
      <body className="min-h-screen bg-canvas font-sans text-ink-primary antialiased">
        <BranchProvider>
          <ToastProvider>
            <AppShell>{children}</AppShell>
          </ToastProvider>
        </BranchProvider>
      </body>
    </html>
  );
}
