import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? "Agent-to-Agent Compute Marketplace";

export const metadata: Metadata = {
  title: APP_NAME,
  description:
    "A trustless marketplace where autonomous agents trade compute and settle in USDC on the Arc network.",
};

const NAV = [
  { href: "/", label: "Overview" },
  { href: "/compute", label: "Run compute" },
  { href: "/batch", label: "Batch" },
  { href: "/providers", label: "Providers" },
  { href: "/leaderboard", label: "Leaderboard" },
  { href: "/status", label: "Status" },
  { href: "/funding", label: "Funding" },
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col">
        <header className="border-b border-border/80 bg-panel/60 backdrop-blur">
          <div className="mx-auto max-w-5xl flex items-center justify-between px-6 py-4">
            <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-accent" />
              <span>{APP_NAME}</span>
            </Link>
            <nav className="flex items-center gap-1 text-sm">
              {NAV.map((n) => (
                <Link
                  key={n.href}
                  href={n.href}
                  className="rounded-md px-3 py-1.5 text-muted hover:bg-border/50 hover:text-white transition"
                >
                  {n.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="flex-1 mx-auto max-w-5xl w-full px-6 py-10">{children}</main>
        <footer className="border-t border-border/80 text-xs text-muted">
          <div className="mx-auto max-w-5xl px-6 py-4 flex justify-between">
            <span>Settlement on Arc testnet. USDC denominated.</span>
            <span>v0.1</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
