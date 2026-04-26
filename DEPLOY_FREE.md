# Free Hosting Guide

This project is easiest to host for free as two services:

- **Backend:** FastAPI on Render free tier
- **Frontend:** Next.js on Vercel free tier

The deployed demo should run with `SETTLEMENT_SIMULATE=true` unless you are ready to add funded Arc testnet credentials. Do not add `PRIVATE_KEY` or Circle secrets for a public demo deployment.

## 1. Deploy Backend On Render

1. Push this repository to GitHub.
2. In Render, choose **New > Blueprint** and select the repository.
3. Render will read `render.yaml` and create the `acm-backend` web service.
4. Wait for the deploy to finish, then open:

```text
https://<your-render-service>.onrender.com/health
```

Expected health shape:

```json
{
  "status": "ok",
  "settlement_simulate": true
}
```

Render free services can sleep after inactivity. The first request after sleep may take a minute.

If Render does not offer the Blueprint, confirm `render.yaml` is committed at
the repository root in GitHub, next to `requirements.txt` and `backend/`.
Render cannot see local untracked files.

## 2. Deploy Frontend On Vercel

1. In Vercel, import the same GitHub repository.
2. Set **Root Directory** to:

```text
web
```

Use the **Next.js** framework preset. Leave **Output Directory** blank; do not
set it to `public` or `.next`.

3. Add these environment variables:

```text
BACKEND_URL=https://<your-render-service>.onrender.com
DEMO_X402_PAYMENT=proof
NEXT_PUBLIC_APP_NAME=Agent-to-Agent Compute Marketplace
NEXT_PUBLIC_EXPLORER_URL=https://testnet.arc.io
NEXT_PUBLIC_EXPLORER_TX_PATH=/tx/
```

4. Deploy.

If the Vercel URL returns Vercel's plain `404: NOT_FOUND`, confirm the `web/`
directory is committed and pushed, then redeploy with the root directory set to
`web`.

## 3. Smoke Test The Public App

After both services are live:

1. Open the Vercel URL.
2. Visit `/status` and confirm the backend is reachable.
3. Register a provider on `/providers`.
4. Submit a compute request on `/compute`.
5. Confirm `/leaderboard` shows the provider after a successful job.

## 4. Live Settlement Later

Only switch away from simulated settlement after the demo is stable and you have funded testnet credentials:

```text
SETTLEMENT_SIMULATE=false
ARC_CONTRACT_ADDRESS=<deployed marketplace contract>
PRIVATE_KEY=<backend signer testnet key>
```

For live runs, the consumer must have an internal marketplace escrow balance. Funding only the EOA wallet is not enough.
