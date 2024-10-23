import os

from loguru import logger as base_logger

from app.core.config import config


class Logger:
    def __init__(self):
        self._logger = base_logger
        self._logger.remove()

        log_file = os.path.join(config.log_dir, f"{__name__}.log")
        log_format = "{time} {level} {message}"
        log_level = "INFO"
        self._logger.add(log_file, format=log_format, level=log_level, rotation="10 MB")

    def info(self, message):
        self._logger.info(message)

    def warning(self, message):
        self._logger.warning(message)

    def error(self, message):
        self._logger.error(message)

    def debug(self, message):
        self._logger.debug(message)


logger = Logger()
