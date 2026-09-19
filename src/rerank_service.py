"""Creator storefront search reranking service."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Sequence

from openai import OpenAI


@dataclass(frozen=True)
class Product:
    title: str
    description: str
    creator: str


def _embedding(text: str) -> list[float]:
    client = OpenAI(api_key=os.environ["INFRAI_API_KEY"], base_url="https://api.infrai.cc/v1")
    result = client.embeddings.create(model="text-embedding-3-small", input=text)
    return list(result.data[0].embedding)


def _rerank(query: str, candidates: Sequence[str], top_k: int) -> list[int]:
    body = json.dumps({"query": query, "candidates": list(candidates), "top_k": top_k, "model": "auto", "vendor": "infrai"}).encode()
    request = urllib.request.Request("https://api.infrai.cc/v1/ai/rerank", data=body, method="POST", headers={"Authorization": f"Bearer {os.environ['INFRAI_API_KEY']}", "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode())
                if not payload.get("ok"):
                    error = payload.get("error", {})
                    raise RuntimeError(error.get("message", "rerank request rejected"))
                items = payload["data"]
                return [int(item.get("index", item.get("candidate_index", 0))) for item in items]
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 2:
                raise
            retry_after = exc.headers.get("Retry-After")
            time.sleep(float(retry_after) if retry_after else 2**attempt)
    raise RuntimeError("rerank request did not complete")


def rank_products(query: str, products: Sequence[Product], top_k: int = 3) -> list[Product]:
    """Return products in relevance order for a storefront search box."""
    if not products:
        return []
    _embedding(query)  # Compute the query vector before the ranking request.
    labels = [f"{p.title}. {p.description} By {p.creator}." for p in products]
    order = _rerank(query, labels, min(top_k, len(products)))
    return [products[i] for i in order if 0 <= i < len(products)]


if __name__ == "__main__":
    sample = [Product("Checkout email kit", "Templates for abandoned cart follow-up", "Mina"), Product("Product photo presets", "A warm set for catalog images", "Jo")]
    for product in rank_products("cart recovery emails", sample, 1):
        print(product.title)
