import { NextResponse } from "next/server";
import { z } from "zod";
import { backendFetch, DEMO_X402_PAYMENT, humaniseStatus } from "@/lib/backend";

export const runtime = "nodejs";

const TASK_TYPES = [
  "image_classification",
  "data_processing",
  "model_inference",
  "embedding_generation",
  "text_classification",
] as const;

const ADDRESS_RE = /^0x[a-fA-F0-9]{40}$/;

const JobSchema = z.object({
  task_id: z.string().min(1).max(128),
  task_type: z.enum(TASK_TYPES),
  consumer_address: z.string().regex(ADDRESS_RE),
  provider_address: z.string().regex(ADDRESS_RE),
  estimated_units: z.number().int().positive(),
  max_price_usdc: z.number().positive(),
  max_latency_ms: z.number().int().positive().optional(),
  params: z.record(z.unknown()).optional().default({}),
});

const BatchBody = z.object({
  jobs: z.array(JobSchema).min(1).max(500),
  allow_partial: z.boolean().optional().default(true),
});

export async function POST(req: Request) {
  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return NextResponse.json(
      { error: "Body must be valid JSON.", status: 400 },
      { status: 400 },
    );
  }

  const parsed = BatchBody.safeParse(raw);
  if (!parsed.success) {
    return NextResponse.json(
      {
        error: "Invalid batch request.",
        status: 400,
        detail: parsed.error.flatten().fieldErrors,
      },
      { status: 400 },
    );
  }

  try {
    const upstream = await backendFetch("/api/compute/batch", {
      method: "POST",
      headers: { "X-402-Payment": DEMO_X402_PAYMENT },
      body: JSON.stringify(parsed.data),
    });
    const text = await upstream.text();
    let body: unknown = text;
    try {
      body = JSON.parse(text);
    } catch {
      /* keep raw text */
    }
    if (!upstream.ok) {
      const detail = (body as { detail?: unknown } | null)?.detail;
      return NextResponse.json(
        {
          error: humaniseStatus(
            upstream.status,
            typeof detail === "string" ? detail : undefined,
          ),
          status: upstream.status,
          detail,
        },
        { status: upstream.status },
      );
    }
    return NextResponse.json(body, { status: 200 });
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
