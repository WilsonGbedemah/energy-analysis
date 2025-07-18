from unittest import mock

from src import pipeline


def test_run_step_success(capfd):
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        pipeline.run_step("Test Step", "echo test")
        out, _ = capfd.readouterr()
        assert "✅ Test Step completed" in out


def test_run_step_failure(capfd):
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        pipeline.run_step("Fail Step", "false")
        out, _ = capfd.readouterr()
        assert "❌ Fail Step failed." in out


def test_is_dashboard_running_true():
    with mock.patch("subprocess.check_output") as mock_check:
        mock_check.return_value = b"streamlit.exe"
        assert pipeline.is_dashboard_running() is True


def test_is_dashboard_running_false():
    with mock.patch("subprocess.check_output") as mock_check:
        mock_check.return_value = b"python.exe"
        assert pipeline.is_dashboard_running() is False


def test_is_dashboard_running_exception():
    with mock.patch("subprocess.check_output", side_effect=Exception("fail")):
        assert pipeline.is_dashboard_running() is False
