"""Provenance helpers for corpus runs."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    """Return an ISO timestamp suitable for provenance metadata."""
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_run_metadata(
    command: str,
    inputs: dict[str, str],
    outputs: dict[str, str],
) -> dict[str, Any]:
    return {
        "command": command,
        "created_at": utc_now_iso(),
        "inputs": inputs,
        "outputs": outputs,
    }


def load_provenance(path: str | Path) -> dict[str, Any]:
    """Load JSON or a small YAML subset used by the project templates."""
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".json":
        return json.loads(text)
    return _load_simple_yaml(text)


def _load_simple_yaml(text: str) -> dict[str, Any]:
    """Parse simple key/value YAML without requiring PyYAML at runtime.

    This parser covers the repository templates: scalar keys, quoted strings,
    and top-level lists. It deliberately does not try to implement full YAML.
    """
    data: dict[str, Any] = {}
    current_list_key: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- ") and current_list_key:
            data.setdefault(current_list_key, []).append(_clean_scalar(line[2:]))
            continue
        current_list_key = None
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            data[key] = {}
            continue
        if value == "[]":
            data[key] = []
            current_list_key = key
        else:
            data[key] = _clean_scalar(value)
    return data


def _clean_scalar(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value
