"""
Contains all functions that aren't directly correlated to Influx, MQTT, or logging
"""

import configparser
import csv
import logging
import os

from config.consts import CONFIG_FILENAME, MAX_PORT_RANGE

from classes.custom_exceptions import MissingCredentialsError


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
        logging.critical("Failed to write CSV")
        raise err


def read_query_settings(config_name: str) -> any:
    """
    :param config_name: Section under the config for the configuration to pull data from
    :return: Query variables
    """
    config_p = configparser.ConfigParser()
    config_p.read(CONFIG_FILENAME)
    return config_p.get(section=config_name, option="query_mode")


class SecretStore:
    """
    Class which reads environment secrets and stores them
    """

    def __init__(self, read_mqtt: bool = False, read_influx: bool = False) -> None:
        """
        :param mqtt_secrests: Dictionary of secrets for MQTT server
        :param influx_secrets: Dictionary of secrets for Influx server
        """
        self._read_mqtt = read_mqtt
        self._read_influx = read_influx

        self._mqtt_secrets = {
            "mqtt_host": None,
            "mqtt_port": None,
            "mqtt_user": None,
            "mqtt_token": None,
            "mqtt_topic": None,
        }
        self._influx_secrets = {
            "influx_url": None,
            "influx_org": None,
            "influx_bucket": None,
            "influx_token": None,
        }

        if self._read_mqtt:
            logging.info("Reading MQTT environment variables")
            self._read_mqtt_secrets()

        if self._read_influx:
            self._read_influx_secrets()
            logging.info("Reading Influx environment variables")

    @property
    def mqtt_secrets(self) -> dict:
        """
        Dictionary containing MQTT secrets
        """
        if self._read_mqtt:
            return self._mqtt_secrets
        else:
            # TODO
            raise NotImplementedError

    @property
    def influx_secrets(self) -> dict:
        """
        Dictionary containing Influx secrets
        """
        if self._read_influx:
            return self._influx_secrets
        else:
            # TODO
            raise NotImplementedError

    def _set_env_secrets(self, env: list) -> None:
        if self._read_mqtt:
            # TODO
            for item in list:
                self.mqtt_secrets[] = item
        if self._read_influx:

    def _read_mqtt_secrets(self) -> dict:
        """
        Gets secret details from the environment file.
        :return mqtt_store: Dictionary of secrets
        """
        try:
            _mqtt_host = os.environ.get("MQTT_HOST")
            _mqtt_port = os.environ.get("MQTT_PORT")
            if not isinstance(_mqtt_port, int):
                _mqtt_port = int(_mqtt_port)
            if _mqtt_port not in range(0, MAX_PORT_RANGE):
                # TODO Exceptions
                raise Exception
            _mqtt_user = os.environ.get("MQTT_USER")
            _mqtt_token = os.environ.get("MQTT_TOKEN")
            _mqtt_topic = os.environ.get("MQTT_TOPIC")
        except Exception as err:
            # TODO
            logging.critical("Ran into error when reading environment variables")
            raise err


    def _read_influx_secrets(self) -> dict:
        """
        Gets secret details from the environment file.
        :return influx_store: Dictionary of secrets
        """
        try:
            self._influx_secrets["influx_url"] = os.environ.get("INFLUX_URL")
            self._influx_secrets["influx_org"] = os.environ.get("INFLUX_ORG")
            self._influx_secrets["influx_bucket"] = os.environ.get("INFLUX_BUCKET")
            self._influx_secrets["influx_token"] = os.environ.get("INFLUX_TOKEN")
        except TypeError as err:
            logging.critical("Missing secret credential for MQTT in the .env-")
            raise MissingCredentialsError(
                "Missing secret credential for MQTT in the .env"
            ) from err
        except ValueError as err:
            logging.critical("Missing secret credential for Influx in the .env")
            raise MissingCredentialsError(
                "Missing secret credential for Influx in the .env"
            ) from err
        except Exception as err:
            logging.critical("Ran into error when reading environment variables")
            raise err
        for key, value in self._influx_secrets.items():
            if not value:
                logging.critical(
                    f"Missing secret credential for InfluxDB in the .env, {key}"
                )
                raise MissingCredentialsError(
                    f"Missing secret credential for InfluxDB in the .env, {key}"
                )
