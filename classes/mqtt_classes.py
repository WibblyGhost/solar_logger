"""
Classes file, contains methods for the MQTT subscriber which will receive packets
from the broker and input them into an Influx database.
Check the Influx query documentation for write syntax:
https://docs.influxdata.com/influxdb/v2.0/api-guide/client-libraries/python/#query-data-from-influxdb-with-python
"""

import logging
import ssl
import time
from datetime import datetime

from paho.mqtt.client import Client, MQTTMessage
from pymate.matenet import DCStatusPacket, FXStatusPacket, MXStatusPacket

from classes.py_functions import SecretStore
from classes.custom_exceptions import MqttServerOfflineError
from classes.common_classes import QueuePackage
from config.consts import MAX_QUEUE_LENGTH, THREADED_QUEUE


class PyMateDecoder:
    """
    Class which decodes bytestreams received from the MQTT broker
    """

    @staticmethod
    def fx_decoder(msg: bytearray = b"") -> dict:
        """
        Decoder for FX objects
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        fx_packet = FXStatusPacket.from_buffer(msg).__dict__
        return {key: value for (key, value) in fx_packet.items() if key != "raw"}

    @staticmethod
    def mx_decoder(msg: bytearray = b"") -> dict:
        """
        Decoder for MX objects
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        mx_packet = MXStatusPacket.from_buffer(msg).__dict__
        return {key: value for (key, value) in mx_packet.items() if key != "raw"}

    @staticmethod
    def dc_decoder(msg: bytearray = b"") -> dict:
        """
        Decoder for DC objects
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        dc_packet = DCStatusPacket.from_buffer(msg).__dict__
        return {key: value for (key, value) in dc_packet.items() if key != "raw"}

    @staticmethod
    def check_status(msg: MQTTMessage) -> None:
        """
        Called everytime a status message is received and checks the status of the server
        :param msg: Received message from MQTT broker
        """
        status_topics = [
            "mate/status",
            "mate/mx-1/status",
            "mate/fx-1/status",
            "mate/dc-1/status",
        ]
        for status in status_topics:
            if msg.topic == status and msg.payload.decode("ascii") == "offline":
                logging.critical(
                    f"A backend MQTT service isn't online, {status} = offline"
                )
                raise MqttServerOfflineError(
                    f"A backend MQTT service isn't online, {status} = offline"
                )


class MqttConnector:
    """
    Class which creates a client to connect to MQTT subscriber and decode the messages
    """

    def __init__(
        self,
        secret_store: SecretStore,
    ) -> None:
        """
        :param host: Web url for the subscriber to listen on
        :param port: Port which the web server uses for MQTT
        :param user: Username to access MQTT server
        :param token: Token to access MQTT server
        :param influx_connector: Database for the MQTTDecoder to write results to
        """
        self._fx_time = None
        self._mx_time = None
        self._dc_time = None
        self._dec_msg = None
        self._mqtt_secrets = secret_store.mqtt_secrets
        self._mqtt_client = Client()
        self.contiguous_errors = 0

    def get_mqtt_client(self) -> Client:
        """
        Initial setup for the MQTT connector, connects to MQTT broker
        and failing to connect will exit the program
        """
        logging.info("Connecting to MQTT broker")
        self._mqtt_client.username_pw_set(
            username=self._mqtt_secrets["mqtt_user"],
            password=self._mqtt_secrets["mqtt_token"],
        )
        self._mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
        self._mqtt_client.tls_insecure_set(True)
        try:
            self._mqtt_client.connect(
                host=self._mqtt_secrets["mqtt_host"],
                port=self._mqtt_secrets["mqtt_port"],
            )
        except Exception as err:
            print(
                type(self._mqtt_secrets["mqtt_host"]),
                type(self._mqtt_secrets["mqtt_port"]),
            )
            logging.critical("Failed to connect to MQTT broker")
            raise err
        self._mqtt_client.on_connect = self._on_connect
        self._mqtt_client.on_disconnect = self._on_disconnect
        self._mqtt_client.on_message = self._on_message
        return self._mqtt_client

    @staticmethod
    def _on_disconnect(_client, _userdata, _flags, return_code: int) -> None:
        logging.info(f"MQTT disconnected from broker, {return_code}")

    def _on_connect(self, _client, _userdata, _flags, return_code: int) -> None:
        """
        On first connection to MQTT broker this function will subscribe to the brokers topics
        :param _client: Unused
        :param _userdata: Unused
        :param _flags: Unused
        :param return_code: Returned connection code
        """
        try:
            if return_code == 0:
                self._mqtt_client.subscribe(self._mqtt_secrets["mqtt_topic"])
                logging.info(f"Connected to MQTT broker, returned code: {return_code}")
            else:
                logging.warning(
                    f"Connection to MQTT broker refused, returned code: {return_code}"
                )
        except Exception as err:
            logging.critical(
                "Connection to MQTT broker was refused and raised exception."
            )
            raise err

    @staticmethod
    def _load_queue(measurement: str, time_field: datetime, payload: dict) -> None:
        for key, value in payload.items():
            THREADED_QUEUE.put(
                QueuePackage(
                    measurement=measurement,
                    time_field=time_field,
                    field={key: float(value)},
                )
            )
        logging.debug(
            f"Pushed item onto queue, queue now has {THREADED_QUEUE.qsize()} items"
        )

    def _on_message(self, _client, _userdata, msg: MQTTMessage) -> None:
        """
        Called everytime a message is received which it then decodes
        :param msg: Message to partition into categories and decode
        """
        PyMateDecoder.check_status(msg=msg)
        while THREADED_QUEUE.qsize() > MAX_QUEUE_LENGTH:
            logging.warning("Queue is full, sleeping for 0.5 seconds")
            time.sleep(0.5)

        try:
            if msg.topic == "mate/fx-1/stat/ts":
                self._fx_time = int(msg.payload.decode("ascii"))
                self._fx_time = datetime.fromtimestamp(self._fx_time)
                logging.debug(f"Received fx_time packet: {self._fx_time}")
            elif msg.topic == "mate/mx-1/stat/ts":
                self._mx_time = int(msg.payload.decode("ascii"))
                self._mx_time = datetime.fromtimestamp(self._mx_time)
                logging.debug(f"Received mx_time packet: {self._mx_time}")
            elif msg.topic == "mate/dc-1/stat/ts":
                self._dc_time = int(msg.payload.decode("ascii"))
                self._dc_time = datetime.fromtimestamp(self._dc_time)
                logging.debug(f"Received dc_time packet: {self._dc_time}")
            elif msg.topic == "mate/fx-1/stat/raw" and self._fx_time:
                fx_payload = PyMateDecoder.fx_decoder(msg.payload)
                logging.debug("Loading fx_payload onto queue")
                self._load_queue(
                    measurement="fx-1", time_field=self._fx_time, payload=fx_payload
                )
                self.contiguous_errors = 0
            elif msg.topic == "mate/mx-1/stat/raw" and self._mx_time:
                mx_payload = PyMateDecoder.mx_decoder(msg.payload)
                logging.debug("Loading mx_payload onto queue")
                self._load_queue(
                    measurement="mx-1", time_field=self._mx_time, payload=mx_payload
                )
                self.contiguous_errors = 0
            elif msg.topic == "mate/dc-1/stat/raw" and self._dc_time:
                dc_payload = PyMateDecoder.dc_decoder(msg.payload)
                logging.debug("Loading dc_payload onto queue")
                self._load_queue(
                    measurement="dc-1", time_field=self._dc_time, payload=dc_payload
                )
                self.contiguous_errors = 0
        except Exception as err:
            self.contiguous_errors += 1
            logging.warning(f"Failed to decode incoming MQTT packets:\n{err}")
            logging.warning(
                f"Contiguous MQTT errors increased to {self.contiguous_errors}"
            )
