from src.rerank_service import Product, rank_products


def test_storefront_search_uses_rerank_order(monkeypatch):
    products = [
        Product("Photo presets", "Catalog image edits", "Jo"),
        Product("Checkout email kit", "Abandoned cart follow-up templates", "Mina"),
    ]
    monkeypatch.setattr("src.rerank_service._embedding", lambda text: [0.1, 0.2])
    monkeypatch.setattr("src.rerank_service._rerank", lambda query, candidates, top_k: [1, 0])
    ranked = rank_products("cart recovery emails", products, 2)
    assert [item.title for item in ranked] == ["Checkout email kit", "Photo presets"]
