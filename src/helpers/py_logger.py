"""
Contains all functions required to setup logging
"""

import logging
import os
from configparser import ConfigParser
from logging import Logger, StreamHandler
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from src.classes.custom_exceptions import MissingConfigurationError
from src.helpers.consts import CONFIG_FILENAME, SOLAR_DEBUG_CONFIG_TITLE


class LoggingTools:
    """
    Class contains all tools required to create loggers
    """

    def __init__(
        self, config_name: str, logger: Logger, config_dir: str = CONFIG_FILENAME
    ) -> None:
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
        self._mode = None
        self._logger = logger
        self._config_dir = config_dir
        self._config_name = config_name
        self._config_parser = ConfigParser()

    def create_loggers(self):
        """
        Creates loggers from the given configs
        """
        self._create_stdout_logger(logger=self._logger)
        if self._is_file_logging and self._log_rotation == "size_based":
            self._create_rotating_file_logger(logger=self._logger)
        elif self._is_file_logging and self._log_rotation == "time_based":
            self._create_timed_rotating_file_logger(logger=self._logger)

    def _read_basic_config(self) -> None:
        try:
            debug_dict = {
                "DEBUG": logging.DEBUG,
                "INFO": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
                "CRITICAL": logging.CRITICAL,
            }
            self._debug_level = debug_dict[
                self._config_parser.get(self._config_name, "debug_level")
            ]
            self._file_format = self._config_parser.get(self._config_name, "format")
            self._date_format = self._config_parser.get(self._config_name, "dateformat")
            self._is_file_logging = self._config_parser.getboolean(
                self._config_name, "file_logging"
            )
        except Exception as err:
            logging.critical("Failed to read basic logger configs")
            raise MissingConfigurationError(
                "Failed to read basic logger configs"
            ) from err

        if None in [self._debug_level, self._file_format, self._date_format]:
            logging.critical("Failed to read basic logger configs")
            raise MissingConfigurationError("Failed to read basic logger configs")

    def _read_extra_configs(self) -> None:
        try:
            self._log_rotation = self._config_parser.get(
                self._config_name, "log_rotation"
            )

            self._file_location = self._config_parser.get(
                self._config_name, "file_location"
            )
            file_name = self._config_parser.get(self._config_name, "file_name")
            self._file_path = self._file_location + file_name
            self._max_file_bytes = int(
                self._config_parser.get(self._config_name, "max_file_bytes")
            )
            self._max_file_no = int(
                self._config_parser.get(self._config_name, "max_file_no")
            )
            if self._config_name == SOLAR_DEBUG_CONFIG_TITLE:
                self._mode = str(self._config_parser.get(self._config_name, "mode"))
        except Exception as err:
            logging.critical("Failed to read file logger settings in configs")
            raise MissingConfigurationError(
                "Failed to read file logger settings in configs"
            ) from err

        if (
            None
            in [
                self._log_rotation,
                self._file_location,
                self._file_path,
                self._max_file_bytes,
                self._max_file_no,
            ]
            or (self._config_name == SOLAR_DEBUG_CONFIG_TITLE and self._mode is None)
            or self._mode in ["None", ""]
        ):
            logging.critical("Failed to read file logger settings in configs")
            raise MissingConfigurationError(
                "Failed to read file logger settings in configs"
            )

    def read_configs(self) -> None:
        """
        Reads config file and parses and stores the result
        """
        self._config_parser.read(self._config_dir)
        self._read_basic_config()
        if self._is_file_logging:
            self._read_extra_configs()

    def _create_stdout_logger(self, logger: Logger) -> None:
        """
        Creates a standard STDOUT logger
        """
        logger.setLevel(self._debug_level)
        stream_handler = StreamHandler()
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
            os.makedirs(self._file_location)  # pragma: no cover

        rotating_handler = RotatingFileHandler(
            filename=self._file_path,
            maxBytes=self._max_file_bytes,
            backupCount=self._max_file_no,
            mode=self._mode,
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
            os.makedirs(self._file_location)  # pragma: no cover
        rotating_time_handler = TimedRotatingFileHandler(
            filename=self._file_path,
            when="midnight",
            backupCount=self._max_file_no,
        )
        rotating_time_handler.suffix = "%Y-%m-%d"
        rotating_time_handler.setLevel(self._debug_level)
        log_formatter = logging.Formatter(
            fmt=self._file_format,
            datefmt=self._date_format,
        )
        rotating_time_handler.setFormatter(log_formatter)
        logger.addHandler(rotating_time_handler)
        logging.info(f"Created time rotating file log file at {self._file_path}")


def create_logger(
    config_name: str, config_dir: str = CONFIG_FILENAME
) -> Logger:  # pragma: no cover
    """
    Creates a logging instance, can be customized through the config.ini
    :param config_name: Section under the config for the configuration to pull data from
    :return: Logger for logging
    """

    logger = logging.getLogger()
    logging_tools = LoggingTools(
        config_name=config_name, config_dir=config_dir, logger=logger
    )
    logging_tools.read_configs()
    logging_tools.create_loggers()
    return logger
