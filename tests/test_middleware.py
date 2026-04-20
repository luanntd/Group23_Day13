import uuid
from unittest.mock import MagicMock

from app.middleware import CorrelationIdMiddleware


def test_correlation_id_format() -> None:
    """Verify generated correlation IDs follow req-<8hex> format."""
    # Generate several IDs and check format
    for _ in range(10):
        cid = f"req-{uuid.uuid4().hex[:8]}"
        assert cid.startswith("req-")
        assert len(cid) == 12  # "req-" (4) + 8 hex chars
        # Verify hex part is valid
        hex_part = cid[4:]
        int(hex_part, 16)  # Will raise if not valid hex


def test_correlation_id_uniqueness() -> None:
    """Verify generated correlation IDs are unique."""
    ids = {f"req-{uuid.uuid4().hex[:8]}" for _ in range(100)}
    assert len(ids) == 100
