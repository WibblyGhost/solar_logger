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
from classes.common_classes import QueuePackage
from classes.consts import QUEUE_WAIT_TIME, THREADED_QUEUE


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
        self._status = {
            "mate/status": "offline",
            "mate/mx-1/status": "offline",
            "mate/fx-1/status": "offline",
            "mate/dc-1/status": "offline",
        }
        self._fx_time = None
        self._mx_time = None
        self._dc_time = None
        self._dec_msg = None
        self._mqtt_secrets = secret_store.mqtt_secrets
        self._mqtt_client = Client()

    def _on_subscribe(self) -> None:
        """
        Logs when the MQTT client calls on_subscribe
        """
        logging.info("Subscribed to MQTT topic, _on_subscribe")

    def _on_unsubscribe(self) -> None:
        """
        Logs when MQTT calls on_unsubscribe
        """
        logging.info("Unsubscribed from MQTT topic, _on_unsubscribe")

    def _on_connect(self) -> None:
        """
        Logs when MQTT calls on_connect
        """
        logging.info("Connecting to MQTT broker, _on_connect")

    def _on_disconnect(self) -> None:
        """
        Logs when MQTT calls on_disconnect
        """
        logging.warning("Disconnected from MQTT broker, _on_disconnect")

    def _check_status(self, msg: MQTTMessage) -> None:
        """
        Called everytime a status message is received and checks the status of the server
        :param msg: Received message from MQTT broker
        """
        for topic, _ in self._status.items():
            if msg.topic == topic and msg.payload.decode("ascii") == "offline":
                self._status[topic] = "offline"
            elif msg.topic == topic and msg.payload.decode("ascii") == "online":
                self._status[topic] = "online"

    @staticmethod
    def _load_queue(measurement: str, time_field: datetime, payload: dict) -> None:
        """
        Unpacks the payload and assigns a new message with each item in the payload,
        this sets all messages in the packet with the same time and measurement field
        Then loads each packet into a globally accessible queue.
        """
        for key, value in payload.items():
            # We don't like a queue building up since it means our program isn't
            # handling the volume of data or a service is offline
            while THREADED_QUEUE.full():
                logging.error(f"Queue is full, sleeping for {QUEUE_WAIT_TIME} seconds")
                time.sleep(QUEUE_WAIT_TIME)
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

    def _decode_message(self, msg: MQTTMessage):
        """
        Handles all code around decoding raw bytestrings and loading the packets into a global queue
        :param msg: Takes in a raw bytestring from MQTT
        """
        # TODO Convert to new packet format
        fx_online = self._status["mate/fx-1/status"]
        mx_online = self._status["mate/mx-1/status"]
        dc_online = self._status["mate/dc-1/status"]
        if msg.topic == "mate/fx-1/stat/ts" and fx_online:
            self._fx_time = int(msg.payload.decode("ascii"))
            self._fx_time = datetime.fromtimestamp(self._fx_time)
            logging.debug(f"Received fx_time packet: {self._fx_time}")
        elif msg.topic == "mate/fx-1/stat/raw" and self._fx_time and fx_online:
            fx_payload = PyMateDecoder.fx_decoder(msg.payload)
            logging.debug("Loading fx_payload onto queue")
            self._load_queue(
                measurement="fx-1", time_field=self._fx_time, payload=fx_payload
            )

        elif msg.topic == "mate/mx-1/stat/ts" and mx_online:
            self._mx_time = int(msg.payload.decode("ascii"))
            self._mx_time = datetime.fromtimestamp(self._mx_time)
            logging.debug(f"Received mx_time packet: {self._mx_time}")
        elif msg.topic == "mate/mx-1/stat/raw" and self._mx_time and mx_online:
            mx_payload = PyMateDecoder.mx_decoder(msg.payload)
            logging.debug("Loading mx_payload onto queue")
            self._load_queue(
                measurement="mx-1", time_field=self._mx_time, payload=mx_payload
            )

        elif msg.topic == "mate/dc-1/stat/ts" and dc_online:
            self._dc_time = int(msg.payload.decode("ascii"))
            self._dc_time = datetime.fromtimestamp(self._dc_time)
            logging.debug(f"Received dc_time packet: {self._dc_time}")
        elif msg.topic == "mate/dc-1/stat/raw" and self._dc_time and dc_online:
            dc_payload = PyMateDecoder.dc_decoder(msg.payload)
            logging.debug("Loading dc_payload onto queue")
            self._load_queue(
                measurement="dc-1", time_field=self._dc_time, payload=dc_payload
            )

    def _on_message(self, _client, _userdata, msg: MQTTMessage) -> None:
        """
        Called everytime a message is received which it then decodes
        :param msg: Message to partition into categories and decode
        """
        try:
            self._check_status(msg=msg)
            if self._status["mate/status"] == "online":
                self._decode_message(msg=msg)
        except Exception as err:
            logging.exception(f"MQTT on_message raised an exception:{err}")

    def get_mqtt_client(self) -> Client:
        """
        Initial setup for the MQTT connector, connects to MQTT broker
        and failing to connect will exit the program
        """
        self._mqtt_client.username_pw_set(
            username=self._mqtt_secrets["mqtt_user"],
            password=self._mqtt_secrets["mqtt_token"],
        )
        self._mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
        self._mqtt_client.tls_insecure_set(True)

        self._mqtt_client.on_connect = self._on_connect
        self._mqtt_client.on_message = self._on_message
        self._mqtt_client.on_disconnect = self._on_disconnect
        self._mqtt_client.on_unsubscribe = self._on_unsubscribe
        self._mqtt_client.on_subscribe = self._on_subscribe

        self._mqtt_client.subscribe(self._mqtt_secrets["mqtt_topic"])
        self._mqtt_client.connect(
            host=self._mqtt_secrets["mqtt_host"],
            port=self._mqtt_secrets["mqtt_port"],
        )

        return self._mqtt_client
