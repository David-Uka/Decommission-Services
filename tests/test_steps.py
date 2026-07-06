from unittest.mock import patch, MagicMock

from decommission import steps


def test_dry_run_never_calls_subprocess():
    with patch("decommission.steps.subprocess.run") as mock_run:
        result = steps.drain_traffic("payments", dry_run=True)
        mock_run.assert_not_called()
        assert result.ok
        assert "DRY-RUN" in result.detail


def test_drain_traffic_real_success():
    fake = MagicMock(returncode=0, stdout="scaled", stderr="")
    with patch("decommission.steps.subprocess.run", return_value=fake) as mock_run:
        result = steps.drain_traffic("payments", dry_run=False)
        assert result.ok
        assert mock_run.call_count == 2  # scale + delete svc


def test_drain_traffic_real_failure_halts_with_detail():
    fake = MagicMock(returncode=1, stdout="", stderr="deployment not found")
    with patch("decommission.steps.subprocess.run", return_value=fake):
        result = steps.drain_traffic("payments", dry_run=False)
        assert not result.ok
        assert "deployment not found" in result.detail


def test_mock_adapter_steps_are_labeled_as_mock():
    result = steps.remove_dns("payments", dry_run=False)
    assert result.ok
    assert "MOCK" in result.detail


def test_pipeline_order_is_drain_first_and_monitoring_last():
    names = [f.__name__ for f in steps.PIPELINE]
    assert names[0] == "drain_traffic"
    assert names[-1] == "clean_monitoring"
