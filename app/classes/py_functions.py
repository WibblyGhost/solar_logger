"""
Contains all functions that aren't directly correlated to Influx, MQTT, or logging
"""

import configparser
import csv
import logging
import os

from config.consts import CONFIG_FILENAME

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
        if read_influx:
            self._read_influx_secrets()

    def _read_mqtt_secrets(self) -> dict:
        """
        Gets secret details from the environment file.
        :return mqtt_store: Dictionary of secrets
        """
        try:
            self.mqtt_secrets["mqtt_host"] = os.environ.get("MQTT_HOST")
            self.mqtt_secrets["mqtt_port"] = int(os.environ.get("MQTT_PORT"))
            self.mqtt_secrets["mqtt_user"] = os.environ.get("MQTT_USER")
            self.mqtt_secrets["mqtt_token"] = os.environ.get("MQTT_TOKEN")
            self.mqtt_secrets["mqtt_topic"] = os.environ.get("MQTT_TOPIC")
        except Exception as err:
            logging.error("Ran into error when reading environment variables")
            raise err
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
                raise MissingCredentialsError(
                    f"Missing secret credential for InfluxDB in the .env, {key}"
                )


def strtobool(val: str) -> bool:
    """
    Convert a string representation of truth to true (1) or false (0).
    Note: distutils is being discontinued so this function is required
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    if val in ("n", "no", "f", "false", "off", "0"):
        return False
    raise ValueError(f"invalid truth value %{val!r}")
