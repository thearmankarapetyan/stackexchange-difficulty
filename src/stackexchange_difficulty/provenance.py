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


def write_provenance_json(record: dict[str, Any], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def finalize_processed_hashes(
    record: dict[str, Any],
    hash_manifest: str | Path,
) -> dict[str, Any]:
    digest = f"sha256:{sha256_file(hash_manifest)}"
    finalized = dict(record)
    finalized["processed_hash_manifest"] = str(hash_manifest)
    finalized["processed_output_hash"] = digest
    finalized["output_hash"] = digest
    return finalized


def _load_simple_yaml(text: str) -> dict[str, Any]:
    """Parse simple key/value YAML without requiring PyYAML at runtime.

    This parser covers the repository templates: scalar keys, quoted strings,
    top-level lists, and one-level nested mappings. It deliberately does not
    try to implement full YAML.
    """
    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        is_nested = raw_line[:1].isspace()
        if is_nested and current_key:
            if stripped.startswith("- "):
                if not isinstance(data.get(current_key), list):
                    data[current_key] = []
                data[current_key].append(_clean_scalar(stripped[2:]))
                continue
            if ":" in stripped:
                if not isinstance(data.get(current_key), dict):
                    data[current_key] = {}
                nested_key, nested_value = stripped.split(":", 1)
                nested_key = nested_key.strip()
                nested_value = nested_value.strip()
                data[current_key][nested_key] = (
                    _clean_scalar(nested_value) if nested_value else {}
                )
                continue

        current_key = None
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            data[key] = None
            current_key = key
            continue
        if value == "[]":
            data[key] = []
        else:
            data[key] = _clean_scalar(value)
    return data


def _clean_scalar(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value
