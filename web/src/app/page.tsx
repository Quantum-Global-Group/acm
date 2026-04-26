import Link from "next/link";

const STEPS = [
  {
    title: "Consumer agent requests compute",
    body: "An autonomous agent calls the marketplace API with a task, a price ceiling, and an x402 payment proof.",
  },
  {
    title: "Marketplace meters and prices the work",
    body: "Usage is metered, total cost is computed, and a per-unit price ceiling is enforced before any money moves.",
  },
  {
    title: "Settlement on Arc",
    body: "USDC is transferred from the consumer's marketplace escrow to the provider on Arc, atomically and on-chain.",
  },
];

export default function Home() {
  return (
    <div className="space-y-12">
      <section className="space-y-4">
        <h1 className="text-3xl font-semibold tracking-tight">
          Autonomous compute, settled in stablecoin.
        </h1>
        <p className="text-muted max-w-2xl">
          Software agents pay each other for compute in USDC on the Arc network. No invoices, no
          chargebacks, no escrow officers — just metered usage and atomic settlement.
        </p>
        <div className="flex gap-3 pt-2">
          <Link
            href="/compute"
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg hover:bg-accent/90 transition"
          >
            Run a compute request
          </Link>
          <Link
            href="/status"
            className="rounded-md border border-border px-4 py-2 text-sm hover:bg-panel transition"
          >
            View live status
          </Link>
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold uppercase tracking-widest text-muted mb-4">
          How it works
        </h2>
        <ol className="grid gap-4 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <li
              key={s.title}
              className="rounded-lg border border-border bg-panel/60 p-5 space-y-2"
            >
              <div className="text-xs text-accent font-mono">Step {i + 1}</div>
              <div className="font-semibold">{s.title}</div>
              <div className="text-sm text-muted">{s.body}</div>
            </li>
          ))}
        </ol>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-panel/60 p-5">
          <h3 className="font-semibold mb-1">Why agents need this</h3>
          <p className="text-sm text-muted">
            Multi-agent systems need a way to pay for resources without humans in the loop. A
            marketplace with on-chain settlement removes counterparty risk and makes pricing a
            first-class signal.
          </p>
        </div>
        <div className="rounded-lg border border-border bg-panel/60 p-5">
          <h3 className="font-semibold mb-1">Why Arc</h3>
          <p className="text-sm text-muted">
            Arc is purpose-built for stablecoin settlement at low cost. Sub-cent transactions are
            economically viable, which is exactly what per-task agent payments require.
          </p>
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold uppercase tracking-widest text-muted mb-4">
          Explore the marketplace
        </h2>
        <div className="grid gap-4 md:grid-cols-2">
          <FeatureLink
            href="/providers"
            title="Provider directory"
            body="Browse registered providers, filter by task and reputation, and register new compute capacity."
          />
          <FeatureLink
            href="/leaderboard"
            title="Reputation leaderboard"
            body="Top providers ranked by success rate, experience, and latency. Click any row for recent events."
          />
          <FeatureLink
            href="/batch"
            title="Batch compute"
            body="Submit many jobs at once and earn volume discounts up to 15%. Per-job settlements stay on-chain."
          />
          <FeatureLink
            href="/status"
            title="Live status"
            body="Throughput, settlement mode, and network metadata — live from the marketplace backend."
          />
        </div>
      </section>
    </div>
  );
}

function FeatureLink({
  href,
  title,
  body,
}: {
  href: string;
  title: string;
  body: string;
}) {
  return (
    <Link
      href={href}
      className="rounded-lg border border-border bg-panel/60 p-5 hover:border-accent/60 hover:bg-accent/5 transition group"
    >
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">{title}</h3>
        <span className="text-accent opacity-0 group-hover:opacity-100 transition">→</span>
      </div>
      <p className="text-sm text-muted mt-1">{body}</p>
    </Link>
  );
}
