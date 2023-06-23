import logging

import typer


class TyperLoggerHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        fg = None
        bg = None
        if record.levelno == logging.DEBUG:
            fg = typer.colors.BLACK
        elif record.levelno == logging.INFO:
            fg = typer.colors.BRIGHT_BLUE
        elif record.levelno == logging.WARNING:
            fg = typer.colors.BRIGHT_MAGENTA
        elif record.levelno == logging.CRITICAL:
            fg = typer.colors.BRIGHT_RED
        elif record.levelno == logging.ERROR:
            fg = typer.colors.BRIGHT_WHITE
            bg = typer.colors.RED
        typer.secho(self.format(record), bg=bg, fg=fg)


def get_logger():
    # Note to self! Without declaring basicConfig, the logger will not respond to any change in the logging level
    typer_handler = TyperLoggerHandler()
    logging.basicConfig(format="[%(asctime)s: %(levelname)s/%(name)s] | %(message)s", handlers=(typer_handler,))
    _logger = logging.getLogger("bumpyproject")
    return _logger


logger = get_logger()
