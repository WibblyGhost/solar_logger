"""
Contains both a logger and csv writing function for use in outside functions
"""

import configparser
import csv
from distutils.util import strtobool
import logging
import os

from config.consts import CONFIG_FILENAME

# from classes.py_logger import LoggerConfigs


def create_logger(config_name: str) -> logging:
    """
    Creates a logging instance, can be customised through the config.ini
    :param config_name: Section under the config for the configuration to pull data from
    :return: Logger for logging
    """
    config_p = configparser.ConfigParser()
    config_p.read(CONFIG_FILENAME)
    file_logging = config_p.get(config_name, "file_logging")
    file_logging = bool(strtobool(file_logging))
    debug_dict = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    debug_level = debug_dict[config_p.get(config_name, "debug_level")]
    file_format = config_p.get(config_name, "format")
    date_format = config_p.get(config_name, "dateformat")

    logger = logging.getLogger()
    logger.setLevel(debug_level)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(debug_level)
    log_formatter = logging.Formatter(fmt=file_format, datefmt=date_format)
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)
    logging.info("Created logger")

    if file_logging:
        file_location = config_p.get(config_name, "file_location")
        if not os.path.exists(file_location):
            os.makedirs(file_location)
        filename = config_p.get(config_name, "file_name")
        full_path = file_location + filename
        file_mode = config_p.get(config_name, "file_mode")
        file_stream_handler = logging.FileHandler(filename=full_path, mode=file_mode)
        file_stream_handler.setLevel(debug_level)
        file_stream_handler.setFormatter(log_formatter)
        logger.addHandler(file_stream_handler)
        logging.info(f"Created file logger at {full_path}")

    return logging


# def create_logger(config_name: str) -> logging:
#     """
#     Creates a logging instance, can be customised through the config.ini
#     :param config_name: Section under the config for the configuration to pull data from
#     :return: Logger for logging
#     """
#     logger = logging.getLogger()
#     LoggerConfigs(config_name=config_name, logger=logger)
#     return logging


def write_results_to_csv(config_name: str, table: dict) -> None:
    """
    Writes a CSV file from an Influx query
    :param config_name: Section under the config for the configuration to pull data from
    :param table: Resultant CSV query from the Influx database
    """
    try:
        config_p = configparser.ConfigParser()
        config_p.read(CONFIG_FILENAME)
        file_location = config_p.get(config_name, "csv_location")
        filename = config_p.get(config_name, "csv_name")
        full_path = file_location + filename
        filemode = config_p.get(config_name, "csv_mode")

        if not os.path.exists(file_location):
            os.makedirs(file_location)
        with open(full_path, filemode) as file_instance:
            writer = csv.writer(file_instance)
            for row in table:
                writer.writerow(row)
        logging.info(f"Wrote rows into CSV file at: {full_path}")
    except Exception as err:
        raise err


def read_query_settings(config_name: str):
    """
    :param config_name: Section under the config for the configuration to pull data from
    :return: Query variables
    """
    config_p = configparser.ConfigParser()
    config_p.read(CONFIG_FILENAME)
    return config_p.get(section=config_name, option="query_mode")


class SecretStore:
    """
    TODO
    """

    def __init__(self, read_mqtt: bool = False, read_influx: bool = False):
        """
        TODO
        """
        self.mqtt_secrets = {
            "mqtt_host": None,
            "mqtt_port": None,
            "mqtt_user": None,
            "mqtt_token": None,
            "mqtt_topic": None,
        }

        self.influx_secrets = {
            "influx_url": None,
            "influx_org": None,
            "influx_bucket": None,
            "influx_token": None,
        }

        if read_mqtt:
            self._read_mqtt_secrets()
        elif read_influx:
            self._read_influx_secrets()

    def _read_mqtt_secrets(self) -> dict:
        """
        Gets secret details from the environment file.
        :return mqtt_store: Dictionary of secrets
        """
        self.mqtt_secrets["mqtt_host"] = os.environ.get("MQTT_HOST")
        self.mqtt_secrets["mqtt_port"] = int(os.environ.get("MQTT_PORT"))
        self.mqtt_secrets["mqtt_user"] = os.environ.get("MQTT_USER")
        self.mqtt_secrets["mqtt_token"] = os.environ.get("MQTT_TOKEN")
        self.mqtt_secrets["mqtt_topic"] = os.environ.get("MQTT_TOPIC")
        for key, value in self.mqtt_secrets.items():
            if not value:
                logging.error(f"Missing secret credential for MQTT in the .env, {key}")
                raise ValueError(
                    f"Missing secret credential for MQTT in the .env, {key}"
                )

    def _read_influx_secrets(self) -> dict:
        """
        Gets secret details from the environment file.
        :return influx_store: Dictionary of secrets
        """
        self.influx_secrets["influx_url"] = os.environ.get("INFLUX_URL")
        self.influx_secrets["influx_org"] = os.environ.get("INFLUX_ORG")
        self.influx_secrets["influx_bucket"] = os.environ.get("INFLUX_BUCKET")
        self.influx_secrets["influx_token"] = os.environ.get("INFLUX_TOKEN")
        for key, value in self.influx_secrets.items():
            if not value:
                logging.error(
                    f"Missing secret credential for InfluxDB in the .env, {key}"
                )
                raise ValueError(
                    f"Missing secret credential for InfluxDB in the .env. {key}"
                )
