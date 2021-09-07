"""
Classes file, contains both methods for the Influx database controller and MQTT subscriber
"""
from datetime import datetime
# Imports for Influx
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
# Imports for MQTT
import paho.mqtt.client as mqtt
from pymate.matenet.fx import FXStatusPacket as MateFX
from pymate.matenet.mx import MXStatusPacket as MateMX
# TODO: from pymate.matenet.dc import DCStatusPacket as mate_dc
import ssl
# Imports for logging
import logging
import sys


class InfluxController:
    """
    Class which creates a client to access and modify a connected database
    """
    influx_client = None
    influx_bucket = None
    influx_org = None

    def __init__(self, token, org, bucket, url):
        """
        :param token: Secret password to login to database with
        :param org: Organisation of the bucket to login to
        :param bucket: Database source
        :param url: Web address to connect to database
        """
        self.influx_token = token
        self.influx_org = org
        self.influx_bucket = bucket
        self.influx_url = url
        self.influx_client = InfluxDBClient
        # self.write_api = InfluxDBClient.write_api

    def startup(self):
        """
        Defines the initialization of the InfluxController, invoking the connection to the InfluxDB and write API
        """
        logging.info('Connecting to InfluxDB')
        self._create_client()
        # self._create_write_api()

    def _create_client(self):
        """
        :return: Client api which act commands on given database,
            on failure to connect it wil terminate the program
        """
        client = None
        try:
            client = InfluxDBClient(url=self.influx_url, token=self.influx_token, org=self.influx_org)
            logging.debug(f'Connected to bucket: {self.influx_bucket}')
        except Exception as err:
            logging.error(f'Failed to connect to bucket: {self.influx_bucket}', err)
            sys.exit()
        finally:
            self.influx_client = client


class MQTTDecoder:
    """
    Class which creates a client to connect to MQTT subscriber and decode the messages
    """

    def __init__(self, host, port, user, password, topic, influx_database=InfluxController):
        """
        :param host: Web url for the subscriber to listen on
        :param port: Port which the web server uses for MQTT
        :param user: Username to access MQTT server
        :param password: Password to access MQTT server
        :param influx_database: Database for the MQTTDecoder to write results to
        """
        self.fx_time = None
        self.mx_time = None
        self.dc_time = None
        self.dec_msg = None
        self.mqtt_host = host
        self.mqtt_port = port
        self.mqtt_topic = topic
        self.mqtt_user = user
        self.mqtt_password = password
        self.mqtt_client = mqtt.Client()
        self.influx_database = influx_database
        self.influx_bucket = influx_database.influx_bucket
        self.influx_org = influx_database.influx_org

    def startup(self):
        """
        Initial setup for the MQTT connector, connects to MQTT broker and failing to connect will exit the program
        """
        logging.info('Connecting to MQTT broker')
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.username_pw_set(self.mqtt_user, self.mqtt_password)
        self.mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.mqtt_client.tls_insecure_set(True)
        self._connect_mqtt()

    def _connect_mqtt(self):
        """
        Connects to MQTT broker, on failure to connect it wil terminate the program
        """
        try:
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port)
        except Exception as err:
            logging.error(f'Failed to connect to MQTT broker', err)
            sys.exit()

    def _on_connect(self, _client, _userdata, _flags, rc):
        """
        On first connection to MQTT broker this function will subscribe to the brokers topics
        :param _client: Unused
        :param _userdata: Unused
        :param _flags: Unused
        :param rc: Returned connection code
        """
        if rc == 0:
            self.mqtt_client.subscribe(self.mqtt_topic)
            logging.info(f'Connected to MQTT broker, returned code: {rc}')
        else:
            logging.error(f'Connection to MQTT broker refused, returned code: {rc}')

    def mqtt_runtime(self):
        """
        Continuous even loop which never returns, runs the main MQTT program
        """
        self.mqtt_client.loop_forever()

    def _database_add(self, msg_time, msg_dict, msg_type):
        """
        Adds message to Influx database
        :param msg_dict: Message for MQTTDecoder to input into the Influx Database in dictionary form
        :param msg_type: Type of header the msg carries, either FX, MX or DX
        # point_template = {'measurement': None, 'fields': {None, None}, 'time': None}
        """
        logging.debug(f'Creating database points from ({msg_time}, {msg_type})')
        write_client = self.influx_database.influx_client.write_api(write_options=SYNCHRONOUS)
        for key, value in msg_dict.items():
            point_template = {'measurement': msg_type, 'fields': {key: float(value)}, 'time': msg_time}
            logging.debug(f'Wrote point: {point_template}')
            write_client.write(self.influx_bucket, self.influx_org, point_template)

    @staticmethod
    def _fx_decoder(msg=b''):
        """
        Decoder for FX objects
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        fx_packet = MateFX.from_buffer(msg).__dict__
        return {key: value for (key, value) in fx_packet.items() if key != 'raw'}

    @staticmethod
    def _mx_decoder(msg=b''):
        """
        Decoder for MX objects
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        mx_packet = MateMX.from_buffer(msg).__dict__
        return {key: value for (key, value) in mx_packet.items() if key != 'raw'}

    # @staticmethod
    # def _dc_decoder(msg=b''):
    #     # TODO: Include DC Packets in decoder
    #     """
    #     Decoder for DC objects
    #     :param msg: Input message to decode
    #     :return: List of decoded objects
    #     """
    #     dc_packet = MateDC.from_buffer(msg).__dict__
    #     return {key: value for (key, value) in dc_packet.items() if key != 'raw'}

    def _on_message(self, _client, _userdata, msg):
        """
        Called everytime a message is received which it then decodes
        :param msg: Message to partition into categories and decode
        """
        # Time Packets
        if msg.topic == 'mate/fx-1/stat/ts':
            self.fx_time = int(msg.payload.decode('ascii'))
            self.fx_time = datetime.fromtimestamp(self.fx_time)
            logging.debug(f'Received fx_time packet: {self.fx_time}')
        elif msg.topic == 'mate/mx-1/stat/ts':
            self.mx_time = int(msg.payload.decode('ascii'))
            self.mx_time = datetime.fromtimestamp(self.mx_time)
            logging.debug(f'Received mx_time packet: {self.mx_time}')
        elif msg.topic == 'mate/dc-1/stat/ts':
            self.dc_time = int(msg.payload.decode('ascii'))
            self.dc_time = datetime.fromtimestamp(self.dc_time)
            logging.debug(f'Received dc_time packet: {self.dc_time}')
        # Data Packets
        elif msg.topic == 'mate/fx-1/stat/raw':
            if self.fx_time:
                fx_payload = self._fx_decoder(msg.payload)
                logging.debug(f'Received fx_payload packet: {fx_payload}')
                self._database_add(self.fx_time, fx_payload, 'fx-1')
        elif msg.topic == 'mate/mx-1/stat/raw':
            if self.mx_time:
                mx_payload = self._mx_decoder(msg.payload)
                logging.debug(f'Received mx_payload packet: {mx_payload}')
                self._database_add(self.mx_time, mx_payload, 'mx-1')
        # TODO: Include DC packets
        # elif msg.topic == 'mate/dc-1/stat/raw':
        #     if self.dc_time:
        #         dc_payload = self._dc_decoder(msg.payload)
        #         logging.debug(f'Received dc_payload packet: {dc_payload}')
        #         self._database_add(self.dc_time, dc_payload, 'dc-1')
