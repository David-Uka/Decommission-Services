import json
from pathlib import Path

from decommission.cli import main


def make_inventory(tmp_path: Path) -> Path:
    p = tmp_path / "services.yaml"
    p.write_text("- name: payments\n  owner: team-pay\n  tier: critical\n")
    return p


def test_list_command(tmp_path, capsys):
    inv = make_inventory(tmp_path)
    rc = main(["--inventory", str(inv), "list"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "payments" in out


def test_validate_unknown_service_fails(tmp_path):
    inv = make_inventory(tmp_path)
    rc = main(["--inventory", str(inv), "validate", "ghost-service"])
    assert rc == 1


def test_run_defaults_to_dry_run_and_writes_audit_log(tmp_path):
    inv = make_inventory(tmp_path)
    audit = tmp_path / "audit.log"
    rc = main(["--inventory", str(inv), "--audit-log", str(audit), "run", "payments"])
    assert rc == 0
    lines = audit.read_text().strip().splitlines()
    assert len(lines) == 6  # one per pipeline step
    for line in lines:
        event = json.loads(line)
        assert event["dry_run"] is True
        assert event["status"] == "ok"


def test_run_rejects_unknown_service_before_any_step(tmp_path):
    inv = make_inventory(tmp_path)
    audit = tmp_path / "audit.log"
    rc = main(["--inventory", str(inv), "--audit-log", str(audit), "run", "not-real"])
    assert rc == 1
    assert not audit.exists()


def test_run_skip_flag_marks_steps_skipped(tmp_path):
    inv = make_inventory(tmp_path)
    audit = tmp_path / "audit.log"
    rc = main([
        "--inventory", str(inv), "--audit-log", str(audit),
        "run", "payments", "--skip", "snapshot_db,clean_monitoring",
    ])
    assert rc == 0
    lines = audit.read_text().strip().splitlines()
    events = [json.loads(line) for line in lines]
    skipped = {e["step"] for e in events if e["status"] == "skipped"}
    assert skipped == {"snapshot_db", "clean_monitoring"}


def test_inventory_flag_before_subcommand_is_not_lost(tmp_path, capsys):
    # Regression test: argparse's subparser dispatch re-parses into a fresh
    # namespace and can silently overwrite parent-level flags with the
    # subparser's own defaults if not guarded with SUPPRESS. This asserts
    # a --inventory given *before* the subcommand actually takes effect.
    inv = make_inventory(tmp_path)
    rc = main(["--inventory", str(inv), "list"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "payments" in out
