"use client";

import { useState } from "react";
import { txUrl, shorten } from "@/lib/explorer";

const TASK_TYPES = [
  { value: "image_classification", label: "Image classification" },
  { value: "data_processing", label: "Data processing" },
  { value: "model_inference", label: "Model inference" },
  { value: "embedding_generation", label: "Embedding generation" },
] as const;

type TaskType = (typeof TASK_TYPES)[number]["value"];

interface ComputeResult {
  task_id: string;
  status: string;
  actual_cost_usdc: number;
  arc_tx_hash: string | null;
  result?: Record<string, unknown> | null;
  error?: string | null;
  timestamp: string;
}

interface ApiError {
  error: string;
  status: number;
  detail?: unknown;
}

function newTaskId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `task-${crypto.randomUUID().slice(0, 8)}`;
  }
  return `task-${Math.random().toString(16).slice(2, 10)}`;
}

export default function ComputePage() {
  const [taskId, setTaskId] = useState<string>(() => newTaskId());
  const [taskType, setTaskType] = useState<TaskType>("image_classification");
  const [consumer, setConsumer] = useState("");
  const [provider, setProvider] = useState("");
  const [units, setUnits] = useState<number>(100);
  const [maxPrice, setMaxPrice] = useState<number>(0.05);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ComputeResult | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setResult(null);
    setError(null);

    try {
      const res = await fetch("/api/compute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_id: taskId,
          task_type: taskType,
          consumer_address: consumer.trim(),
          provider_address: provider.trim(),
          estimated_units: Number(units),
          max_price_usdc: Number(maxPrice),
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body as ApiError);
      } else {
        setResult(body as ComputeResult);
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

  const explorer = txUrl(result?.arc_tx_hash);

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Run a compute request</h1>
        <p className="text-muted text-sm max-w-2xl">
          Submit a task on behalf of a consumer agent. The marketplace meters and prices the work,
          then settles USDC from the consumer&apos;s on-chain escrow to the provider.
        </p>
      </header>

      <form
        onSubmit={handleSubmit}
        className="rounded-lg border border-border bg-panel/60 p-6 space-y-5"
      >
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Task ID" hint="Unique identifier for this request">
            <div className="flex gap-2">
              <input
                value={taskId}
                onChange={(e) => setTaskId(e.target.value)}
                className="input flex-1"
                required
              />
              <button
                type="button"
                onClick={() => setTaskId(newTaskId())}
                className="rounded-md border border-border px-3 text-sm hover:bg-border/60"
              >
                Regenerate
              </button>
            </div>
          </Field>

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

          <Field label="Consumer address" hint="Funded escrow on the marketplace">
            <input
              value={consumer}
              onChange={(e) => setConsumer(e.target.value)}
              placeholder="0x…"
              className="input font-mono"
              required
            />
          </Field>

          <Field label="Provider address" hint="Receives the USDC payment">
            <input
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              placeholder="0x…"
              className="input font-mono"
              required
            />
          </Field>

          <Field label="Estimated units" hint="Higher units split the per-unit price">
            <input
              type="number"
              min={1}
              value={units}
              onChange={(e) => setUnits(Number(e.target.value))}
              className="input"
              required
            />
          </Field>

          <Field label="Max price (USDC)" hint="Caller&apos;s spending ceiling">
            <input
              type="number"
              min={0}
              step="0.001"
              value={maxPrice}
              onChange={(e) => setMaxPrice(Number(e.target.value))}
              className="input"
              required
            />
          </Field>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg hover:bg-accent/90 transition disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {submitting ? "Settling…" : "Submit and settle"}
        </button>
      </form>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-5 space-y-2">
          <div className="font-semibold text-red-300">
            Request failed (HTTP {error.status})
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
        <div className="rounded-lg border border-accent/40 bg-accent/5 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-widest text-accent font-mono">
                Settled
              </div>
              <div className="text-lg font-semibold">{result.task_id}</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-muted">Cost</div>
              <div className="text-2xl font-semibold">
                ${result.actual_cost_usdc.toFixed(6)} <span className="text-sm text-muted">USDC</span>
              </div>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-2 text-sm">
            <Info label="Status" value={result.status} mono />
            <Info
              label="Arc transaction"
              value={shorten(result.arc_tx_hash, 10, 8) || "—"}
              mono
            />
          </div>

          {explorer && (
            <a
              href={explorer}
              target="_blank"
              rel="noreferrer noopener"
              className="inline-block rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg hover:bg-accent/90 transition"
            >
              Open transaction in explorer ↗
            </a>
          )}

          <details className="text-xs text-muted">
            <summary className="cursor-pointer">Raw response</summary>
            <pre className="mt-2 whitespace-pre-wrap break-all">
              {JSON.stringify(result, null, 2)}
            </pre>
          </details>
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

function Info({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div className="text-xs text-muted">{label}</div>
      <div className={mono ? "font-mono break-all" : ""}>{value}</div>
    </div>
  );
}
