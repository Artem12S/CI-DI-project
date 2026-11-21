"""Выполнение отдельных шагов конвейера с журналированием."""

from collections.abc import Callable
import logging
from time import monotonic
from typing import Any


def run_step(
    name: str,
    action: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Выполняет шаг, записывает его исход и возвращает результат операции.

    Args:
        name: Название шага для сообщений в журнале.
        action: Вызываемая операция.
        *args: Позиционные аргументы операции.
        **kwargs: Именованные аргументы операции.

    Returns:
        Результат action без преобразований.

    Raises:
        Exception: Исходное исключение операции после записи ошибки в журнал.
        KeyboardInterrupt: Прерывание пользователем после записи в журнал.
    """
    logger = logging.getLogger(__name__)
    logger.info("Запуск %s", name)
    start = monotonic()
    try:
        result = action(*args, **kwargs)
    except KeyboardInterrupt:
        logger.warning(
            "Проверка прервана пользователем на шаге %s через %.1f с",
            name, monotonic() - start,
        )
        raise
    except Exception as exc:
        logger.error(
            "Шаг %s завершился ошибкой через %.1f с: %s",
            name, monotonic() - start, exc,
        )
        raise
    logger.info("Шаг %s выполнен за %.1f с", name, monotonic() - start)
    return result
