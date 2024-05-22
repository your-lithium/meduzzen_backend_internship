from loguru import logger as base_logger


class Logger:
    def __init__(self):
        self.logger = base_logger

        self.logger.remove()
        log_file = f"{__name__}.log"
        log_format = "{time} {level} {message}"
        log_level = "INFO"
        self.logger.add(log_file, format=log_format, level=log_level, rotation="10 MB")

        self.logger.add("file.log")

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def debug(self, message):
        self.logger.debug(message)


logger = Logger()
