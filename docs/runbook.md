# Decommission runbook

## Triggering a decommission

1. Go to **Actions → Decommission Service → Run workflow**.
2. Enter `service_name` and re-type it in `confirm` (must match exactly).
3. The `dry-run` job runs immediately, no approval needed:
   - validates the service is in `services.yaml`
   - runs the full pipeline in dry-run mode (no real changes)
   - uploads `dry-run-audit-log` as a build artifact — read it before approving.
4. The `execute` job is gated on the `production-decommission` GitHub
   Environment. Configure that environment with at least one required
   reviewer (Settings → Environments). Nothing destructive runs without
   that approval.
5. On approval, `execute` re-runs the same pipeline with `--yes`, this time
   for real, and uploads `execution-audit-log`.

## What "decommission" actually does

Pipeline order (fail-fast — first failing step halts the rest):

1. `drain_traffic` — scales the deployment to 0 replicas and deletes the
   Service in the service's namespace. **Real kubectl calls.**
2. `archive_logs` — pulls all container logs from the namespace before
   they're gone. **Real kubectl call.**
3. `snapshot_db` — mock adapter point. Wire to `pg_dump`/`mysqldump` or your
   snapshot API for your environment.
4. `remove_from_service_registry` — mock adapter point. Wire to your
   service discovery / API gateway.
5. `remove_dns` — mock adapter point. Wire to Route53 or your DNS provider.
6. `clean_monitoring` — mock adapter point. Wire to Datadog/Alertmanager.

Steps 3–6 are intentionally mocked in this repo (no shared cloud account to
demo against) — see the module docstring in `src/decommission/steps.py` for
exactly where to plug in real calls.

## If a step fails mid-run

- The run **halts immediately** — steps after the failure never execute.
  A failure in `remove_from_service_registry`, for example, means DNS and
  monitoring cleanup did **not** run; the service is drained and archived
  but still has live DNS/monitoring. That's deliberate: partial teardown
  should be visible and paused, not silently completed with a hole in it.
- Read `audit.log` (or the `execution-audit-log` artifact) — every step's
  status and detail is one JSON line.
- Fix the underlying issue, then re-run with `--skip` for the steps that
  already succeeded:
  ```
  decommission run payments --yes --skip drain_traffic,archive_logs
  ```

## Recovering a service decommissioned by mistake

This tool does not attempt automatic rollback — undoing a decommission is
an infra-restore operation, not a workflow re-run. To recover:

1. Check `audit.log` / the uploaded artifact for exactly which steps ran.
2. Re-apply the service's Deployment/Service manifests (GitOps: revert the
   ArgoCD app or delete-and-let-it-reconcile from `gitops-manifests`).
3. Restore DNS record and re-register in the service registry manually
   (these are the mock steps — nothing was actually removed from a real
   DNS/registry provider yet in this repo's current state).
4. Restore from the DB snapshot taken in step 3, if the DB was actually
   dropped elsewhere as part of a fuller decommission.
5. Re-add monitors.

The `snapshot_db` step exists specifically so step 4 above is possible —
never skip it to "save time."
