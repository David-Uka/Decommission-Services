# Decommission Services

A small, auditable CLI + GitHub Actions workflow for safely tearing down a
service: drain traffic, archive logs, snapshot the DB, deregister it, clean
up DNS and monitoring — in that order, with a dry-run-by-default safety
model and a JSON audit trail for every step.

This exists because "delete the service" is usually done by hand, under
time pressure, in a different order every time, with no record of what
happened. This tool makes it one command, in a fixed safe order, with
proof afterward.

## Why this shape

- **Inventory as allow-list.** `services.yaml` is the only place that says
  a service may be decommissioned. The CLI validates the name against it
  before anything runs — a typo or a service that isn't listed is rejected,
  not silently attempted.
- **Dry-run by default.** `decommission run <service>` without `--yes`
  never touches real infrastructure. It prints and logs exactly what would
  happen. `--yes` is the only way to go live.
- **Fail-fast pipeline.** If a step fails, later steps don't run. A
  half-torn-down service with a clear stop point is safer than one where
  every step "best-effort" continues past a failure.
- **Audit trail, not just console output.** Every step's outcome is
  appended to `audit.log` as JSON — service, step, status, dry-run flag,
  detail, timestamp. That's what you hand to an incident review.
- **Honest about what's real.** `drain_traffic` and `archive_logs` run
  actual `kubectl` commands. `snapshot_db`, `remove_from_service_registry`,
  `remove_dns`, and `clean_monitoring` are explicitly labeled mock adapter
  points (see `src/decommission/steps.py`) — this repo doesn't have a
  shared AWS/Datadog account to demo real calls against, so it says so
  instead of faking a working integration.

## Usage

```bash
pip install -e ".[dev]"

# see what's eligible
decommission list

# check one service is valid without running anything
decommission validate payments

# dry-run (default, safe)
decommission run payments

# real execution
decommission run payments --yes

# resume after a fixed failure, skipping steps that already succeeded
decommission run payments --yes --skip drain_traffic,archive_logs
```

## GitHub Actions

`workflow_dispatch`-only, two jobs:

1. `dry-run` — validates input, runs the pipeline in simulation mode,
   uploads the audit log as an artifact. No approval required (read-only).
2. `execute` — gated on the `production-decommission` GitHub Environment
   (configure a required reviewer in Settings → Environments). Only runs
   the real pipeline after that approval.

See [`docs/runbook.md`](docs/runbook.md) for the full operational runbook,
including what to do when a step fails mid-run and how to recover a
service decommissioned by mistake.

## Configuration

Copy [`examples/services.example.yaml`](examples/services.example.yaml) to
`services.yaml` and adjust for your services. No secrets live in this repo
— the real DNS/registry/monitoring/DB credentials this tool would need in
a live environment belong in the CI provider's encrypted secrets store or
an external secrets manager, injected as environment variables at run
time, never committed here.

## Development

```bash
make install   # pip install -e ".[dev]"
make lint      # ruff
make test      # pytest with coverage
```

## What this is not

Not a rollback tool — decommissioning is destructive by design. See the
runbook's recovery section for what "undo" actually looks like (manual,
using the audit log and the DB snapshot, not a button).
