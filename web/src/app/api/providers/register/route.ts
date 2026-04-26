import { NextResponse } from "next/server";
import { z } from "zod";
import { backendFetch, humaniseStatus } from "@/lib/backend";

export const runtime = "nodejs";

const TASK_TYPES = [
  "image_classification",
  "data_processing",
  "model_inference",
  "embedding_generation",
  "text_classification",
] as const;

const ADDRESS_RE = /^0x[a-fA-F0-9]{40}$/;

const RegisterBody = z.object({
  agent_id: z.string().min(1).max(128),
  wallet_address: z.string().regex(ADDRESS_RE),
  supported_tasks: z.array(z.enum(TASK_TYPES)).min(1),
  pricing: z.record(z.number().nonnegative()).optional().default({}),
  default_unit_price: z.number().positive().optional(),
  name: z.string().max(128).optional(),
  description: z.string().max(512).optional(),
  provider_endpoint: z.string().url().optional(),
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

  const parsed = RegisterBody.safeParse(raw);
  if (!parsed.success) {
    return NextResponse.json(
      {
        error: "Invalid provider registration.",
        status: 400,
        detail: parsed.error.flatten().fieldErrors,
      },
      { status: 400 },
    );
  }

  try {
    const upstream = await backendFetch("/api/providers/register", {
      method: "POST",
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
    return NextResponse.json(body, { status: 201 });
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
