from pathlib import Path
import logging
import subprocess

from errors import ProjectToolError


class CheckError(ProjectToolError):
    """Ошибка запуска pytest или неуспешный результат проверки."""


def run_tests(project: Path, python: Path, timeout: int) -> None:
    """Запускает pytest и записывает его подробный вывод на уровне DEBUG.

    Args:
        project: Рабочий каталог для pytest. В нём выполняется поиск тестов.
        python: Абсолютный путь к интерпретатору или путь от каталога запуска
            CLI. Может указывать на Python из виртуального окружения.
        timeout: Максимальное время выполнения в секундах.

    Returns:
        None при успешном завершении pytest.

    Raises:
        CheckError: Каталог проекта недоступен, процесс не запустился,
            истёк таймаут или pytest вернул ненулевой код. Отсутствие
            собранных тестов также считается ошибкой.
    """
    project = project.expanduser()
    if not project.is_dir():
        raise CheckError(f"Каталог проекта не найден: {project}")

    # resolve() раскроет ссылку из venv и может выбрать системное окружение.
    interpreter = python.expanduser().absolute()
    logger = logging.getLogger(__name__)
    try:
        result = subprocess.run([str(interpreter), "-m", "pytest"],
                                cwd=project, timeout=timeout,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired as exc:
        logger.debug("Вывод pytest перед таймаутом: %r", exc.output)
        raise CheckError(f"Истёк таймаут pytest ({timeout} с)") from exc
    except OSError as exc:
        raise CheckError(f"Не удалось запустить Python: {exc}") from exc

    logger.debug("Вывод pytest:\n%s", result.stdout)
    if result.returncode == 5:
        raise CheckError("Тесты не найдены")
    if result.returncode == 1:
        raise CheckError("Один или несколько тестов не прошли")
    if result.returncode:
        raise CheckError(f"pytest завершился с кодом {result.returncode}")
