"use client";

import { useCallback, useEffect, useState } from "react";
import { shorten } from "@/lib/explorer";

interface HealthBody {
  status: string;
  timestamp: string;
  version: string;
  arc_connected: boolean;
  contract_deployed: boolean;
  settlement_simulate: boolean;
}

interface MetricsBody {
  metering: { record_count?: number; total_units?: number };
  settlement: {
    transaction_count?: number;
    total_settled?: number;
    avg_amount?: number;
    mode?: string;
  };
  uptime_seconds: number;
}

interface MetaBody {
  api_version?: string;
  arc_chain_id?: number;
  arc_contract_address?: string;
  arc_explorer_url?: string;
  usdc_address?: string;
}

export default function StatusPage() {
  const [health, setHealth] = useState<HealthBody | null>(null);
  const [metrics, setMetrics] = useState<MetricsBody | null>(null);
  const [meta, setMeta] = useState<MetaBody | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [hRes, mRes, metaRes] = await Promise.all([
        fetch("/api/backend-health"),
        fetch("/api/backend-metrics"),
        fetch("/api/public-meta"),
      ]);
      if (hRes.ok) setHealth(await hRes.json());
      if (mRes.ok) setMetrics(await mRes.json());
      if (metaRes.ok) setMeta(await metaRes.json());
      if (!hRes.ok && !mRes.ok) {
        setError("Backend is unreachable. Check that FastAPI is running.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const settlementMode = health
    ? health.settlement_simulate
      ? "Simulated (no on-chain transactions)"
      : "Live (Arc testnet)"
    : "Unknown";

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Marketplace status</h1>
          <p className="text-muted text-sm">Live readout from the FastAPI backend.</p>
        </div>
        <button
          onClick={refresh}
          disabled={loading}
          className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-panel disabled:opacity-60"
        >
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </header>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
          {error}
        </div>
      )}

      <section className="grid gap-4 md:grid-cols-3">
        <Card label="Settlement mode" value={settlementMode} tone={health?.settlement_simulate ? "warn" : "ok"} />
        <Card label="Arc RPC" value={health?.arc_connected ? "Connected" : "Disconnected"} tone={health?.arc_connected ? "ok" : "warn"} />
        <Card label="Contract" value={health?.contract_deployed ? "Deployed" : "Missing"} tone={health?.contract_deployed ? "ok" : "warn"} />
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Panel title="Throughput">
          <Row label="Total settlements" value={metrics?.settlement?.transaction_count ?? "—"} />
          <Row label="Total settled (USDC)" value={metrics?.settlement?.total_settled?.toFixed(6) ?? "—"} />
          <Row label="Average tx amount" value={metrics?.settlement?.avg_amount?.toFixed(6) ?? "—"} />
          <Row label="Metering records" value={metrics?.metering?.record_count ?? "—"} />
          <Row label="Uptime (s)" value={metrics?.uptime_seconds?.toFixed(0) ?? "—"} />
        </Panel>

        <Panel title="Network">
          <Row label="Chain ID" value={meta?.arc_chain_id ?? "—"} />
          <Row label="Contract" value={shorten(meta?.arc_contract_address) || "—"} mono />
          <Row label="USDC" value={shorten(meta?.usdc_address) || "—"} mono />
          <Row label="Explorer" value={meta?.arc_explorer_url || "—"} />
          <Row label="API version" value={health?.version ?? meta?.api_version ?? "—"} />
        </Panel>
      </section>
    </div>
  );
}

function Card({ label, value, tone }: { label: string; value: string; tone?: "ok" | "warn" }) {
  const ring =
    tone === "ok"
      ? "border-accent/40 bg-accent/5"
      : tone === "warn"
        ? "border-yellow-500/40 bg-yellow-500/5"
        : "border-border bg-panel/60";
  return (
    <div className={`rounded-lg border ${ring} p-5`}>
      <div className="text-xs uppercase tracking-widest text-muted">{label}</div>
      <div className="mt-2 text-lg font-semibold">{value}</div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-panel/60 p-5">
      <div className="text-sm font-semibold mb-3">{title}</div>
      <dl className="space-y-2 text-sm">{children}</dl>
    </div>
  );
}

function Row({
  label,
  value,
  mono,
}: {
  label: string;
  value: string | number | undefined;
  mono?: boolean;
}) {
  return (
    <div className="flex justify-between gap-3 border-b border-border/40 pb-1.5 last:border-0">
      <dt className="text-muted">{label}</dt>
      <dd className={mono ? "font-mono" : ""}>{String(value ?? "—")}</dd>
    </div>
  );
}
