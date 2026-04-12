import anyio

from backend.app.modules.providers.embeddings import HashEmbeddingProvider


def test_hash_embeddings_are_deterministic() -> None:
    provider = HashEmbeddingProvider(dimension=16)

    first = anyio.run(provider.embed_texts, ["transformer attention"])
    second = anyio.run(provider.embed_texts, ["transformer attention"])
    third = anyio.run(provider.embed_texts, ["convolution pooling"])

    assert first == second
    assert first != third
    assert len(first[0]) == 16
