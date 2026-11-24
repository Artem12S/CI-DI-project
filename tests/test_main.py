import logging
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

import main as cli
from errors import ProjectToolError
from pytest_runner import CheckError


@pytest.fixture
def command(monkeypatch):
    monkeypatch.setattr(sys, "argv", [
        "main.py", "check", "--only", "tests", "--project", "web app",
        "--python", "env/bin/python", "--log-file", "check.log",
        "--test-timeout", "15",
    ])
    configure = Mock(return_value=Path("check.log"))
    runner = Mock()
    monkeypatch.setattr(cli, "configure_log", configure)
    monkeypatch.setattr(cli, "run_tests", runner)
    return configure, runner


def test_success_forwards_arguments(command, caplog):
    configure, runner = command
    with caplog.at_level(logging.INFO):
        assert cli.main() == 0
    configure.assert_called_once_with(Path("check.log"))
    runner.assert_called_once_with(Path("web app"), Path("env/bin/python"), 15)
    assert "Тесты прошли" in caplog.text


@pytest.mark.parametrize(("error", "code", "message"), [
    (CheckError("Тесты не найдены"), 1, "Тесты не найдены"),
    (ProjectToolError("Ошибка другого модуля"), 1, "Ошибка другого модуля"),
    (KeyboardInterrupt(), 130, "Проверка прервана пользователем"),
])
def test_runner_failure_is_reported(command, caplog, error, code, message):
    _, runner = command
    runner.side_effect = error
    assert cli.main() == code
    assert message in caplog.text
    assert sum(message in record.message for record in caplog.records) == 1


def test_log_error_stops_check(command, capsys):
    configure, runner = command
    configure.side_effect = OSError("каталог недоступен")
    assert cli.main() == 1
    runner.assert_not_called()
    assert "Не удалось открыть журнал" in capsys.readouterr().err


def test_invalid_timeout_stops_before_setup(command, monkeypatch, capsys):
    configure, runner = command
    monkeypatch.setattr(sys, "argv", [*sys.argv[:-1], "0"])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
    assert "--test-timeout должен быть положительным" in capsys.readouterr().err
    configure.assert_not_called()
    runner.assert_not_called()


def test_default_settings_use_current_project_and_python(
    command, monkeypatch, tmp_path,
):
    configure, runner = command
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["main.py", "check", "--only", "tests"])

    assert cli.main() == 0

    configure.assert_called_once_with(None)
    runner.assert_called_once_with(tmp_path, Path(sys.executable), 300)


@pytest.mark.parametrize("arguments", [
    ["--help"],
    ["check", "--help"],
])
def test_help_finishes_without_setup(command, monkeypatch, capsys, arguments):
    configure, runner = command
    monkeypatch.setattr(sys, "argv", ["main.py", *arguments])

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 0
    assert "--help" in capsys.readouterr().out
    configure.assert_not_called()
    runner.assert_not_called()


def test_unexpected_error_is_reported_without_traceback(command, capsys):
    _, runner = command
    failure = RuntimeError("Сбой реализации шага")
    runner.side_effect = failure

    assert cli.main() == 1
    output = capsys.readouterr().err
    assert "Непредвиденная ошибка" in output
    assert "check.log" in output
    assert str(failure) not in output
    assert "Traceback" not in output


@pytest.mark.parametrize("stage", ["parse_arguments", "configure_log"])
@pytest.mark.parametrize(("error", "code", "message"), [
    (RuntimeError("сбой подготовки"), 1, "Не удалось подготовить"),
    (KeyboardInterrupt(), 130, "Выполнение прервано"),
])
def test_preparation_errors_are_handled(
    command, monkeypatch, capsys, stage, error, code, message,
):
    monkeypatch.setattr(cli, stage, Mock(side_effect=error))
    assert cli.main() == code
    output = capsys.readouterr().err
    assert message in output
    assert "Traceback" not in output
    command[1].assert_not_called()
