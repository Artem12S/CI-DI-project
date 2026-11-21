import logging
from pathlib import Path
from unittest.mock import Mock

import pytest

from errors import ProjectToolError
import pipeline
from pytest_runner import CheckError


def test_step_returns_result_and_forwards_arguments(caplog, monkeypatch):
    result = Path("release.tar.gz")
    action = Mock(return_value=result)
    monkeypatch.setattr(pipeline, "monotonic", Mock(side_effect=[10, 12.5]))

    with caplog.at_level(logging.INFO):
        actual = pipeline.run_step(
            "Архивирование", action, Path("project"), output=result
        )

    assert actual is result
    action.assert_called_once_with(Path("project"), output=result)
    assert caplog.messages == [
        "Запуск Архивирование",
        "Шаг Архивирование выполнен за 2.5 с",
    ]


@pytest.mark.parametrize("error", [
    ProjectToolError("Ошибка конфигурации"),
    CheckError("Тесты не найдены"),
    ValueError("Неожиданная ошибка"),
    KeyboardInterrupt(),
])
def test_failed_step_preserves_exception_and_stops_sequence(
    error, caplog, monkeypatch,
):
    action = Mock(side_effect=error)
    next_action = Mock()
    monkeypatch.setattr(pipeline, "monotonic", Mock(side_effect=[10, 13]))

    with caplog.at_level(logging.INFO), pytest.raises(type(error)) as raised:
        pipeline.run_step("Проверка", action)
        pipeline.run_step("Отправка", next_action)

    assert raised.value is error
    action.assert_called_once_with()
    next_action.assert_not_called()
    assert len(caplog.records) == 2
    assert caplog.records[0].message == "Запуск Проверка"
    assert "3.0 с" in caplog.records[1].message
    if isinstance(error, KeyboardInterrupt):
        assert caplog.records[1].levelno == logging.WARNING
        assert "прервана пользователем" in caplog.records[1].message
    else:
        assert caplog.records[1].levelno == logging.ERROR
        assert str(error) in caplog.records[1].message
