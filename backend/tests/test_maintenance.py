from backend.app.modules.maintenance.service import EmbeddingMaintenanceService


def test_embedding_is_stale_when_dimension_mismatches() -> None:
    assert EmbeddingMaintenanceService._is_stale_embedding([0.0] * 8, expected_dimension=256) is True


def test_embedding_is_not_stale_when_dimension_matches() -> None:
    assert EmbeddingMaintenanceService._is_stale_embedding([0.0] * 256, expected_dimension=256) is False


def test_embedding_is_stale_when_non_finite() -> None:
    assert EmbeddingMaintenanceService._is_stale_embedding([0.0, float("inf")], expected_dimension=2) is True
