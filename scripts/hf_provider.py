#!/usr/bin/env python3
"""
Reference provider — runs a real Hugging Face text-classification pipeline
and registers itself with the marketplace backend.

Usage:
    # Start the marketplace backend on :8000, then:
    python scripts/hf_provider.py \\
        --marketplace-url http://localhost:8000 \\
        --self-url http://localhost:8001 \\
        --host 0.0.0.0 \\
        --port 8001 \\
        --wallet 0xAAAA...AAAA \\
        --agent-id hf-sentiment-1 \\
        --model distilbert-base-uncased-finetuned-sst-2-english

The provider:
    1. Starts a FastAPI server on :8001 with POST /infer
    2. POSTs to <marketplace>/api/providers/register with its provider_endpoint
    3. When the marketplace receives a compute request, it forwards the job to
       <self-url>/infer, which runs the HF pipeline and returns the labels.

Dependencies (not installed by default — this is a reference, not required
for the core marketplace):
    pip install transformers torch
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from typing import Any, Dict, Optional

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

log = logging.getLogger("hf_provider")


class InferRequest(BaseModel):
    """Mirrors backend.models.ComputeRequestModel for what we actually use."""
    task_id: str
    task_type: str
    estimated_units: int
    params: Dict[str, Any] = {}


class InferResponse(BaseModel):
    task_id: str
    result: Any
    compute_time_ms: int
    tokens_used: int


def build_app(model_name: str) -> FastAPI:
    app = FastAPI(title="HF Provider", version="0.1.0")

    try:
        from transformers import pipeline  # type: ignore
    except ImportError:
        log.warning(
            "transformers not installed — provider will return stub results. "
            "Install with: pip install transformers torch"
        )
        pipeline = None  # type: ignore

    # Lazy init to avoid paying model-load cost on import.
    state: Dict[str, Any] = {"pipe": None}

    def _get_pipe():
        if state["pipe"] is None and pipeline is not None:
            log.info("Loading model %s (first request — may take a minute)…", model_name)
            state["pipe"] = pipeline("sentiment-analysis", model=model_name)
        return state["pipe"]

    @app.get("/health")
    async def health() -> Dict[str, Any]:
        return {"status": "ok", "model": model_name, "loaded": state["pipe"] is not None}

    @app.post("/infer", response_model=InferResponse)
    async def infer(req: InferRequest) -> InferResponse:
        text = req.params.get("text") or req.params.get("input") or "hello world"
        t0 = time.perf_counter()
        pipe = _get_pipe()
        if pipe is None:
            result: Any = {"stub": True, "label": "NEUTRAL", "score": 0.5, "text": text}
        else:
            try:
                result = pipe(text)
            except Exception as exc:  # pragma: no cover — inference error path
                raise HTTPException(status_code=500, detail=f"inference_failed: {exc}")
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return InferResponse(
            task_id=req.task_id,
            result=result,
            compute_time_ms=elapsed_ms,
            tokens_used=max(1, len(text.split())),
        )

    return app


def register_with_marketplace(
    marketplace_url: str,
    registration: Dict[str, Any],
) -> None:
    url = marketplace_url.rstrip("/") + "/api/providers/register"
    log.info("Registering with marketplace at %s", url)
    try:
        r = httpx.post(url, json=registration, timeout=10.0)
        r.raise_for_status()
        log.info("Registration OK: %s", r.json().get("agent_id"))
    except httpx.HTTPError as exc:
        log.error("Registration failed: %s", exc)
        sys.exit(1)


def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--marketplace-url", default="http://localhost:8000")
    ap.add_argument("--self-url", required=True, help="Public URL the marketplace should dispatch to (e.g. http://localhost:8001)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8001)
    ap.add_argument("--agent-id", required=True)
    ap.add_argument("--wallet", required=True, help="Provider wallet address (0x…)")
    ap.add_argument("--model", default="distilbert-base-uncased-finetuned-sst-2-english")
    ap.add_argument("--price", type=float, default=0.0003, help="Per-unit price in USDC")
    ap.add_argument("--name", default="HF Sentiment Provider")
    ap.add_argument("--description", default="DistilBERT sentiment classification via HuggingFace pipelines.")
    ap.add_argument("--skip-register", action="store_true", help="Don't register with marketplace (for local dev)")
    return ap.parse_args(argv)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    args = parse_args()

    app = build_app(args.model)

    if not args.skip_register:
        register_with_marketplace(args.marketplace_url, {
            "agent_id": args.agent_id,
            "wallet_address": args.wallet,
            "supported_tasks": ["text_classification", "model_inference"],
            "pricing": {
                "text_classification": args.price,
                "model_inference": args.price,
            },
            "default_unit_price": args.price,
            "name": args.name,
            "description": args.description,
            "provider_endpoint": args.self_url.rstrip("/") + "/infer",
        })

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
