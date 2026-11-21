import argparse
import logging
from pathlib import Path
import sys

from errors import ProjectToolError
from log import configure_log
from pipeline import run_step
from pytest_runner import run_tests


def main() -> int:
    """Читает аргументы из sys.argv, открывает журнал и запускает проверку.

    Returns:
        0 при успехе, 1 при ошибке журнала или проверки, 130 при прерывании
        выполнения шага пользователем. Ожидаемые ошибки шагов должны
        наследоваться от ProjectToolError.

    Raises:
        SystemExit: argparse завершает разбор с кодом 2 при ошибке аргументов
            или с кодом 0 при запросе справки.
    """
    parser = argparse.ArgumentParser(description="Проверка Python-проекта")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="проверить проект")
    check.add_argument("--only", choices=["tests"], required=True,
                       help="вид проверки")
    check.add_argument("--project", type=Path, default=Path.cwd(),
                       help="каталог проверяемого проекта")
    check.add_argument("--python", type=Path, default=Path(sys.executable),
                       help="путь к Python проверяемого проекта")
    check.add_argument("--test-timeout", type=int, default=300,
                       help="время на pytest в секундах (по умолчанию 300)")
    check.add_argument("--log-file", type=Path, help="путь к журналу запуска")
    args = parser.parse_args()
    if args.test_timeout <= 0:
        check.error("--test-timeout должен быть положительным")

    try:
        log_path = configure_log(args.log_file)
    except OSError as exc:
        print(f"Не удалось открыть журнал: {exc}", file=sys.stderr)
        return 1

    logger = logging.getLogger(__name__)
    logger.info("Журнал: %s", log_path)
    logger.info("Проект: %s", args.project)
    try:
        run_step("pytest", run_tests,
                 args.project, args.python, args.test_timeout)
    except ProjectToolError:
        return 1
    except KeyboardInterrupt:
        return 130
    logger.info("Тесты прошли")
    return 0


if __name__ == "__main__":
    sys.exit(main())
