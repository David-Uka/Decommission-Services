"""Command-line entry point.

    decommission list
    decommission validate <service>
    decommission run <service> [--yes] [--skip step1,step2]

Safety model:
  - dry-run is the default for `run`. Nothing destructive happens unless
    --yes is passed explicitly.
  - the service must exist in services.yaml (the inventory is the
    allow-list); anything else is rejected before any step runs.
  - the pipeline is fail-fast: the first failing step stops the run and is
    recorded in the audit log, so a half-decommissioned service doesn't
    silently continue through DNS/monitoring cleanup.
  - every step outcome (ok/failed, dry-run or real) is appended to
    audit.log as JSON lines.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import steps
from .audit import AuditLog
from .inventory import InventoryError, find_service, load_inventory

DEFAULT_INVENTORY = Path("services.yaml")
DEFAULT_AUDIT_LOG = Path("audit.log")


def cmd_list(args: argparse.Namespace) -> int:
    try:
        records = load_inventory(args.inventory)
    except InventoryError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for r in records:
        print(f"{r.name:<24} owner={r.owner:<16} tier={r.tier}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        records = load_inventory(args.inventory)
        svc = find_service(records, args.service)
    except InventoryError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"'{svc.name}' is a valid decommission target (owner={svc.owner}, tier={svc.tier})")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    try:
        records = load_inventory(args.inventory)
        svc = find_service(records, args.service)
    except InventoryError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    dry_run = not args.yes
    skip = set(args.skip.split(",")) if args.skip else set()
    audit = AuditLog(args.audit_log)

    mode = "DRY-RUN" if dry_run else "LIVE"
    print(f"[{mode}] decommissioning '{svc.name}' (owner={svc.owner}, tier={svc.tier})")

    for step_fn in steps.PIPELINE:
        name = step_fn.__name__
        if name in skip:
            print(f"  - {name}: SKIPPED (explicit --skip)")
            audit.record(svc.name, name, "skipped", dry_run)
            continue

        result = step_fn(svc.name, dry_run)
        status = "ok" if result.ok else "failed"
        print(f"  - {name}: {status.upper()} — {result.detail}")
        audit.record(svc.name, name, status, dry_run, result.detail)

        if not result.ok:
            print(
                f"\nHalting: '{name}' failed. No further steps ran. "
                f"See {args.audit_log} for the full trail before retrying.",
                file=sys.stderr,
            )
            return 1

    print(f"\n'{svc.name}' decommission {'simulated' if dry_run else 'complete'}. "
          f"Audit trail: {args.audit_log}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    # Shared flags (--inventory/--audit-log) are defined on a parent parser
    # and attached to *every* subcommand, so they can be passed either
    # before or after the subcommand name:
    #   decommission --inventory x.yaml run payments
    #   decommission run payments --inventory x.yaml
    # A single top-level-only definition would only allow the first form,
    # which is not how most people type CLI flags.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY,
                         help="path to services.yaml (default: ./services.yaml)")
    common.add_argument("--audit-log", type=Path, default=DEFAULT_AUDIT_LOG,
                         help="path to audit log (default: ./audit.log)")

    # A second copy with default=SUPPRESS, attached to each subparser. If we
    # reused `common` on both the top parser and every subparser, argparse's
    # subparser dispatch re-parses from a *fresh* namespace and then copies
    # every attribute onto the shared namespace — including untouched
    # defaults — silently clobbering an --inventory/--audit-log given before
    # the subcommand. SUPPRESS means "only set this if the user actually
    # typed it here," so a flag given before the subcommand survives, and
    # one given after it can still override.
    common_override = argparse.ArgumentParser(add_help=False)
    common_override.add_argument("--inventory", type=Path, default=argparse.SUPPRESS)
    common_override.add_argument("--audit-log", type=Path, default=argparse.SUPPRESS)

    p = argparse.ArgumentParser(prog="decommission", parents=[common])
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list", parents=[common_override],
                    help="list services eligible for decommission").set_defaults(func=cmd_list)

    p_validate = sub.add_parser("validate", parents=[common_override],
                                 help="check a service exists in the inventory")
    p_validate.add_argument("service")
    p_validate.set_defaults(func=cmd_validate)

    p_run = sub.add_parser("run", parents=[common_override],
                            help="run the decommission pipeline for a service")
    p_run.add_argument("service")
    p_run.add_argument("--yes", action="store_true", help="execute for real (default is dry-run)")
    p_run.add_argument("--skip", help="comma-separated step function names to skip")
    p_run.set_defaults(func=cmd_run)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
