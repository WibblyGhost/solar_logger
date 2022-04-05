"""
Contains all functions required to setup logging
"""

import configparser
import logging
import os
from logging import Logger
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from classes.consts import CONFIG_FILENAME
from classes.custom_exceptions import MissingConfigurationError


class LoggingTools:
    """
    Class contains all tools required to create loggers
    """

    def __init__(self, config_name: str, logger: Logger) -> None:
        """
        Initialization of logging class
        """
        self._debug_level = None
        self._file_format = None
        self._date_format = None
        self._is_file_logging = None
        self._log_rotation = None
        self._file_location = None
        self._file_path = None
        self._max_file_bytes = None
        self._max_file_no = None
        self._read_configs(config_name)

        self._create_stdout_logger(logger=logger)
        if self._is_file_logging and self._log_rotation == "size_based":
            self._create_rotating_file_logger(logger=logger)
        elif self._is_file_logging and self._log_rotation == "time_based":
            self._create_timed_rotating_file_logger(logger=logger)

    def _read_configs(self, config_name: str) -> None:
        """
        Reads config file and parses and stores the result
        """
        config_parser = configparser.ConfigParser()
        try:
            config_parser.read(CONFIG_FILENAME)
            debug_dict = {
                "DEBUG": logging.DEBUG,
                "INFO": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
                "CRITICAL": logging.CRITICAL,
            }
            self._debug_level = debug_dict[
                config_parser.get(config_name, "debug_level")
            ]
            self._file_format = config_parser.get(config_name, "format")
            self._date_format = config_parser.get(config_name, "dateformat")
            self._is_file_logging = config_parser.getboolean(
                config_name, "file_logging"
            )

            if None in [self._debug_level, self._file_format, self._date_format]:
                logging.critical("Failed to read basic logger configs")
                raise MissingConfigurationError("Failed to read basic logger configs")

            if self._is_file_logging:
                self._log_rotation = config_parser.get(config_name, "log_rotation")

                self._file_location = config_parser.get(config_name, "file_location")
                file_name = config_parser.get(config_name, "file_name")
                self._file_path = self._file_location + file_name
                self._max_file_bytes = int(
                    config_parser.get(config_name, "max_file_bytes")
                )
                self._max_file_no = int(config_parser.get(config_name, "max_file_no"))

                if None in [
                    self._file_location,
                    self._file_path,
                    self._max_file_bytes,
                    self._max_file_no,
                ]:
                    logging.critical("Failed to read file logger settings in configs")
                    raise MissingConfigurationError(
                        "Failed to read file logger settings in configs"
                    )
        except Exception as err:
            logging.critical("An unexpected exception has occurred")
            raise err

    def _create_stdout_logger(self, logger: Logger) -> None:
        """
        Creates a standard STDOUT logger
        """
        logger.setLevel(self._debug_level)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(self._debug_level)
        log_formatter = logging.Formatter(
            fmt=self._file_format, datefmt=self._date_format
        )
        stream_handler.setFormatter(log_formatter)
        logger.addHandler(stream_handler)
        logging.info("Created stdout logger")

    def _create_rotating_file_logger(self, logger: Logger) -> None:
        """
        Creates a rotating file logger which limits log files size
        and when exceeding that size, creates a new log file
        """
        if not os.path.exists(self._file_location):
            os.makedirs(self._file_location)

        rotating_handler = RotatingFileHandler(
            filename=self._file_path,
            maxBytes=self._max_file_bytes,
            backupCount=self._max_file_no,
        )
        rotating_handler.setLevel(self._debug_level)
        log_formatter = logging.Formatter(
            fmt=self._file_format, datefmt=self._date_format
        )
        rotating_handler.setFormatter(log_formatter)
        logger.addHandler(rotating_handler)
        logging.info(f"Created rotating file log file at {self._file_path}")

    def _create_timed_rotating_file_logger(self, logger: Logger) -> None:
        """
        Creates a rotating file logger which limits log files size
        and when exceeding that size, creates a new log file
        """
        if not os.path.exists(self._file_location):
            os.makedirs(self._file_location)
        rotating_time_handler = TimedRotatingFileHandler(
            filename=self._file_path,
            when="midnight",
            backupCount=self._max_file_no,
        )
        rotating_time_handler.suffix = "%Y-%m-%d"
        rotating_time_handler.setLevel(self._debug_level)
        log_formatter = logging.Formatter(
            fmt=self._file_format, datefmt=self._date_format
        )
        rotating_time_handler.setFormatter(log_formatter)
        logger.addHandler(rotating_time_handler)
        logging.info(f"Created time rotating file log file at {self._file_path}")


def create_logger(config_name: str) -> logging:
    """
    Creates a logging instance, can be customized through the config.ini
    :param config_name: Section under the config for the configuration to pull data from
    :return: Logger for logging
    """
    logger = logging.getLogger()
    LoggingTools(config_name=config_name, logger=logger)
    return logging
