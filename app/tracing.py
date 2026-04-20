from __future__ import annotations

import os
from typing import Any

try:
    from langfuse import observe, get_client

    class _LangfuseContext:
        """Adapter wrapping langfuse v3 get_client() to match the interface
        expected by agent.py (update_current_trace / update_current_observation)."""

        def update_current_trace(self, **kwargs: Any) -> None:
            try:
                client = get_client()
                client.update_current_trace(**kwargs)
            except Exception:
                pass

        def update_current_observation(self, **kwargs: Any) -> None:
            try:
                client = get_client()
                # v3 update_current_span doesn't support usage_details,
                # merge it into metadata instead
                usage = kwargs.pop("usage_details", None)
                meta = kwargs.get("metadata", {}) or {}
                if usage:
                    meta["usage"] = usage
                    kwargs["metadata"] = meta
                client.update_current_span(**kwargs)
            except Exception:
                pass

    langfuse_context = _LangfuseContext()

except Exception:  # pragma: no cover
    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator

    class _DummyContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_observation(self, **kwargs: Any) -> None:
            return None

    langfuse_context = _DummyContext()


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
