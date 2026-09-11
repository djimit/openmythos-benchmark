"""One-way sanitized Federation snapshot; never a live control-plane adapter."""

from __future__ import annotations

import copy
import re

from worldlab.runtime.event_log import sha256

SECRET_KEY = re.compile(r"(secret|token|password|credential|api[_-]?key|private[_-]?key)", re.I)
SECRET_VALUE = re.compile(r"(sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|-----BEGIN [A-Z ]+PRIVATE KEY-----)")


def synthetic_mirror(snapshot: dict) -> dict:
    def sanitize(value: object) -> object:
        if isinstance(value, dict):
            return {str(key): sanitize(item) for key, item in value.items() if not SECRET_KEY.search(str(key))}
        if isinstance(value, list):
            return [sanitize(item) for item in value]
        if isinstance(value, str) and SECRET_VALUE.search(value):
            return "[REDACTED]"
        return copy.deepcopy(value)

    sanitized = sanitize(snapshot)
    assert isinstance(sanitized, dict)
    return {"schema": "djimit.federation.synthetic-mirror.v1", "source_hash": sha256(snapshot),
            "snapshot": sanitized, "read_only": True, "live_mutation": False}
