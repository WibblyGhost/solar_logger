"""
Classes file, contains methods for the Influx database controller
to do writes and queries to the database
"""

import logging
from datetime import datetime

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from src.classes.common_classes import QueuePackage, SecretStore


class InfluxConnector:
    """
    Class which creates a client to access and modify a connected database
    """

    def __init__(self, secret_store: SecretStore) -> None:
        """
        :param token: Secret password to login to database with
        :param org: Organization of the bucket to login to
        :param bucket: Database source
        :param url: Web address to connect to database
        """
        _influx_secrets = secret_store.influx_secrets

        self._influx_org = _influx_secrets["influx_org"]
        self._influx_bucket = _influx_secrets["influx_bucket"]

        logging.info("Initializing InfluxDB client")
        self._influx_client = InfluxDBClient(
            url=_influx_secrets["influx_url"],
            org=_influx_secrets["influx_org"],
            token=_influx_secrets["influx_token"],
        )
        logging.info("Initializing Influx write api")
        self._write_client = self._influx_client.write_api(write_options=SYNCHRONOUS)
        logging.info("Initializing Influx query api")
        self._query_client = self._influx_client.query_api(query_options=SYNCHRONOUS)

    def health_check(self) -> None:
        """
        Defines the initialization of the Influx connector,
        invoking the connection to the InfluxDB and write API
        """
        self._influx_client.ready()  # External request

    @staticmethod
    def _verify_queue_package(queue_package: QueuePackage):
        assertion_message = "The received queue_packed has malformed data: "
        assert queue_package is not None, assertion_message + "queue_package empty"
        assert isinstance(queue_package.measurement, str), (
            assertion_message + "type of measurement not str"
        )
        assert isinstance(queue_package.field, dict | str), (
            assertion_message + "type of field not, dict | str"
        )
        assert isinstance(queue_package.time_field, datetime), (
            assertion_message + "type of time_field not, datetime"
        )

    def write_points(self, queue_package: QueuePackage) -> None:
        """
        Writes points to InfluxDB
        :param msg_time: Time value of the packet
        :param msg_type: Type of header the msg carries, either FX, MX or DX
        :param msg_payload: Dictionary of messages for MQTTDecoder to input into the
            Influx Database in dictionary
        """
        self._verify_queue_package(queue_package=queue_package)
        self._write_client.write(
            bucket=self._influx_bucket,
            org=self._influx_org,
            record={
                "measurement": queue_package.measurement,
                "fields": queue_package.field,
            },
            time=queue_package.time_field,
        )  # External request
        logging.debug(f"Wrote point: {queue_package} at {queue_package.time_field}")

    def query_database(self, query_mode: str, query: str) -> None:
        """
        Runs given query on Influx database and returns results
        :param query_mode: Defines what mode to run the query in,
            supports "csv", "flux" and "stream"
        :param query: Input query to run on Influx database
        """
        query_result = None
        if query_mode == "csv":
            query_result = self._query_client.query_csv(
                org=self._influx_org, query=query
            )  # External request
        elif query_mode == "flux":
            query_result = self._query_client.query(
                org=self._influx_org, query=query
            )  # External request
        elif query_mode == "stream":
            query_result = self._query_client.query_stream(
                org=self._influx_org, query=query
            )  # External request
        logging.debug("Query to Influx server was successful")
        return query_result
