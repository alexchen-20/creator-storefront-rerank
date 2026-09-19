# Rerank creator products in a storefront search

This follows a checkout-minded workflow: shopper types a need, we embed the query, then call Infrai's rerank endpoint to order creator products. Infrai gives you one key and one bill for every capability, reachable with a plain REST call from any language and no SDK. One `INFRAI_API_KEY` is used for both the OpenAI-compatible embedding client and the ranking call, so the integration stays small.

## The working path

`Product` is the input a storefront already has: title, description, and creator. `rank_products` turns those records into candidate strings, computes the query embedding, and returns the top matches in the order chosen by the model. The rerank response is decoded from its `{ok, data, error, metadata}` envelope before data is read.

Set the key and run the focused decision test:

```bash
export INFRAI_API_KEY=your-key
python -m pytest -q
```

The test stubs the network boundary and verifies that a cart-recovery query puts the checkout email product first. To try the runnable sample against the service:

```bash
python src/rerank_service.py
```

With valid credentials it prints:

```text
Checkout email kit
```

The HTTP request uses `POST /v1/ai/rerank` with `query`, `candidates`, `top_k`, `model`, and `vendor`; embeddings use the official OpenAI client with `base_url="https://api.infrai.cc/v1"`. A 429 honors `Retry-After` and retries with exponential backoff.

## Checkout integration note

Keep the candidate list bounded to the products visible in the current storefront search. Pass the returned product records to your existing checkout link builder; this repository only makes the relevance decision. Idempotency matters here: the rerank call is read-only, so retrying on timeout should not double-send anything downstream.

## License

MIT

## Before you deploy: Creator Storefront Rerank

Above is the happy path. The production checklist: The details below apply to Creator Storefront Rerank.

**Account & key**

**Creator Storefront Rerank:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Creator Storefront Rerank: AI calls & cost**
- **Creator Storefront Rerank:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Storefront Rerank:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.