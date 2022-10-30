"""
File which contains classes required by both Influx and MQTT
This file should be minimal since both MQTT and Influx is independent.
"""


import logging
import os
from dataclasses import dataclass
from datetime import datetime

from src.classes.custom_exceptions import MissingCredentialsError
from src.helpers.consts import MAX_PORT_RANGE


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
        assert self._mqtt_secrets is not None, "MQTT secrets missing"
        return self._mqtt_secrets

    @property
    def influx_secrets(self) -> dict | None:
        """
        Dictionary containing Influx secrets
        """
        assert self._influx_secrets is not None, "Influx secrets missing"
        return self._influx_secrets

    def _read_env_mqtt(self) -> dict:
        """
        Gets secret details from the environment file.
        :return mqtt_store: Dictionary of secrets
        """
        try:
            mqtt_port = int(os.environ.get("MQTT_PORT"))
            if mqtt_port not in range(0, MAX_PORT_RANGE):
                logging.critical(
                    f"MQTT port outside maximum port range, 0-{MAX_PORT_RANGE}"
                )
                raise MissingCredentialsError(
                    f"MQTT port outside maximum port range, 0-{MAX_PORT_RANGE}"
                )
            self._mqtt_secrets = {
                "mqtt_host": os.environ.get("MQTT_HOST"),
                "mqtt_user": os.environ.get("MQTT_USER"),
                "mqtt_port": mqtt_port,
                "mqtt_token": os.environ.get("MQTT_TOKEN"),
                "mqtt_topic": os.environ.get("MQTT_TOPIC"),
            }
            assert None not in self._mqtt_secrets.values()
            assert "" not in self._mqtt_secrets.values()
        except (AssertionError, TypeError) as err:
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
            assert None not in self._influx_secrets.values()
            assert "" not in self._influx_secrets.values()
        except AssertionError as err:
            logging.critical("Ran into error when reading environment variables")
            raise MissingCredentialsError(
                "Ran into error when reading environment variables"
            ) from err


@dataclass
class QueuePackage:
    """
    Data class which defines values that are pushed and popped off the global stack
    """

    measurement: str = None
    time_field: datetime = None
    field: str = None
