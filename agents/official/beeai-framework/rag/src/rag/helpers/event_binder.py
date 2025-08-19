# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Dict, Optional

from beeai_framework.emitter import EventMeta


class EventBinder:
    """Binds start and end events by maintaining a registry of start events."""

    def __init__(self):
        self.start_events: Dict[str, str] = {}

    @staticmethod
    def get_event_id(meta: EventMeta) -> str:
        """Extract event ID from meta."""
        return meta.id

    def _get_trace_id(self, meta: EventMeta) -> str:
        """Get trace ID or fallback value if trace is None."""
        return meta.trace.id if meta.trace else "no_trace"

    def _create_event_key(self, path: str, meta: EventMeta) -> str:
        """Create a key for events dict: path + "_" + trace_id"""
        trace_id = self._get_trace_id(meta)
        return f"{path}_{trace_id}"

    def _get_start_path_from_end_path(self, end_path: str) -> str:
        """Convert end event path to start event path by replacing last part with 'start'."""
        parts = end_path.split(".")
        if parts:
            parts[-1] = "start"
        return ".".join(parts)

    def get_start_event_id(self, meta: EventMeta) -> Optional[str]:
        """Get start event ID by reconstructing the key from the provided meta."""
        start_path = self._get_start_path_from_end_path(meta.path)
        key = self._create_event_key(start_path, meta)
        return self.start_events.get(key)

    def set_start_event_id(self, meta: EventMeta) -> None:
        """Store start event ID with validation that path ends with '.start'."""
        if not meta.path.endswith(".start"):
            raise ValueError(f"Event path must end with '.start', got: {meta.path}")
        key = self._create_event_key(meta.path, meta)
        self.start_events[key] = meta.id

    def clear(self) -> None:
        """Clear all stored start events."""
        self.start_events.clear()

    def __len__(self) -> int:
        """Return number of stored start events."""
        return len(self.start_events)
