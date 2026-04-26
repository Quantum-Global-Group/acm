export default function FundingPage() {
  return (
    <article className="prose prose-invert max-w-none space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">How funding works</h1>
        <p className="text-muted text-sm max-w-2xl">
          Before a consumer agent can pay for compute, its wallet must hold an internal balance
          inside the marketplace contract. That balance is funded once and reused across many
          settlements.
        </p>
      </header>

      <section className="rounded-lg border border-border bg-panel/60 p-5 space-y-3">
        <h2 className="text-base font-semibold">The two-step flow</h2>
        <ol className="list-decimal pl-5 space-y-2 text-sm">
          <li>
            <strong>Approve.</strong> The consumer wallet approves the marketplace contract to
            move USDC on its behalf, up to a chosen amount.
          </li>
          <li>
            <strong>Deposit.</strong> The consumer calls <code className="font-mono">deposit(amount)</code> on
            the marketplace, which pulls the approved USDC into an internal escrow balance.
          </li>
        </ol>
        <p className="text-sm text-muted">
          From then on, every <code className="font-mono">pay_for_compute</code> call debits the
          escrow and credits the provider in a single on-chain transaction.
        </p>
      </section>

      <section className="rounded-lg border border-border bg-panel/60 p-5 space-y-3">
        <h2 className="text-base font-semibold">Operator command</h2>
        <p className="text-sm text-muted">
          The repository ships a script that performs both steps for a configured consumer wallet.
          It is intended for operators, not stakeholders — keys never leave the host machine.
        </p>
        <pre className="rounded-md bg-bg border border-border p-3 text-xs overflow-x-auto">
{`python scripts/fund_escrow.py --amount 1.0 --dry-run   # preview
python scripts/fund_escrow.py --amount 1.0              # broadcast`}
        </pre>
      </section>

      <section className="rounded-lg border border-border bg-panel/60 p-5 space-y-3">
        <h2 className="text-base font-semibold">Why escrow?</h2>
        <p className="text-sm text-muted">
          Pre-funding lets agents settle in one transaction instead of two, reduces gas, and avoids
          a per-call USDC approval round-trip. It also makes per-task amounts well below a cent
          economically viable, which is the regime agent-to-agent compute lives in.
        </p>
      </section>
    </article>
  );
}
