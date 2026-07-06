# Decommission-Services

A runbook-as-code pipeline for retiring a service safely: one `workflow_dispatch`
trigger walks it through inventory validation, traffic drain, backups, cleanup,
and infra teardown — instead of a human running seven commands by hand in the
wrong order at 4pm on a Friday.

## Why this exists

Decommissioning is rare enough that nobody remembers the steps, and risky
enough that skipping one (forgetting a DB snapshot, leaving a stale DNS
record, leaving a service authorized in the registry) causes real incidents.
This repo encodes the runbook as a versioned, reviewable pipeline instead of
tribal knowledge in someone's head or a wiki page nobody updates.

## How it's triggered

GitHub Actions `workflow_dispatch` on `.github/workflows/Decommission.yml`,
with one required input: `service_name`.

```
gh workflow run Decommission.yml -f service_name=payments
```

## Pipeline order

```
validate
  └─ check_inventory.sh      # refuse to run against anything not in services.yaml
       │
       ▼  (requires manual approval — see "Approval gate" below)
k8s-cleanup                          terraform-destroy
  ├─ drain_traffic.sh                  ├─ skip if no infra/services/<name> stack
  ├─ archive_logs.sh                   └─ terraform destroy (if present)
  ├─ snapshot_db.sh
  ├─ remove_from_service_registry.sh
  ├─ remove_dns.sh
  └─ clean_monitoring.sh
       │                                    │
       └──────────────┬─────────────────────┘
                       ▼
                    notify
```

`k8s-cleanup` and `terraform-destroy` run in parallel once `validate` passes
— there's no ordering dependency between draining Kubernetes traffic and
tearing down the Terraform-managed infra for the same service, so there's no
reason to serialize them.

## Approval gate

Both destructive jobs (`k8s-cleanup`, `terraform-destroy`) run under the
`decommission-approval` GitHub Environment. A workflow condition alone can't
provide a real manual gate — GitHub Environments with **required reviewers**
can. Configure that environment once in *Settings > Environments* and every
run will pause for sign-off before anything destructive executes. (Until
that environment is configured, GitHub runs the jobs immediately with no
gate — set it up before pointing this at anything real.)

## What's real vs. mocked

| Script | Status |
|---|---|
| `check_inventory.sh` | Real — parses `services.yaml`, hard fails on no match |
| `drain_traffic.sh` | Real — `kubectl scale` + `kubectl delete svc` |
| `archive_logs.sh` | Real — `kubectl logs`, writes to `/tmp/archives/<service>`. S3 upload is commented out; set `BACKUP_BUCKET` and uncomment to enable |
| `snapshot_db.sh` | **Mocked** — placeholder, wire up `pg_dump`/`mysqldump`/your backup API before relying on it |
| `remove_from_service_registry.sh` | **Mocked** — placeholder for your service discovery API |
| `remove_dns.sh` | **Mocked** — placeholder for Route53/your DNS provider |
| `clean_monitoring.sh` | **Mocked** — placeholder for Datadog/your observability stack |
| `terraform-destroy` job | Real, but **skips gracefully** if `infra/services/<service_name>/` doesn't exist in this repo |

This repo ships as a template/reference pipeline, not wired to a specific
company's live registry/DNS/monitoring stack — the mocked steps are exactly
where you plug that in.

## services.yaml

The inventory allow-list. Only services listed here can be targeted —
`check_inventory.sh` does an exact-match check (not a loose substring match)
against this file and hard-fails otherwise. This is the main guard against
someone fat-fingering a production service name into the workflow input.

## Local testing

Every script validates its argument and can be run directly:

```bash
./scripts/check_inventory.sh payments   # passes
./scripts/check_inventory.sh nope       # fails: not in inventory
./scripts/check_inventory.sh            # fails: missing argument
```

The mocked scripts (`snapshot_db.sh`, `remove_from_service_registry.sh`,
`remove_dns.sh`, `clean_monitoring.sh`) run standalone with no cluster or
credentials needed. `drain_traffic.sh` and `archive_logs.sh` need a
reachable `kubectl` context.

## CI

`.github/workflows/lint.yml` runs ShellCheck against every script on push/PR.

`.github/workflows/fix-script-permissions.yml` is a manual fallback that re-applies `+x` to `scripts/*.sh` and commits — useful if a script ever loses its executable bit (e.g. edited via the GitHub web UI).
