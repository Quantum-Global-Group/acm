"use client";

import { useMemo, useState } from "react";
import { shorten, txUrl } from "@/lib/explorer";

const TASK_TYPES = [
  { value: "image_classification", label: "Image classification" },
  { value: "data_processing", label: "Data processing" },
  { value: "model_inference", label: "Model inference" },
  { value: "embedding_generation", label: "Embedding generation" },
  { value: "text_classification", label: "Text classification" },
] as const;

type TaskType = (typeof TASK_TYPES)[number]["value"];

interface JobResult {
  task_id: string;
  status: string;
  actual_cost_usdc: number;
  arc_tx_hash: string | null;
  error?: string | null;
}

interface BatchResponse {
  results: JobResult[];
  job_count: number;
  successful_count: number;
  failed_count: number;
  discount_rate: number;
  total_cost_usdc: number;
  gross_cost_usdc: number;
  savings_usdc: number;
}

interface ApiError {
  error: string;
  status: number;
  detail?: unknown;
}

const DISCOUNT_TIERS = [
  { min: 1, max: 9, rate: 0 },
  { min: 10, max: 49, rate: 0.05 },
  { min: 50, max: 99, rate: 0.1 },
  { min: 100, max: Infinity, rate: 0.15 },
];

function expectedDiscount(jobCount: number): number {
  const tier = DISCOUNT_TIERS.find((t) => jobCount >= t.min && jobCount <= t.max);
  return tier?.rate ?? 0;
}

function randomTaskId(prefix: string, i: number): string {
  const rand =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID().slice(0, 6)
      : Math.random().toString(16).slice(2, 8);
  return `${prefix}-${rand}-${i}`;
}

export default function BatchPage() {
  const [taskType, setTaskType] = useState<TaskType>("image_classification");
  const [consumer, setConsumer] = useState("");
  const [provider, setProvider] = useState("");
  const [jobCount, setJobCount] = useState(50);
  const [units, setUnits] = useState(10);
  const [maxPrice, setMaxPrice] = useState(0.01);
  const [allowPartial, setAllowPartial] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<BatchResponse | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  const preview = useMemo(() => expectedDiscount(jobCount), [jobCount]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setResult(null);

    const prefix = `batch-${Date.now().toString(36)}`;
    const jobs = Array.from({ length: jobCount }, (_, i) => ({
      task_id: randomTaskId(prefix, i),
      task_type: taskType,
      consumer_address: consumer.trim(),
      provider_address: provider.trim(),
      estimated_units: Number(units),
      max_price_usdc: Number(maxPrice),
    }));

    try {
      const r = await fetch("/api/compute/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jobs, allow_partial: allowPartial }),
      });
      const body = await r.json();
      if (!r.ok) {
        setError(body as ApiError);
      } else {
        setResult(body as BatchResponse);
      }
    } catch (err) {
      setError({
        error: "Network error reaching the marketplace UI server.",
        status: 0,
        detail: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Batch compute</h1>
        <p className="text-muted text-sm max-w-2xl">
          Submit many jobs in a single call and earn a volume discount. Use the same
          consumer/provider pair for the whole batch — each job is metered and settled
          individually, but discounted together.
        </p>
      </header>

      <section className="grid gap-3 md:grid-cols-4">
        {DISCOUNT_TIERS.map((t) => {
          const active = jobCount >= t.min && jobCount <= t.max;
          return (
            <div
              key={t.min}
              className={`rounded-lg border p-4 text-center ${
                active
                  ? "border-accent/60 bg-accent/10"
                  : "border-border bg-panel/60"
              }`}
            >
              <div className="text-xs uppercase tracking-widest text-muted">
                {t.max === Infinity ? `${t.min}+ jobs` : `${t.min}–${t.max} jobs`}
              </div>
              <div
                className={`mt-1 text-2xl font-semibold ${
                  active ? "text-accent" : ""
                }`}
              >
                {(t.rate * 100).toFixed(0)}%
              </div>
              <div className="text-[11px] text-muted">discount</div>
            </div>
          );
        })}
      </section>

      <form
        onSubmit={submit}
        className="rounded-lg border border-border bg-panel/60 p-6 space-y-5"
      >
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Task type">
            <select
              value={taskType}
              onChange={(e) => setTaskType(e.target.value as TaskType)}
              className="input"
            >
              {TASK_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Number of jobs" hint={`Current tier: ${(preview * 100).toFixed(0)}% off`}>
            <input
              type="number"
              min={1}
              max={500}
              value={jobCount}
              onChange={(e) => setJobCount(Number(e.target.value))}
              className="input"
              required
            />
          </Field>
          <Field label="Consumer address">
            <input
              value={consumer}
              onChange={(e) => setConsumer(e.target.value)}
              placeholder="0x…"
              className="input font-mono"
              required
            />
          </Field>
          <Field label="Provider address">
            <input
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              placeholder="0x…"
              className="input font-mono"
              required
            />
          </Field>
          <Field label="Units per job">
            <input
              type="number"
              min={1}
              value={units}
              onChange={(e) => setUnits(Number(e.target.value))}
              className="input"
              required
            />
          </Field>
          <Field label="Max price per job (USDC)">
            <input
              type="number"
              min={0}
              step="0.0001"
              value={maxPrice}
              onChange={(e) => setMaxPrice(Number(e.target.value))}
              className="input"
              required
            />
          </Field>
        </div>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={allowPartial}
            onChange={(e) => setAllowPartial(e.target.checked)}
          />
          <span>
            Allow partial — continue batch if individual jobs fail (otherwise abort on first
            failure)
          </span>
        </label>

        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg hover:bg-accent/90 transition disabled:opacity-60"
        >
          {submitting ? `Settling ${jobCount} jobs…` : `Submit batch of ${jobCount}`}
        </button>
      </form>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-5 space-y-2">
          <div className="font-semibold text-red-300">
            Batch failed (HTTP {error.status})
          </div>
          <div className="text-sm">{error.error}</div>
          {error.detail !== undefined && (
            <details className="text-xs text-muted">
              <summary className="cursor-pointer">Details</summary>
              <pre className="mt-2 whitespace-pre-wrap break-all">
                {JSON.stringify(error.detail, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <section className="grid gap-3 md:grid-cols-4">
            <Summary
              label="Jobs"
              value={`${result.successful_count} / ${result.job_count}`}
              sub={result.failed_count > 0 ? `${result.failed_count} failed` : "all settled"}
              tone={result.failed_count > 0 ? "warn" : "ok"}
            />
            <Summary
              label="Discount"
              value={`${(result.discount_rate * 100).toFixed(0)}%`}
              sub="volume tier applied"
              tone="accent"
            />
            <Summary
              label="Gross cost"
              value={`$${result.gross_cost_usdc.toFixed(6)}`}
              sub="before discount"
            />
            <Summary
              label="Paid / saved"
              value={`$${result.total_cost_usdc.toFixed(6)}`}
              sub={`saved $${result.savings_usdc.toFixed(6)}`}
              tone="accent"
            />
          </section>

          <div className="rounded-lg border border-border bg-panel/60 overflow-hidden">
            <div className="px-5 py-3 border-b border-border/60 flex items-center justify-between">
              <span className="text-sm font-semibold">Per-job results</span>
              <span className="text-xs text-muted">{result.results.length} shown</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-xs uppercase tracking-wider text-muted">
                  <tr className="border-b border-border/60">
                    <Th>Task ID</Th>
                    <Th>Status</Th>
                    <Th right>Cost</Th>
                    <Th>Tx</Th>
                  </tr>
                </thead>
                <tbody>
                  {result.results.map((job) => {
                    const link = txUrl(job.arc_tx_hash);
                    return (
                      <tr
                        key={job.task_id}
                        className="border-b border-border/30 last:border-0"
                      >
                        <Td mono>{job.task_id}</Td>
                        <Td>
                          <span
                            className={`rounded px-1.5 py-0.5 text-[10px] uppercase tracking-wider ${
                              job.status === "success"
                                ? "bg-accent/15 text-accent"
                                : "bg-red-500/15 text-red-300"
                            }`}
                          >
                            {job.status}
                          </span>
                          {job.error && (
                            <div className="text-[11px] text-red-300 mt-1">
                              {job.error}
                            </div>
                          )}
                        </Td>
                        <Td right>${job.actual_cost_usdc.toFixed(6)}</Td>
                        <Td mono>
                          {link ? (
                            <a
                              href={link}
                              target="_blank"
                              rel="noreferrer noopener"
                              className="text-accent hover:underline"
                            >
                              {shorten(job.arc_tx_hash, 8, 6)} ↗
                            </a>
                          ) : (
                            <span className="text-muted">
                              {shorten(job.arc_tx_hash, 8, 6) || "—"}
                            </span>
                          )}
                        </Td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        :global(.input) {
          width: 100%;
          background: #0b0d10;
          border: 1px solid #1e242c;
          border-radius: 0.375rem;
          padding: 0.5rem 0.75rem;
          font-size: 0.875rem;
          color: #e6edf3;
          outline: none;
        }
        :global(.input:focus) {
          border-color: #5eead4;
          box-shadow: 0 0 0 3px rgba(94, 234, 212, 0.15);
        }
      `}</style>
    </div>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block space-y-1">
      <span className="text-xs font-medium uppercase tracking-wider text-muted">{label}</span>
      {children}
      {hint && <span className="block text-[11px] text-muted">{hint}</span>}
    </label>
  );
}

function Summary({
  label,
  value,
  sub,
  tone,
}: {
  label: string;
  value: string;
  sub?: string;
  tone?: "accent" | "warn" | "ok";
}) {
  const ring =
    tone === "accent"
      ? "border-accent/40 bg-accent/5"
      : tone === "warn"
        ? "border-yellow-500/40 bg-yellow-500/5"
        : tone === "ok"
          ? "border-accent/30 bg-accent/5"
          : "border-border bg-panel/60";
  return (
    <div className={`rounded-lg border ${ring} p-4`}>
      <div className="text-xs uppercase tracking-widest text-muted">{label}</div>
      <div className="mt-1 text-xl font-semibold">{value}</div>
      {sub && <div className="text-[11px] text-muted mt-0.5">{sub}</div>}
    </div>
  );
}

function Th({ children, right }: { children: React.ReactNode; right?: boolean }) {
  return (
    <th className={`px-4 py-2 font-medium ${right ? "text-right" : "text-left"}`}>
      {children}
    </th>
  );
}

function Td({
  children,
  right,
  mono,
}: {
  children: React.ReactNode;
  right?: boolean;
  mono?: boolean;
}) {
  return (
    <td
      className={`px-4 py-2 align-top ${right ? "text-right" : ""} ${mono ? "font-mono text-xs" : ""}`}
    >
      {children}
    </td>
  );
}
