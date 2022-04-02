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

import paho.mqtt.client as mqtt
from pymate.matenet import DCStatusPacket, FXStatusPacket, MXStatusPacket
from config.consts import MAX_QUEUE_LENGTH, THREADED_QUEUE

from classes.custom_exceptions import MqttServerOfflineError
from classes.influx_classes import InfluxConnector


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
    def check_status(msg: mqtt.MQTTMessage) -> None:
        """
        Called everytime a status message is received and checks the status of the server
        :param msg: Recevied message from MQTT broker
        """
        status_topics = [
            "mate/status",
            "mate/mx-1/status",
            "mate/fx-1/status",
            "mate/dc-1/status",
        ]
        for status_group in status_topics:
            if msg.topic == status_group and msg.payload.decode("ascii") == "offline":
                logging.error(
                    f"A backend MQTT service isn't online, {status_group} = offline"
                )
                raise MqttServerOfflineError(
                    f"A backend MQTT service isn't online, {status_group} = offline"
                )


class MqttConnector:
    """
    Class which creates a client to connect to MQTT subscriber and decode the messages
    """

    def __init__(
        self,
        mqtt_secrets: dict,
        influx_connector: InfluxConnector = InfluxConnector,
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
        self._mqtt_secrets = mqtt_secrets
        self._mqtt_client = mqtt.Client()
        self._influx_connector = influx_connector

    def run_mqtt_listener(self) -> mqtt.Client:
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
            logging.error(f"Failed to connect to MQTT broker, {err}")
            raise err
        self._mqtt_client.on_connect = self._on_connect
        self._mqtt_client.on_disconnect = self._on_disconnect
        self._mqtt_client.on_message = self._on_message
        self._mqtt_client.loop_forever()

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
        if return_code == 0:
            self._mqtt_client.subscribe(self._mqtt_secrets["mqtt_topic"])
            logging.info(f"Connected to MQTT broker, returned code: {return_code}")
        else:
            logging.error(
                f"Connection to MQTT broker refused, returned code: {return_code}"
            )

    def _on_message(self, _client, _userdata, msg: mqtt.MQTTMessage) -> None:
        """
        Called everytime a message is received which it then decodes
        :param msg: Message to partition into categories and decode
        """
        PyMateDecoder.check_status(msg=msg)

        while THREADED_QUEUE.qsize() > MAX_QUEUE_LENGTH:
            logging.error("Queue is full, sleeping for 1 second")
            time.sleep(0.5)

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
            logging.debug(
                f"Received fx_payload packet and pushed onto queue: {fx_payload}"
            )
            THREADED_QUEUE.put(
                [self._fx_time, fx_payload, "fx-1", self._influx_connector]
            )
        elif msg.topic == "mate/mx-1/stat/raw" and self._mx_time:
            mx_payload = PyMateDecoder.mx_decoder(msg.payload)
            logging.debug(
                f"Received mx_payload packet and pushed onto queue: {mx_payload}"
            )
            THREADED_QUEUE.put(
                [self._mx_time, mx_payload, "mx-1", self._influx_connector]
            )
        elif msg.topic == "mate/dc-1/stat/raw" and self._dc_time:
            dc_payload = PyMateDecoder.dc_decoder(msg.payload)
            logging.debug(
                f"Received dc_payload packet and pushed onto queue: {dc_payload}"
            )
            THREADED_QUEUE.put(
                [self._dc_time, dc_payload, "dc-1", self._influx_connector]
            )
