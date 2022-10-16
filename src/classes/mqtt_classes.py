"""
Classes file, contains methods for the MQTT subscriber which will receive packets
from the broker and input them into an Influx database.
Check the Influx query documentation for write syntax:
https://docs.influxdata.com/influxdb/v2.0/api-guide/client-libraries/python/#query-data-from-influxdb-with-python
"""

import logging
import ssl
import struct
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple

from paho.mqtt.client import Client, MQTTMessage
from pymate.matenet import DCStatusPacket, FXStatusPacket, MXStatusPacket

from src.classes.common_classes import QueuePackage, SecretStore
from src.helpers.consts import QUEUE_WAIT_TIME, THREADED_QUEUE, TIME_PACKET_SIZE


class PyMateDecoder:
    """
    Class which decodes bytestreams received from the MQTT broker
    """

    @staticmethod
    def detach_time(
        msg: bytearray, padding_at_end: int = 0
    ) -> Tuple[bytearray, bytearray]:
        """
        Splits the bytearray into two objects, time and payload
        """
        raw_time = msg[:TIME_PACKET_SIZE]
        msg_time = struct.unpack("i", raw_time)
        msg_payload = msg[TIME_PACKET_SIZE:-padding_at_end]
        return msg_time[0], msg_payload

    @staticmethod
    def dc_decoder(msg: bytearray) -> dict:
        """
        Decoder for DC objects
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        dc_packet = DCStatusPacket.from_buffer(msg).__dict__
        return {key: value for (key, value) in dc_packet.items() if key != "raw"}

    @staticmethod
    def fx_decoder(msg: bytearray) -> dict:
        """
        Decoder for FX objects
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        fx_packet = FXStatusPacket.from_buffer(msg).__dict__
        return {key: value for (key, value) in fx_packet.items() if key != "raw"}

    @staticmethod
    def mx_decoder(msg: bytearray) -> dict:
        """
        Decoder for MX objects
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        mx_packet = MXStatusPacket.from_buffer(msg).__dict__
        return {key: value for (key, value) in mx_packet.items() if key != "raw"}


@dataclass
class MqttTopics:
    """
    Object which is a model of all the different MQTT topics
    """

    mate_status = "mate/status"

    dc_name = "dc-1"
    dc_status = "mate/dc-1/status"
    dc_data = "mate/dc-1/dc-status"
    dc_raw = "mate/dc-1/stat/raw"
    dc_ts = "mate/dc-1/stat/ts"

    fx_name = "fx-1"
    fx_status = "mate/fx-1/status"
    fx_data = "mate/fx-1/fx-status"
    fx_raw = "mate/fx-1/stat/raw"
    fx_ts = "mate/fx-1/stat/ts"

    mx_name = "mx-1"
    mx_status = "mate/mx-1/status"
    mx_data = "mate/mx-1/mx-status"
    mx_raw = "mate/mx-1/stat/raw"
    mx_ts = "mate/mx-1/stat/ts"


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
            MqttTopics.mate_status: "offline",
            MqttTopics.dc_status: "offline",
            MqttTopics.fx_status: "offline",
            MqttTopics.mx_status: "offline",
        }
        self._dec_msg = None
        self._mqtt_secrets = secret_store.mqtt_secrets
        self._mqtt_client = Client()

    @staticmethod
    def _on_socket_open(_client, userdata, sock) -> None:
        """
        Debug function for logging socket openings from MQTT
        """
        logging.debug(f"Socket open debug args, {userdata}, {sock}")

    @staticmethod
    def _on_socket_close(_client, userdata, sock) -> None:
        """
        Debug function for logging socket closes from MQTT
        """
        logging.debug(f"Socket close debug args, {userdata}, {sock}")

    @staticmethod
    def _on_subscribe(_client, userdata, mid, granted_qos) -> None:
        """
        Logs when the MQTT client calls on_subscribe
        """
        logging.info("Subscribed to MQTT topic, _on_subscribe")
        logging.info(f"MQTT topic returns QoS level of {granted_qos}")
        logging.debug(f"Subscribe debug args, {userdata}, {mid}, {granted_qos}")

    @staticmethod
    def _on_unsubscribe(_client, userdata, mid) -> None:
        """
        Logs when MQTT calls on_unsubscribe
        """
        logging.info("Unsubscribed from MQTT topic, _on_unsubscribe")
        logging.debug(f"Unsubscribe debug args, {userdata}, {mid}")

    def _on_connect(self, _client, userdata, flags, return_code) -> None:
        """
        Logs when MQTT calls on_connect
        The value of rc indicates success or not
        """
        return_codes = {
            0: "Connection successful",
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorized",
        }
        if return_code == 0:
            logging.info("Connecting to MQTT broker, _on_connect")
            topic = f"{self._mqtt_secrets['mqtt_topic']}"
            self._mqtt_client.subscribe(topic=topic)
        else:
            logging.error(
                f"Couldn't connect to MQTT broker returned code: {return_code}\n"
                f"{return_codes[return_code]}"
            )
            logging.debug(f"Connect debug args, {userdata}, {flags}, {return_code}")

    @staticmethod
    def _on_disconnect(_client, userdata, return_code) -> None:
        """
        Logs when MQTT calls on_disconnect
        """
        logging.warning("Disconnected from MQTT broker, _on_disconnect")
        logging.debug(f"Disconnect debug args, {userdata}, {return_code}")

    def _check_status(self, msg: MQTTMessage) -> None:
        """
        Called everytime a status message is received and checks the status of the server
        :param msg: Received message from MQTT broker
        """
        for topic, _ in self._status.items():
            if msg.topic == topic and msg.payload.decode("ascii") == "offline":
                self._status[topic] = "offline"
                logging.warning(f"{msg.topic} has gone offline")
            elif msg.topic == topic and msg.payload.decode("ascii") == "online":
                self._status[topic] = "online"
                logging.info(f"{msg.topic} is now online")

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
        logging.info(
            f"Pushed items onto queue, queue now has {THREADED_QUEUE.qsize()} items"
        )

    def _decode_message(self, msg: MQTTMessage) -> None:
        """
        Handles all code around decoding raw bytestrings and loading the packets into a global queue
        :param msg: Takes in a raw bytestring from MQTT
        """
        dc_online = self._status[MqttTopics.dc_status]
        fx_online = self._status[MqttTopics.fx_status]
        mx_online = self._status[MqttTopics.mx_status]

        if msg.topic == MqttTopics.dc_data and dc_online == "online":
            logging.info(f"Received {MqttTopics.dc_name} data packet")
            logging.debug(f"{MqttTopics.dc_name} payload: {msg.payload}")
            # NOTE: Due to errors in our packet packing, it introduces a random buffer at the end
            padding_at_end = 2
            msg_time, msg_payload = PyMateDecoder.detach_time(
                msg=msg.payload, padding_at_end=padding_at_end
            )
            dc_time = datetime.fromtimestamp(msg_time)
            dc_payload = PyMateDecoder.dc_decoder(msg_payload)
            logging.debug(
                f"Decoded and split {MqttTopics.dc_name} payload: {dc_payload} at {dc_time}"
            )
            self._load_queue(
                measurement=MqttTopics.dc_name, time_field=dc_time, payload=dc_payload
            )

        if msg.topic == MqttTopics.fx_data and fx_online == "online":
            logging.info(f"Received {MqttTopics.fx_name} data packet")
            logging.debug(f"{MqttTopics.fx_name} payload: {msg.payload}")
            # NOTE: Due to errors in our packet packing, it introduces a random buffer at the end
            padding_at_end = 3
            msg_time, msg_payload = PyMateDecoder.detach_time(
                msg=msg.payload, padding_at_end=padding_at_end
            )
            fx_time = datetime.fromtimestamp(msg_time)
            fx_payload = PyMateDecoder.fx_decoder(msg_payload)
            logging.debug(
                f"Decoded and split {MqttTopics.fx_name} payload: {fx_payload} at {fx_time}"
            )
            self._load_queue(
                measurement=MqttTopics.fx_name, time_field=fx_time, payload=fx_payload
            )

        if msg.topic == MqttTopics.mx_data and mx_online == "online":
            logging.info(f"Received {MqttTopics.mx_name} data packet")
            logging.debug(f"{MqttTopics.mx_name} payload: {msg.payload}")
            # NOTE: Due to errors in our packet packing, it introduces a random buffer at the end
            padding_at_end = 3
            msg_time, msg_payload = PyMateDecoder.detach_time(
                msg=msg.payload, padding_at_end=padding_at_end
            )
            mx_time = datetime.fromtimestamp(msg_time)
            mx_payload = PyMateDecoder.mx_decoder(msg_payload)
            logging.debug(
                f"Decoded and split {MqttTopics.mx_name} payload: {mx_payload} at {mx_time}"
            )
            self._load_queue(
                measurement=MqttTopics.mx_name, time_field=mx_time, payload=mx_payload
            )

    def _on_message(self, _client, _userdata, msg: MQTTMessage) -> None:
        """
        Called everytime a message is received which it then decodes
        :param msg: Message to partition into categories and decode
        """
        try:
            self._check_status(msg=msg)
            if self._status[MqttTopics.mate_status] == "online":
                self._decode_message(msg=msg)
            else:
                logging.warning(f"{MqttTopics.mate_status} is offline")
        except Exception:
            logging.exception("MQTT on_message raised an exception:")

    def get_mqtt_client(self) -> Client:
        """
        Initial setup for the MQTT connector, connects to MQTT broker
        and failing to connect will exit the program
        """
        self._mqtt_client.username_pw_set(
            username=self._mqtt_secrets["mqtt_user"],
            password=self._mqtt_secrets["mqtt_token"],
        )

        self._mqtt_client.on_connect = self._on_connect
        self._mqtt_client.on_message = self._on_message
        self._mqtt_client.on_disconnect = self._on_disconnect
        self._mqtt_client.on_unsubscribe = self._on_unsubscribe
        self._mqtt_client.on_subscribe = self._on_subscribe
        self._mqtt_client.on_socket_open = self._on_socket_open
        self._mqtt_client.on_socket_close = self._on_socket_close

        self._mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
        self._mqtt_client.tls_insecure_set(True)

        _ = self._mqtt_client.connect(
            host=self._mqtt_secrets["mqtt_host"],
            port=self._mqtt_secrets["mqtt_port"],
        )

        return self._mqtt_client
