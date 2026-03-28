#!/usr/bin/env python3
"""Lightweight local embedding adapter for embeddy remote mode."""

from __future__ import annotations

import hashlib
import math
import os
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

DIMENSION = int(os.getenv("MOCK_EMBED_DIM", "2048"))
MODEL_NAME = os.getenv("MOCK_EMBED_MODEL", "mock-embedder-v1")

app = FastAPI(title="Mock Embedder", version="1.0.0")


class EncodeRequest(BaseModel):
    inputs: list[dict[str, Any]] = Field(default_factory=list)
    instruction: str | None = None


def _stable_vector(text: str, dim: int) -> list[float]:
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    counter = 0
    while len(values) < dim:
        block = hashlib.sha256(seed + counter.to_bytes(8, "little")).digest()
        for idx in range(0, len(block), 4):
            if len(values) >= dim:
                break
            raw = int.from_bytes(block[idx : idx + 4], "little", signed=False)
            values.append((raw / 4294967295.0) * 2.0 - 1.0)
        counter += 1

    norm = math.sqrt(sum(v * v for v in values))
    if norm <= 0:
        return values
    return [v / norm for v in values]


def _extract_text(item: dict[str, Any]) -> str:
    for key in ("text", "content", "query"):
        value = item.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "model": MODEL_NAME, "dimension": DIMENSION}


@app.post("/encode")
async def encode(body: EncodeRequest) -> dict[str, Any]:
    vectors: list[list[float]] = []
    for item in body.inputs:
        text = _extract_text(item)
        if body.instruction:
            text = f"{body.instruction}\n{text}"
        vectors.append(_stable_vector(text, DIMENSION))

    return {
        "embeddings": vectors,
        "model": MODEL_NAME,
        "dimension": DIMENSION,
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("MOCK_EMBED_HOST", "127.0.0.1")
    port = int(os.getenv("MOCK_EMBED_PORT", "8586"))
    uvicorn.run(app, host=host, port=port, log_level="info")
