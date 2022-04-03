"""
Classes file, contains methods for the Influx database controller
to do writes and queries to the database
"""

import logging

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from classes.py_functions import SecretStore


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
        influx_secrets = secret_store.influx_secrets

        self._influx_org = influx_secrets["influx_org"]
        self._influx_bucket = influx_secrets["influx_bucket"]

        logging.info("Initializing InfluxDB client")
        self._influx_client = InfluxDBClient(
            url=influx_secrets["influx_url"],
            org=influx_secrets["influx_org"],
            token=influx_secrets["influx_token"],
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
        logging.info("Influx health check succeeded")

    def write_points(self, msg_time: str, msg_type: str, msg_payload: dict) -> None:
        """
        Writes points to InfluxDB
        :param msg_time: Time value of the packet
        :param msg_type: Type of header the msg carries, either FX, MX or DX
        :param msg_payload: Dictionary of messages for MQTTDecoder to input into the
            Influx Database in dictionary
        """
        for key, value in msg_payload.items():
            point_template = {
                "measurement": msg_type,
                "fields": {key: float(value)},
            }
            self._write_client.write(
                bucket=self._influx_bucket,
                org=self._influx_org,
                record=point_template,
                time=msg_time,
            )  # External request
            logging.debug(f"Wrote point: {point_template} at {msg_time}")

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
        return query_result
