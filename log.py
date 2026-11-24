import logging
from pathlib import Path
from uuid import uuid4


def configure_log(path: Path | None = None) -> Path:
    """Настраивает корневой логгер CLI для записи в UTF-8 и вывода в stderr.

    Каждый вызов заменяет обработчики корневого логгера. Если файл уже
    существует, новые сообщения добавляются в конец. Диагностика DEBUG,
    включая traceback, сохраняется в файл. Терминал получает уровни INFO
    и выше. Внутренний отладочный вывод ошибок logging отключается.

    Args:
        path: Путь к журналу. Родительские каталоги создаются при открытии.
            По умолчанию каждый вызов создаёт отдельный файл в logs/ внутри
            текущего каталога.

    Returns:
        Путь к открытому журналу.

    Raises:
        OSError: Если каталог или файл недоступен для записи.
    """
    if path is None:
        path = Path("logs") / f"run-{uuid4().hex}.log"
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(path, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    ))
    terminal_handler = logging.StreamHandler()
    terminal_handler.setLevel(logging.INFO)
    logging.basicConfig(level=logging.DEBUG, format="%(message)s", force=True,
                        handlers=[file_handler, terminal_handler])
    logging.raiseExceptions = False
    return path
