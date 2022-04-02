"""
Classes file, contains methods for the Influx database controller
to do writes and queries to the database
"""

import logging
import signal

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from classes.custom_exceptions import MissingCredentialsError
from config.consts import ERROR_COUNTS


class InfluxConnector:
    """
    Class which creates a client to access and modify a connected database
    """

    influx_client = None
    influx_bucket = None
    influx_org = None

    def __init__(self, url: str, org: str, bucket: str, token: str) -> None:
        """
        :param token: Secret password to login to database with
        :param org: Organisation of the bucket to login to
        :param bucket: Database source
        :param url: Web address to connect to database
        """
        self._influx_token = token
        self._influx_url = url
        self.influx_org = org
        self.influx_bucket = bucket
        self.influx_client = InfluxDBClient

    def influx_startup(self) -> None:
        """
        Defines the initialization of the Influx connector,
        invoking the connection to the InfluxDB and write API
        """
        logging.info("Attempting to connect to InfluxDB server")
        client = None
        try:
            client = InfluxDBClient(
                url=self._influx_url, token=self._influx_token, org=self.influx_org
            )
            client.ready()
            logging.info("Successfully connected to InfluxDB server")
        except Exception as err:
            logging.critical("Failed to connect InfluxDB server\n--quitting--")
            raise err
        finally:
            self.influx_client = client


def create_influx_connector(influx_secrets: dict) -> InfluxConnector:
    """
    classes function that creates a Influx connector
    :param influx_secret: Secret passwords and logins for Influx database
    :return: A database connector object which can be used to write/read data points
    """
    for key, value in influx_secrets.items():
        if not value:
            logging.critical(
                f"Missing secret credential for InfluxDB in the .env, {key}\n--quitting--"
            )
            raise MissingCredentialsError(
                f"Missing secret credential for InfluxDB in the .env, {key}"
            )

    connector = InfluxConnector(
        url=influx_secrets["influx_url"],
        org=influx_secrets["influx_org"],
        bucket=influx_secrets["influx_bucket"],
        token=influx_secrets["influx_token"],
    )
    connector.influx_startup()
    return connector


def influx_db_write_points(
    msg_time: str,
    msg_payload: dict,
    msg_type: str,
    influx_connector: InfluxConnector,
) -> None:
    """
    Adds message to Influx database
    :param msg_dict: Message for MQTTDecoder to input into the Influx Database in dictionary
    :param msg_type: Type of header the msg carries, either FX, MX or DX
    """
    logging.debug(f"Creating database points from ({msg_time}, {msg_type})")
    write_client = influx_connector.influx_client.write_api(write_options=SYNCHRONOUS)
    try:
        for key, value in msg_payload.items():
            point_template = {
                "measurement": msg_type,
                "fields": {key: float(value)},
            }
            logging.debug(f"Wrote point: {point_template} at {msg_time}")
            write_client.write(
                bucket=influx_connector.influx_bucket,
                org=influx_connector.influx_org,
                record=point_template,
                time=msg_time,
            )
            ERROR_COUNTS.contiguous_influx_errors = 0
    except Exception as err:
        ERROR_COUNTS.contiguous_influx_errors += 1
        logging.warning(f"Failed to run write, returned error: {err}")
        logging.warning(
            f"Contiguous Influx errors increased to {ERROR_COUNTS.contiguous_influx_errors}"
        )
    finally:
        if ERROR_COUNTS.contiguous_influx_errors >= ERROR_COUNTS.max_influx_errors:
            logging.critical(
                f"Contiguous Influx errors has exceceded max count, \
                    {ERROR_COUNTS.max_influx_errors}\n--quitting--"
            )
            signal.raise_signal(signal.SIGTERM)
