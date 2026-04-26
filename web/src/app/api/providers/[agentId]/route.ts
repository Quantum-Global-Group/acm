import { NextResponse } from "next/server";
import { backendFetch, humaniseStatus } from "@/lib/backend";

export const runtime = "nodejs";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ agentId: string }> },
) {
  const { agentId } = await params;
  try {
    const r = await backendFetch(`/api/providers/${encodeURIComponent(agentId)}`);
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

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ agentId: string }> },
) {
  const { agentId } = await params;
  try {
    const r = await backendFetch(`/api/providers/${encodeURIComponent(agentId)}`, {
      method: "DELETE",
    });
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
