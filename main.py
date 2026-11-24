import argparse
import logging
from pathlib import Path
import sys

from errors import ProjectToolError
from log import configure_log
from pipeline import run_step
from pytest_runner import run_tests


def parse_arguments() -> argparse.Namespace:
    """Читает и проверяет аргументы из sys.argv.

    Returns:
        Параметры выбранной команды.

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
    return args


def main() -> int:
    """Выполняет CLI и обрабатывает ошибки подготовки и проверки.

    Returns:
        0 при успехе, 1 при ошибке, 130 при прерывании пользователем.

    Raises:
        SystemExit: argparse завершает разбор с кодом 2 при ошибке аргументов
            или с кодом 0 при запросе справки.
    """
    log_path = None
    logger = logging.getLogger(__name__)
    try:
        args = parse_arguments()
        try:
            log_path = configure_log(args.log_file)
        except OSError as exc:
            print(f"Не удалось открыть журнал: {exc}", file=sys.stderr)
            return 1
        logger.info("Журнал: %s", log_path)
        logger.info("Проект: %s", args.project)
        run_step("pytest", run_tests,
                 args.project, args.python, args.test_timeout)
        logger.info("Тесты прошли")
        return 0
    except ProjectToolError:
        return 1
    except KeyboardInterrupt:
        print("Выполнение прервано.", file=sys.stderr)
        return 130
    except Exception:
        if log_path is None:
            print("Не удалось подготовить запуск проверки.", file=sys.stderr)
        else:
            logger.debug("Непредвиденная ошибка", exc_info=True)
            print(f"Непредвиденная ошибка. Подробности в журнале: {log_path}",
                  file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
