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
from influxdb_client.client.write_api import SYNCHRONOUS
from pymate.matenet.fx import FXStatusPacket as MateFX
from pymate.matenet.mx import MXStatusPacket as MateMX

# Imports for Influx
from classes.influx_classes import InfluxController


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
    ):
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
        self._influx_bucket = influx_database.influx_bucket
        self._influx_org = influx_database.influx_org

    def startup(self):
        """
        Initial setup for the MQTT connector, connects to MQTT broker
        and failing to connect will exit the program
        """
        logging.info("Connecting to MQTT broker")
        self._mqtt_client.on_connect = self._on_connect
        self._mqtt_client.on_message = self._on_message
        self._mqtt_client.username_pw_set(self._mqtt_user, self._mqtt_token)
        self._mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
        self._mqtt_client.tls_insecure_set(True)
        self._connect_mqtt()

    def mqtt_runtime(self):
        """
        Continuous even loop which never returns, runs the classes MQTT program
        """
        self._mqtt_client.loop_forever()

    def _connect_mqtt(self):
        """
        Connects to MQTT broker, on failure to connect it wil terminate the program
        """
        try:
            self._mqtt_client.connect(self._mqtt_host, self._mqtt_port)
        except Exception as err:
            print(type(self._mqtt_host), type(self._mqtt_port))
            logging.error(f"Failed to connect to MQTT broker, {err}")
            raise err

    def _on_connect(self, _client, _userdata, _flags, return_code):
        """
        On first connection to MQTT broker this function will subscribe to the brokers topics
        :param _client: Unused
        :param _userdata: Unused
        :param _flags: Unused
        :param return_code: Returned connection code
        """
        if return_code == 0:
            self._mqtt_client.subscribe(self._mqtt_topic)
            logging.info(f"Connected to MQTT broker, returned code: {return_code}")
        else:
            logging.error(
                f"Connection to MQTT broker refused, returned code: {return_code}"
            )

    def _database_add(self, msg_time, msg_dict, msg_type):
        """
        Adds message to Influx database
        :param msg_dict: Message for MQTTDecoder to input into the Influx Database in dictionary
        :param msg_type: Type of header the msg carries, either FX, MX or DX
        # point_template = {"measurement": None, "fields": {None, None}, "time": None}
        """
        logging.debug(f"Creating database points from ({msg_time}, {msg_type})")
        write_client = self._influx_database.influx_client.write_api(
            write_options=SYNCHRONOUS
        )
        for key, value in msg_dict.items():
            # point_template = {
            #     "measurement": msg_type,
            #     "fields": {key: float(value)},
            #     "time": msg_time,
            # }
            # logging.debug(f"wrote point: {point_template}")
            # write_client.write(self._influx_bucket, self._influx_org, point_template)
            # Some strange error with inserting time from Points instead of the write_api
            point_template = {"measurement": msg_type, "fields": {key: float(value)}}
            logging.debug(f"Wrote point: {point_template} at {msg_time}")
            write_client.write(
                self._influx_bucket, self._influx_org, point_template, time=msg_time
            )

    @staticmethod
    def _fx_decoder(msg=b""):
        """
        Decoder for FX objects
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        fx_packet = MateFX.from_buffer(msg).__dict__
        return {key: value for (key, value) in fx_packet.items() if key != "raw"}

    @staticmethod
    def _mx_decoder(msg=b""):
        """
        Decoder for MX objects
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        mx_packet = MateMX.from_buffer(msg).__dict__
        return {key: value for (key, value) in mx_packet.items() if key != "raw"}

    # @staticmethod
    # def _dc_decoder(msg=b""):
    #     # TODO: Include DC Packets in decoder
    #     """
    #     Decoder for DC objects
    #     :param msg: Input message to decode
    #     :return: List of decoded objects
    #     """
    #     dc_packet = MateDC.from_buffer(msg).__dict__
    #     return {key: value for (key, value) in dc_packet.items() if key != "raw"}

    def _on_message(self, _client, _userdata, msg):
        """
        Called everytime a message is received which it then decodes
        :param msg: Message to partition into categories and decode
        """
        # Time Packets
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
                self._database_add(self._fx_time, fx_payload, "fx-1")
        elif msg.topic == "mate/mx-1/stat/raw":
            if self._mx_time:
                mx_payload = self._mx_decoder(msg.payload)
                logging.debug(f"Received mx_payload packet: {mx_payload}")
                self._database_add(self._mx_time, mx_payload, "mx-1")
        # TODO: Include DC packets
        # elif msg.topic == "mate/dc-1/stat/raw":
        #     if self.dc_time:
        #         dc_payload = self._dc_decoder(msg.payload)
        #         logging.debug(f"Received dc_payload packet: {dc_payload}"")
        #         self._database_add(self.dc_time, dc_payload, "dc-1")
