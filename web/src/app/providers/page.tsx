"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { shorten } from "@/lib/explorer";

const TASK_TYPES = [
  "image_classification",
  "data_processing",
  "model_inference",
  "embedding_generation",
  "text_classification",
] as const;

type TaskType = (typeof TASK_TYPES)[number];

interface ProviderListing {
  agent_id: string;
  wallet_address: string;
  supported_tasks: TaskType[];
  pricing: Record<string, number>;
  default_unit_price: number;
  name?: string | null;
  description?: string | null;
  provider_endpoint?: string | null;
  registered_at: string;
  active: boolean;
  jobs_completed: number;
  jobs_failed: number;
  success_rate: number;
  avg_latency_ms: number;
  reputation_score: number;
}

interface ListResponse {
  providers: ProviderListing[];
  count: number;
}

interface ApiError {
  error: string;
  status: number;
  detail?: unknown;
}

export default function ProvidersPage() {
  const [providers, setProviders] = useState<ProviderListing[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [taskFilter, setTaskFilter] = useState<TaskType | "">("");
  const [maxPrice, setMaxPrice] = useState<string>("");
  const [minReputation, setMinReputation] = useState<string>("");
  const [includeInactive, setIncludeInactive] = useState(false);

  const qs = useMemo(() => {
    const p = new URLSearchParams();
    if (taskFilter) p.set("task_type", taskFilter);
    if (maxPrice) p.set("max_price", maxPrice);
    if (minReputation) p.set("min_reputation", minReputation);
    if (includeInactive) p.set("include_inactive", "true");
    return p.toString();
  }, [taskFilter, maxPrice, minReputation, includeInactive]);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(qs ? `/api/providers?${qs}` : "/api/providers");
      const body = (await r.json()) as ListResponse | ApiError;
      if (!r.ok) {
        setError((body as ApiError).error ?? "Failed to load providers.");
        setProviders([]);
        setCount(0);
      } else {
        const ok = body as ListResponse;
        setProviders(ok.providers);
        setCount(ok.count);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [qs]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Provider directory</h1>
          <p className="text-muted text-sm">
            Registered compute providers — discover by task, price, and reputation.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={refresh}
            disabled={loading}
            className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-panel disabled:opacity-60"
          >
            {loading ? "Loading…" : "Refresh"}
          </button>
        </div>
      </header>

      <section className="rounded-lg border border-border bg-panel/60 p-5 grid gap-4 md:grid-cols-4">
        <Field label="Task type">
          <select
            value={taskFilter}
            onChange={(e) => setTaskFilter(e.target.value as TaskType | "")}
            className="input"
          >
            <option value="">Any</option>
            {TASK_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Max price (USDC/unit)">
          <input
            type="number"
            min={0}
            step="0.0001"
            value={maxPrice}
            placeholder="any"
            onChange={(e) => setMaxPrice(e.target.value)}
            className="input"
          />
        </Field>
        <Field label="Min reputation">
          <input
            type="number"
            min={0}
            step="0.01"
            max={1}
            value={minReputation}
            placeholder="any"
            onChange={(e) => setMinReputation(e.target.value)}
            className="input"
          />
        </Field>
        <Field label="Include inactive">
          <label className="flex items-center gap-2 text-sm h-[34px]">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
            />
            <span>Show deregistered</span>
          </label>
        </Field>
      </section>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
          {error}
        </div>
      )}

      <section className="rounded-lg border border-border bg-panel/60 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-border/60 text-xs uppercase tracking-widest text-muted">
          <span>{count} provider{count === 1 ? "" : "s"}</span>
          <span>{loading ? "…" : ""}</span>
        </div>
        {providers.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted">
            No providers match these filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs uppercase tracking-wider text-muted">
                <tr className="border-b border-border/60">
                  <Th>Agent</Th>
                  <Th>Wallet</Th>
                  <Th>Tasks</Th>
                  <Th right>Price</Th>
                  <Th right>Reputation</Th>
                  <Th right>Success</Th>
                  <Th right>Latency</Th>
                  <Th right>Jobs</Th>
                </tr>
              </thead>
              <tbody>
                {providers.map((p) => (
                  <tr
                    key={p.agent_id}
                    className="border-b border-border/30 last:border-0 hover:bg-border/20"
                  >
                    <Td>
                      <div className="font-semibold">{p.name || p.agent_id}</div>
                      <div className="text-[11px] text-muted font-mono">{p.agent_id}</div>
                      {!p.active && (
                        <span className="inline-block mt-1 rounded bg-yellow-500/15 text-yellow-300 text-[10px] uppercase tracking-wider px-1.5 py-0.5">
                          inactive
                        </span>
                      )}
                    </Td>
                    <Td mono>{shorten(p.wallet_address, 6, 4)}</Td>
                    <Td>
                      <div className="flex flex-wrap gap-1">
                        {p.supported_tasks.map((t) => (
                          <span
                            key={t}
                            className="rounded bg-border/40 text-[10px] uppercase tracking-wider px-1.5 py-0.5"
                          >
                            {t.replace(/_/g, " ")}
                          </span>
                        ))}
                      </div>
                    </Td>
                    <Td right>
                      {taskFilter
                        ? `$${(p.pricing[taskFilter] ?? p.default_unit_price).toFixed(4)}`
                        : `$${p.default_unit_price.toFixed(4)}`}
                    </Td>
                    <Td right>
                      <ScoreBadge score={p.reputation_score} />
                    </Td>
                    <Td right>{(p.success_rate * 100).toFixed(1)}%</Td>
                    <Td right>
                      {p.avg_latency_ms > 0 ? `${p.avg_latency_ms.toFixed(0)}ms` : "—"}
                    </Td>
                    <Td right>
                      <span className="text-accent">{p.jobs_completed}</span>
                      {p.jobs_failed > 0 && (
                        <span className="text-red-300"> / {p.jobs_failed}</span>
                      )}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <RegisterCard onRegistered={refresh} />

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

function ScoreBadge({ score }: { score: number }) {
  const pct = Math.min(1, Math.max(0, score));
  const tone =
    pct >= 0.5 ? "text-accent" : pct >= 0.2 ? "text-yellow-300" : "text-muted";
  return <span className={`font-mono ${tone}`}>{score.toFixed(3)}</span>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-1">
      <span className="text-xs font-medium uppercase tracking-wider text-muted">{label}</span>
      {children}
    </label>
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
      className={`px-4 py-3 align-top ${right ? "text-right" : ""} ${mono ? "font-mono" : ""}`}
    >
      {children}
    </td>
  );
}

// ----------------------------------------------------------- Register card

function RegisterCard({ onRegistered }: { onRegistered: () => void }) {
  const [open, setOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  const [agentId, setAgentId] = useState("");
  const [wallet, setWallet] = useState("");
  const [tasks, setTasks] = useState<TaskType[]>(["image_classification"]);
  const [defaultPrice, setDefaultPrice] = useState<number>(0.0003);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [endpoint, setEndpoint] = useState("");

  function toggleTask(t: TaskType) {
    setTasks((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setOk(null);
    try {
      const payload: Record<string, unknown> = {
        agent_id: agentId.trim(),
        wallet_address: wallet.trim(),
        supported_tasks: tasks,
        default_unit_price: defaultPrice,
      };
      if (name.trim()) payload.name = name.trim();
      if (description.trim()) payload.description = description.trim();
      if (endpoint.trim()) payload.provider_endpoint = endpoint.trim();

      const r = await fetch("/api/providers/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await r.json();
      if (!r.ok) {
        setError(body as ApiError);
      } else {
        setOk(`Registered ${agentId}.`);
        onRegistered();
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
    <section className="rounded-lg border border-border bg-panel/60">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-3 text-left"
      >
        <span className="text-sm font-semibold">
          {open ? "— Collapse" : "+ Register a provider"}
        </span>
        <span className="text-xs text-muted">
          {open ? "" : "Advertise compute capacity"}
        </span>
      </button>

      {open && (
        <form onSubmit={submit} className="px-5 pb-5 space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Field label="Agent ID">
              <input
                className="input"
                value={agentId}
                onChange={(e) => setAgentId(e.target.value)}
                required
              />
            </Field>
            <Field label="Wallet address">
              <input
                className="input font-mono"
                value={wallet}
                placeholder="0x…"
                onChange={(e) => setWallet(e.target.value)}
                required
              />
            </Field>
            <Field label="Default unit price (USDC)">
              <input
                className="input"
                type="number"
                min={0}
                step="0.0001"
                value={defaultPrice}
                onChange={(e) => setDefaultPrice(Number(e.target.value))}
                required
              />
            </Field>
            <Field label="Display name (optional)">
              <input
                className="input"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </Field>
            <Field label="Provider endpoint (optional)">
              <input
                className="input font-mono"
                value={endpoint}
                placeholder="https://my-provider.com/infer"
                onChange={(e) => setEndpoint(e.target.value)}
              />
            </Field>
            <Field label="Description (optional)">
              <input
                className="input"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </Field>
          </div>

          <div>
            <div className="text-xs font-medium uppercase tracking-wider text-muted mb-1.5">
              Supported tasks
            </div>
            <div className="flex flex-wrap gap-2">
              {TASK_TYPES.map((t) => (
                <label
                  key={t}
                  className={`cursor-pointer rounded border px-2 py-1 text-xs ${
                    tasks.includes(t)
                      ? "border-accent/60 bg-accent/10 text-accent"
                      : "border-border bg-panel/40 text-muted"
                  }`}
                >
                  <input
                    type="checkbox"
                    className="sr-only"
                    checked={tasks.includes(t)}
                    onChange={() => toggleTask(t)}
                  />
                  {t.replace(/_/g, " ")}
                </label>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting || tasks.length === 0}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg hover:bg-accent/90 transition disabled:opacity-60"
          >
            {submitting ? "Registering…" : "Register provider"}
          </button>

          {error && (
            <div className="rounded border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">
              {error.error}
              {error.detail !== undefined && (
                <pre className="mt-1 text-xs whitespace-pre-wrap break-all">
                  {JSON.stringify(error.detail, null, 2)}
                </pre>
              )}
            </div>
          )}
          {ok && (
            <div className="rounded border border-accent/40 bg-accent/5 p-3 text-sm text-accent">
              {ok}
            </div>
          )}
        </form>
      )}
    </section>
  );
}
