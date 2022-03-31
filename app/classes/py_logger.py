import configparser
from distutils.util import strtobool
import logging

from logging import Logger
from logging.handlers import RotatingFileHandler
import os

from classes.custom_exceptions import EmptyConfig
from config.consts import CONFIG_FILENAME


class LoggerConfigs:
    """
    TODO
    """

    def __init__(self, config_name: str, logger: Logger) -> None:
        """
        TODO
        """
        self.debug_level = None
        self.file_format = None
        self.date_format = None
        self.is_file_logging = None
        self.file_location = None
        self.file_path = None
        self.max_file_bytes = None
        self.max_file_no = None
        self._read_configs(config_name)

        self._create_stdout_logger(logger=logger)
        if self.is_file_logging:
            self._create_rotating_file_logger(logger=logger)

    def _read_configs(self, config_name: str) -> None:
        """
        TODO
        """
        config_p = configparser.ConfigParser()
        try:
            config_p.read(CONFIG_FILENAME)
            debug_dict = {
                "DEBUG": logging.DEBUG,
                "INFO": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
                "CRITICAL": logging.CRITICAL,
            }
            self.debug_level = debug_dict[config_p.get(config_name, "debug_level")]
            self.file_format = config_p.get(config_name, "format")
            self.date_format = config_p.get(config_name, "dateformat")
            file_logging = config_p.get(config_name, "file_logging")
            self.is_file_logging = bool(strtobool(file_logging))

            if None in [self.debug_level, self.file_format, self.date_format]:
                raise EmptyConfig("Failed to read basic logger configs")

            if self.is_file_logging:
                self.file_location = config_p.get(config_name, "file_location")
                file_name = config_p.get(config_name, "file_name")
                self.file_path = self.file_location + file_name
                self.max_file_bytes = int(config_p.get(config_name, "max_file_bytes"))
                self.max_file_no = int(config_p.get(config_name, "max_file_no"))

                if None in [
                    self.file_location,
                    self.file_path,
                    self.max_file_bytes,
                    self.max_file_no,
                ]:
                    raise EmptyConfig("Failed to read file logger settings in configs")
        except Exception as err:
            raise err

    def _create_stdout_logger(self, logger: Logger) -> None:
        """
        TODO
        """
        logger.setLevel(self.debug_level)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(self.debug_level)
        log_formatter = logging.Formatter(
            fmt=self.file_format, datefmt=self.date_format
        )
        stream_handler.setFormatter(log_formatter)
        logger.addHandler(stream_handler)
        logging.info("Created stdout logger")

    def _create_rotating_file_logger(self, logger: Logger) -> None:
        """
        TODO
        """
        if not os.path.exists(self.file_location):
            os.makedirs(self.file_location)

        rotating_handler = RotatingFileHandler(
            filename=self.file_path,
            maxBytes=self.max_file_bytes,
            backupCount=self.max_file_no,
        )
        rotating_handler.setLevel(self.debug_level)
        log_formatter = logging.Formatter(
            fmt=self.file_format, datefmt=self.date_format
        )
        rotating_handler.setFormatter(log_formatter)
        logger.addHandler(rotating_handler)
        logging.info(f"Created rotating file logger at {self.file_path}")
