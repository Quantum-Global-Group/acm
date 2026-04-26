"use client";

import { useCallback, useEffect, useState } from "react";

interface LeaderboardEntry {
  agent_id: string;
  name?: string | null;
  reputation_score: number;
  success_rate: number;
  avg_latency_ms: number;
  jobs_completed: number;
  jobs_failed: number;
}

interface LeaderboardResponse {
  leaderboard: LeaderboardEntry[];
}

interface ProviderEvent {
  agent_id: string;
  task_type: string | null;
  outcome: "success" | "failure";
  latency_ms: number | null;
  reason: string | null;
  timestamp: string;
}

interface EventsResponse {
  agent_id: string;
  events: ProviderEvent[];
}

export default function LeaderboardPage() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [topN, setTopN] = useState(10);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [events, setEvents] = useState<Record<string, ProviderEvent[]>>({});

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`/api/leaderboard?top_n=${topN}`);
      const body = (await r.json()) as LeaderboardResponse;
      if (!r.ok) {
        setError("Failed to load leaderboard.");
        setEntries([]);
      } else {
        setEntries(body.leaderboard);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [topN]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function toggleExpand(agentId: string) {
    if (expanded === agentId) {
      setExpanded(null);
      return;
    }
    setExpanded(agentId);
    if (!events[agentId]) {
      try {
        const r = await fetch(
          `/api/providers/${encodeURIComponent(agentId)}/events?limit=25`,
        );
        if (r.ok) {
          const body = (await r.json()) as EventsResponse;
          setEvents((prev) => ({ ...prev, [agentId]: body.events.reverse() }));
        }
      } catch {
        /* swallow */
      }
    }
  }

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Leaderboard</h1>
          <p className="text-muted text-sm">
            Top providers by reputation. Score combines success rate, experience, and latency.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs uppercase tracking-wider text-muted">Top</label>
          <select
            value={topN}
            onChange={(e) => setTopN(Number(e.target.value))}
            className="input w-20"
          >
            {[5, 10, 25, 50].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
          <button
            onClick={refresh}
            disabled={loading}
            className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-panel disabled:opacity-60"
          >
            {loading ? "…" : "Refresh"}
          </button>
        </div>
      </header>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
          {error}
        </div>
      )}

      {entries.length === 0 && !loading && !error && (
        <div className="rounded-lg border border-border bg-panel/60 p-8 text-center text-sm text-muted">
          No providers have completed jobs yet. Run compute requests to populate the leaderboard.
        </div>
      )}

      <section className="space-y-2">
        {entries.map((e, i) => {
          const rankTone =
            i === 0
              ? "border-accent/60 bg-accent/5"
              : i === 1
                ? "border-accent/30 bg-accent/[0.025]"
                : i === 2
                  ? "border-yellow-500/30 bg-yellow-500/[0.025]"
                  : "border-border bg-panel/60";
          const isOpen = expanded === e.agent_id;
          return (
            <div key={e.agent_id} className={`rounded-lg border ${rankTone}`}>
              <button
                type="button"
                onClick={() => toggleExpand(e.agent_id)}
                className="w-full grid grid-cols-[auto,1fr,auto,auto,auto,auto] items-center gap-4 px-5 py-4 text-left"
              >
                <div className="text-2xl font-mono w-10 text-center">
                  {i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : `#${i + 1}`}
                </div>
                <div>
                  <div className="font-semibold">{e.name || e.agent_id}</div>
                  <div className="text-[11px] text-muted font-mono">{e.agent_id}</div>
                </div>
                <Stat label="Score" value={e.reputation_score.toFixed(3)} tone="accent" />
                <Stat label="Success" value={`${(e.success_rate * 100).toFixed(1)}%`} />
                <Stat
                  label="Avg latency"
                  value={e.avg_latency_ms > 0 ? `${e.avg_latency_ms.toFixed(0)}ms` : "—"}
                />
                <Stat
                  label="Jobs"
                  value={`${e.jobs_completed}${e.jobs_failed > 0 ? ` / ${e.jobs_failed}` : ""}`}
                />
              </button>

              {isOpen && (
                <div className="border-t border-border/60 px-5 py-4 text-sm">
                  <div className="text-xs uppercase tracking-widest text-muted mb-2">
                    Recent events
                  </div>
                  {events[e.agent_id] === undefined ? (
                    <div className="text-muted">Loading…</div>
                  ) : events[e.agent_id].length === 0 ? (
                    <div className="text-muted">No events recorded.</div>
                  ) : (
                    <ul className="space-y-1 text-xs font-mono">
                      {events[e.agent_id].map((ev, idx) => (
                        <li
                          key={idx}
                          className="flex justify-between gap-3 border-b border-border/30 pb-1 last:border-0"
                        >
                          <span
                            className={
                              ev.outcome === "success"
                                ? "text-accent"
                                : "text-red-300"
                            }
                          >
                            {ev.outcome}
                          </span>
                          <span className="text-muted">{ev.task_type ?? "—"}</span>
                          <span className="text-muted">
                            {ev.latency_ms !== null ? `${ev.latency_ms.toFixed(0)}ms` : "—"}
                          </span>
                          <span className="text-muted truncate max-w-[40%]">
                            {ev.reason ?? ""}
                          </span>
                          <span className="text-muted">
                            {new Date(ev.timestamp).toLocaleTimeString()}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </section>

      <section className="rounded-lg border border-border bg-panel/60 p-5 text-sm space-y-2">
        <div className="text-xs uppercase tracking-widest text-muted">How score is computed</div>
        <code className="block font-mono text-xs">
          score = success_rate × min(1, log10(1 + jobs) / 2) × 1 / (1 + avg_latency_s)
        </code>
        <p className="text-muted text-xs">
          Successful work, experience, and low latency all multiply. Saturates near 1.0
          around 100 completed sub-second jobs.
        </p>
      </section>

      <style jsx>{`
        :global(.input) {
          background: #0b0d10;
          border: 1px solid #1e242c;
          border-radius: 0.375rem;
          padding: 0.35rem 0.5rem;
          font-size: 0.875rem;
          color: #e6edf3;
          outline: none;
        }
      `}</style>
    </div>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "accent";
}) {
  return (
    <div className="text-right">
      <div className="text-[10px] uppercase tracking-wider text-muted">{label}</div>
      <div
        className={`text-sm font-semibold ${tone === "accent" ? "text-accent font-mono" : ""}`}
      >
        {value}
      </div>
    </div>
  );
}
