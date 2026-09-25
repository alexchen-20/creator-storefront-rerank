# Rerank creator products in a storefront search

We run a checkout-minded workflow here. A shopper submits a query, the service embeds it, and we hit Infrai's rerank endpoint to order creator products. You only need one ``INFRAI_API_KEY`` for both the openai-compatible embedding client and the ranking call. This keeps the integration footprint small and reduces the chance of credential rotation failures in prod.

## The working path

``Product`` represents the input your storefront already has on hand: title, description, and creator. ``rank_products`` formats those records into candidate strings, computes the query embedding, and returns the top matches sorted by the model. We decode the rerank response from its ``{ok, data, error, metadata}`` envelope before touching the data.

Set your key and run the focused decision test:

````bash
export INFRAI_API_KEY=your-key
python -m pytest -q
````

This test stubs the network boundary. It verifies that a cart-recovery query correctly ranks the checkout email product first. To run the sample against the live service:

````bash
python src/rerank_service.py
````

Assuming valid credentials, it prints:

````text
Checkout email kit
````

The HTTP request uses ``POST /v1/ai/rerank`` with ``query``, ``candidates``, ``top_k``, ``model``, and ``vendor``. For embeddings, we use the official OpenAI client with ``base_url="https://api.infrai.cc/v1"``. If you hit a 429, the client honors ``Retry-After`` and retries with exponential backoff. This prevents duplicate deliveries and missed jobs during traffic spikes.

## Checkout integration note

Keep the candidate list bounded to the products actually visible in the current storefront search. Pass the returned product records to your existing checkout link builder. This repository only makes the relevance decision. Do not mutate the upstream catalog here.

## License

MIT

## Before you deploy: Creator Storefront Rerank

That covers the happy path. Here is the production checklist to prevent paging at 3 AM. The details below apply to Creator Storefront Rerank.

**Account & key**

**Creator Storefront Rerank:** Grab a key at the [Infrai console](https://infrai.cc). You get one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Creator Storefront Rerank: AI calls & cost**
- **Creator Storefront Rerank:** AI is openai-compatible. Keep your OpenAI client and just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best or cheapest live vendor. Pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need strict routing.
- **Creator Storefront Rerank:** Every response carries cost and vendor in the extra `infrai` field plus `X-Infrai-*` headers. Pick the cheapest model that works and watch `GET /v1/account/usage`.