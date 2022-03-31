"""
Classes file, contains methods for the MQTT subscriber which will receive packets
from the broker and input them into an Influx database.
Check the Influx query documentation for write syntax:
https://docs.influxdata.com/influxdb/v2.0/api-guide/client-libraries/python/#query-data-from-influxdb-with-python
"""

import logging
import ssl
from datetime import datetime

# Imports for MQTT
import paho.mqtt.client as mqtt
from pymate.matenet import FXStatusPacket, MXStatusPacket, DCStatusPacket

# Imports for Influx
from classes.influx_classes import InfluxController, influx_db_write_points


class MQTTDecoder:
    """
    Class which creates a client to connect to MQTT subscriber and decode the messages
    """

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        token: str,
        topic: str,
        influx_database: InfluxController = InfluxController,
    ) -> None:
        """
        :param host: Web url for the subscriber to listen on
        :param port: Port which the web server uses for MQTT
        :param user: Username to access MQTT server
        :param token: Token to access MQTT server
        :param influx_database: Database for the MQTTDecoder to write results to
        """
        self._fx_time = None
        self._mx_time = None
        self._dc_time = None
        self._dec_msg = None
        self._mqtt_host = host
        self._mqtt_port = port
        self._mqtt_topic = topic
        self._mqtt_user = user
        self._mqtt_token = token
        self._mqtt_client = mqtt.Client()
        self._influx_database = influx_database

    def startup(self) -> None:
        """
        Initial setup for the MQTT connector, connects to MQTT broker
        and failing to connect will exit the program
        """
        logging.info("Connecting to MQTT broker")
        self._mqtt_client.on_connect = self._on_connect
        self._mqtt_client.on_message = self._on_message
        self._mqtt_client.username_pw_set(
            username=self._mqtt_user, password=self._mqtt_token
        )
        self._mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
        self._mqtt_client.tls_insecure_set(True)
        self._connect_mqtt()

    def start_mqtt_service(self) -> None:
        """
        Continuous even loop which never returns, runs the classes MQTT program
        """
        self._mqtt_client.loop_forever()

    def _connect_mqtt(self) -> None:
        """
        Connects to MQTT broker, on failure to connect it wil terminate the program
        """
        try:
            self._mqtt_client.connect(host=self._mqtt_host, port=self._mqtt_port)
        except Exception as err:
            print(type(self._mqtt_host), type(self._mqtt_port))
            logging.error(f"Failed to connect to MQTT broker, {err}")
            raise err

    def _on_connect(self, _client, _userdata, _flags, return_code: int) -> None:
        """
        On first connection to MQTT broker this function will subscribe to the brokers topics
        :param _client: Unused
        :param _userdata: Unused
        :param _flags: Unused
        :param return_code: Returned connection code
        """
        if return_code == 0:
            # self._mqtt_client.subscribe(self._mqtt_topic)
            self._mqtt_client.subscribe("mate/#")
            logging.info(f"Connected to MQTT broker, returned code: {return_code}")
        else:
            logging.error(
                f"Connection to MQTT broker refused, returned code: {return_code}"
            )

    @staticmethod
    def _fx_decoder(msg: bytearray = b"") -> dict:
        """
        Decoder for FX objects
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        fx_packet = FXStatusPacket.from_buffer(msg).__dict__
        return {key: value for (key, value) in fx_packet.items() if key != "raw"}

    @staticmethod
    def _mx_decoder(msg: bytearray = b"") -> dict:
        """
        Decoder for MX objects
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        mx_packet = MXStatusPacket.from_buffer(msg).__dict__
        return {key: value for (key, value) in mx_packet.items() if key != "raw"}

    @staticmethod
    def _dc_decoder(msg: bytearray = b"") -> dict:
        """
        Decoder for DC objects
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        dc_packet = DCStatusPacket.from_buffer(msg).__dict__
        return {key: value for (key, value) in dc_packet.items() if key != "raw"}

    def _on_message(self, _client, _userdata, msg: str) -> None:
        """
        Called everytime a message is received which it then decodes
        :param msg: Message to partition into categories and decode
        """
        # Time Packets
        logging.debug(f"Ran on message {msg.payload.decode('ascii')}")
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
        # Data Packets
        elif msg.topic == "mate/fx-1/stat/raw":
            if self._fx_time:
                fx_payload = self._fx_decoder(msg.payload)
                logging.debug(f"Received fx_payload packet: {fx_payload}")
                influx_db_write_points(
                    msg_time=self._fx_time,
                    msg_payload=fx_payload,
                    msg_type="fx-1",
                    influx_database=self._influx_database,
                )
        elif msg.topic == "mate/mx-1/stat/raw":
            if self._mx_time:
                mx_payload = self._mx_decoder(msg.payload)
                logging.debug(f"Received mx_payload packet: {mx_payload}")
                influx_db_write_points(
                    msg_time=self._mx_time,
                    msg_payload=mx_payload,
                    msg_type="mx-1",
                    influx_database=self._influx_database,
                )
        elif msg.topic == "mate/dc-1/stat/raw":
            if self._dc_time:
                dc_payload = self._dc_decoder(msg.payload)
                logging.debug(dc_payload)
                logging.debug(f"Received dc_payload packet: {dc_payload}")
                influx_db_write_points(
                    msg_time=self._dc_time,
                    msg_payload=dc_payload,
                    msg_type="dc-1",
                    influx_database=self._influx_database,
                )
        logging.debug("Ran on message END")