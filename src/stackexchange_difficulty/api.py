"""Opt-in Stack Exchange API smoke check."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests

from stackexchange_difficulty.provenance import utc_now_iso

STACK_EXCHANGE_API_INFO_URL = "https://api.stackexchange.com/2.3/info"


def run_api_smoke(
    *,
    site: str = "stackoverflow",
    live: bool = False,
    out: str | Path | None = None,
    http_get: Callable[..., Any] | None = None,
    timeout: int = 10,
) -> dict[str, Any]:
    if not live:
        raise ValueError("api-smoke requires --live to avoid accidental network access.")

    get = http_get or requests.get
    response = get(STACK_EXCHANGE_API_INFO_URL, params={"site": site}, timeout=timeout)
    payload = response.json() if getattr(response, "content", b"") else {}
    metadata = {
        "endpoint": STACK_EXCHANGE_API_INFO_URL,
        "site": site,
        "checked_at": utc_now_iso(),
        "api_version": "2.3",
        "http_status": response.status_code,
        "quota_max": payload.get("quota_max"),
        "quota_remaining": payload.get("quota_remaining"),
        "backoff": payload.get("backoff"),
    }
    if out is not None:
        target = Path(out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata
