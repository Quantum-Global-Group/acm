import { NextResponse } from "next/server";
import { backendFetch, humaniseStatus } from "@/lib/backend";

export const runtime = "nodejs";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const qs = url.searchParams.toString();
  const suffix = qs.length > 0 ? `?${qs}` : "";
  try {
    const r = await backendFetch(`/api/leaderboard${suffix}`);
    const body = await r.json();
    return NextResponse.json(body, { status: r.status });
  } catch (err) {
    return NextResponse.json(
      {
        error: humaniseStatus(503),
        status: 503,
        detail: err instanceof Error ? err.message : String(err),
      },
      { status: 503 },
    );
  }
}
