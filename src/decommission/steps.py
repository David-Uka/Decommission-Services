"""Decommission steps.

Each step is a small, independently testable function with the signature
(service_name, dry_run) -> StepResult. Steps that talk to real
infrastructure (kubectl) execute for real. Steps that would talk to
systems this repo doesn't own a live account for (DNS provider, service
registry, monitoring, DB snapshot target) are explicit, clearly-labeled
adapter points — mocked here, meant to be swapped for a real API/CLI call
per environment. That boundary is intentional, not an oversight: faking a
Route53/Datadog integration would be dishonest about what this tool
actually does today.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class StepResult:
    step: str
    ok: bool
    detail: str


def _run(cmd: list, dry_run: bool) -> StepResult:
    step = cmd[0] if cmd else "unknown"
    if dry_run:
        return StepResult(step=step, ok=True, detail=f"DRY-RUN: would run: {' '.join(cmd)}")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError as e:
        return StepResult(step=step, ok=False, detail=f"command not found: {e}")
    except subprocess.TimeoutExpired:
        return StepResult(step=step, ok=False, detail="command timed out after 60s")
    if proc.returncode != 0:
        return StepResult(step=step, ok=False, detail=proc.stderr.strip() or proc.stdout.strip())
    return StepResult(step=step, ok=True, detail=proc.stdout.strip())


def drain_traffic(service: str, dry_run: bool) -> StepResult:
    """Scale the deployment to 0 and remove the Service. Real kubectl calls."""
    r1 = _run(["kubectl", "scale", "deployment", service, "--replicas=0", "-n", service], dry_run)
    if not r1.ok:
        return StepResult("drain_traffic", False, r1.detail)
    r2 = _run(["kubectl", "delete", "svc", service, "-n", service, "--ignore-not-found=true"], dry_run)
    return StepResult("drain_traffic", r2.ok, r2.detail)


def snapshot_db(service: str, dry_run: bool) -> StepResult:
    """MOCK ADAPTER POINT: wire to pg_dump/mysqldump or a snapshot API."""
    if dry_run:
        return StepResult("snapshot_db", True, f"DRY-RUN: would snapshot DB for {service}")
    # Real implementation goes here, e.g.:
    #   pg_dump -h <host> -U <user> f"{service}_db" > f"/tmp/{service}_db.sql"
    return StepResult("snapshot_db", True, f"MOCK: snapshot recorded for {service} (no real DB wired)")


def archive_logs(service: str, dry_run: bool) -> StepResult:
    """Pull recent container logs via kubectl before the namespace disappears."""
    dest = f"/tmp/decommission-archives/{service}/logs.txt"
    if dry_run:
        return StepResult("archive_logs", True, f"DRY-RUN: would archive logs to {dest}")
    import os
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    r = _run(["kubectl", "logs", "--all-containers=true", "-n", service], dry_run)
    if r.ok:
        with open(dest, "w", encoding="utf-8") as f:
            f.write(r.detail)
        return StepResult("archive_logs", True, f"archived to {dest}")
    return StepResult("archive_logs", False, r.detail)


def remove_from_service_registry(service: str, dry_run: bool) -> StepResult:
    """MOCK ADAPTER POINT: wire to your service-discovery/API-gateway API."""
    if dry_run:
        return StepResult("remove_from_service_registry", True, f"DRY-RUN: would deregister {service}")
    return StepResult("remove_from_service_registry", True, f"MOCK: {service} deregistered (no real registry wired)")


def remove_dns(service: str, dry_run: bool) -> StepResult:
    """MOCK ADAPTER POINT: wire to Route53 / your DNS provider's API."""
    if dry_run:
        return StepResult("remove_dns", True, f"DRY-RUN: would delete DNS record for {service}")
    return StepResult("remove_dns", True, f"MOCK: DNS record removed for {service} (no real DNS provider wired)")


def clean_monitoring(service: str, dry_run: bool) -> StepResult:
    """MOCK ADAPTER POINT: wire to Datadog/Prometheus Alertmanager silences API."""
    if dry_run:
        return StepResult("clean_monitoring", True, f"DRY-RUN: would remove monitors for {service}")
    return StepResult("clean_monitoring", True, f"MOCK: monitors removed for {service} (no real monitoring API wired)")


# Order matters: drain before archiving/snapshotting nothing-left-to-read,
# and registry/DNS/monitoring cleanup happens only after traffic is safely
# drained and evidence (logs, DB snapshot) is captured.
PIPELINE = [
    drain_traffic,
    archive_logs,
    snapshot_db,
    remove_from_service_registry,
    remove_dns,
    clean_monitoring,
]
