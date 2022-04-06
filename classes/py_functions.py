"""
Contains all functions that aren't directly correlated to Influx, MQTT, or logging
"""

import configparser
import csv
import logging
import os

from classes.consts import CONFIG_FILENAME, MAX_PORT_RANGE
from classes.custom_exceptions import MissingCredentialsError


def write_results_to_csv(config_name: str, table: dict) -> None:
    """
    Writes a CSV file from an Influx query
    :param config_name: Section under the config for the configuration to pull data from
    :param table: Resultant CSV query from the Influx database
    """
    try:
        config_parser = configparser.ConfigParser()
        config_parser.read(CONFIG_FILENAME)
        file_location = config_parser.get(config_name, "csv_location")
        filename = config_parser.get(config_name, "csv_name")
        full_path = file_location + filename
        filemode = config_parser.get(config_name, "csv_mode")
        if not os.path.exists(file_location):
            os.makedirs(file_location)
        with open(full_path, filemode) as file_instance:
            writer = csv.writer(file_instance)
            for row in table:
                writer.writerow(row)
        logging.info(f"Wrote rows into CSV file at: {full_path}")
    except Exception as err:
        logging.critical("Failed to write CSV")
        raise err


def read_query_settings(config_name: str) -> any:
    """
    :param config_name: Section under the config for the configuration to pull data from
    :return: Query variables
    """
    config_parser = configparser.ConfigParser()
    config_parser.read(CONFIG_FILENAME)
    return config_parser.get(section=config_name, option="query_mode")


class SecretStore:
    """
    Class which reads environment secrets and stores them
    """

    def __init__(
        self, has_mqtt_access: bool = False, has_influx_access: bool = False
    ) -> None:
        """
        :param mqtt_secrests: Dictionary of secrets for MQTT server
        :param influx_secrets: Dictionary of secrets for Influx server
        """
        self._has_mqtt_access = has_mqtt_access
        self._has_influx_access = has_influx_access

        self._mqtt_secrets = None
        self._influx_secrets = None

        if self._has_mqtt_access:
            logging.info("Reading MQTT environment variables")
            self._read_env_mqtt()

        if self._has_influx_access:
            logging.info("Reading Influx environment variables")
            self._read_env_influx()

    @property
    def mqtt_secrets(self) -> dict | None:
        """
        Dictionary containing MQTT secrets
        """
        assert self._mqtt_secrets is not None
        return self._mqtt_secrets

    @property
    def influx_secrets(self) -> dict | None:
        """
        Dictionary containing Influx secrets
        """
        assert self._influx_secrets is not None
        return self._influx_secrets

    def _read_env_mqtt(self) -> dict:
        """
        Gets secret details from the environment file.
        :return mqtt_store: Dictionary of secrets
        """
        try:
            mqtt_port = int(os.environ.get("MQTT_PORT"))
            if mqtt_port not in range(0, MAX_PORT_RANGE):
                raise ValueError(
                    f"MQTT port outside maximum port range, 0-{MAX_PORT_RANGE}"
                )
            self._mqtt_secrets = {
                "mqtt_host": os.environ.get("MQTT_HOST"),
                "mqtt_user": os.environ.get("MQTT_USER"),
                "mqtt_port": mqtt_port,
                "mqtt_token": os.environ.get("MQTT_TOKEN"),
                "mqtt_topic": os.environ.get("MQTT_TOPIC"),
            }
            assert "" not in self._mqtt_secrets.values()
        except Exception as err:
            logging.critical("Ran into error when reading environment variables")
            raise MissingCredentialsError(
                "Ran into error when reading environment variables"
            ) from err

    def _read_env_influx(self) -> dict:
        """
        Gets secret details from the environment file.
        :return influx_store: Dictionary of secrets
        """
        try:
            self._influx_secrets = {
                "influx_url": os.environ.get("INFLUX_URL"),
                "influx_org": os.environ.get("INFLUX_ORG"),
                "influx_bucket": os.environ.get("INFLUX_BUCKET"),
                "influx_token": os.environ.get("INFLUX_TOKEN"),
            }
            assert "" not in self._influx_secrets.values()
        except Exception as err:
            logging.critical("Ran into error when reading environment variables")
            raise MissingCredentialsError(
                "Ran into error when reading environment variables"
            ) from err
