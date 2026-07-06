"""Append-only JSON-lines audit trail.

Every step of every run — success or failure, dry-run or real — gets one
line. This is the artifact you hand to an incident review or a compliance
ask six months later: "prove what was torn down, when, by what, and whether
it actually executed or was a dry run."
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class AuditEvent:
    ts: float
    service: str
    step: str
    status: str  # "ok" | "failed" | "skipped"
    dry_run: bool
    detail: str = ""


class AuditLog:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, service: str, step: str, status: str, dry_run: bool, detail: str = "") -> None:
        event = AuditEvent(
            ts=time.time(),
            service=service,
            step=step,
            status=status,
            dry_run=dry_run,
            detail=detail,
        )
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event)) + "\n")
