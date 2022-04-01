"""
Contains all functions required to setup logging
"""

import configparser
import logging
import os
from logging import Logger
from logging.handlers import RotatingFileHandler

from config.consts import CONFIG_FILENAME

from classes.custom_exceptions import MissingConfigurationError
from classes.py_functions import strtobool


class LoggingTools:
    """
    Class contains all tools required to create loggers
    """

    def __init__(self, config_name: str, logger: Logger) -> None:
        """
        Initialization of logging class
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
        Reads config file and parses and stores the result
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
            self.is_file_logging = strtobool(file_logging)

            if None in [self.debug_level, self.file_format, self.date_format]:
                raise MissingConfigurationError("Failed to read basic logger configs")

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
                    raise MissingConfigurationError(
                        "Failed to read file logger settings in configs"
                    )
        except Exception as err:
            raise err

    def _create_stdout_logger(self, logger: Logger) -> None:
        """
        Creates a standard STDOUT logger
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
        Creates a rotating file logger which limits log files size
        and when exceeding that size, creates a new log file
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


def create_logger(config_name: str) -> logging:
    """
    Creates a logging instance, can be customised through the config.ini
    :param config_name: Section under the config for the configuration to pull data from
    :return: Logger for logging
    """
    logger = logging.getLogger()
    LoggingTools(config_name=config_name, logger=logger)
    return logging
