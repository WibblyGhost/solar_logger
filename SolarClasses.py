"""
Classes file, contains both methods for the Influx database controller and MQTT subscriber
"""
from datetime import datetime
# Imports for Influx
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS, WritePrecision
# Imports for MQTT
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
    write_api = None
    bucket = None

    def __init__(self, token, org, bucket, url, bucket_id):
        """
        :param token: Secret password to login to database with
        :param org: Organisation of the bucket to login to
        :param bucket: Database source
        :param url: Web address to connect to database
        """
        self.token = token
        self.org = org
        self.bucket = bucket
        self.url = url
        self.bucket_id = bucket_id
        self.influx_client = InfluxDBClient
        self.write_api = InfluxDBClient.write_api

    def startup(self):
        """
        Defines the initialization of the InfluxController, invoking the connection to the InfluxDB and write API
        """
        logging.debug("Connecting to InfluxDB")
        self._create_client()
        self._create_write_api()

    def _create_client(self):
        """
        :return: Client api which act commands on given database,
            on failure to connect it wil terminate the program
        """
        client = None
        try:
            client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            logging.debug(f"Connected to bucket: {self.bucket}")
        except Exception as err:
            logging.error(f"Failed to connect to bucket: {self.bucket}", err)
            sys.exit()
        finally:
            self.influx_client = client

    def _create_write_api(self):
        """
        :return: Write api which act commands on given database,
            on failure to connect it wil terminate the program
        """
        api = None
        try:
            api = self.influx_client.write_api(write_options=SYNCHRONOUS)
            logging.debug("Created bucket write api")
        except Exception as err:
            logging.error(f"Failed to create write api on bucket: {self.bucket}", err)
            sys.exit()
        finally:
            self.write_api = api


class MQTTDecoder:
    """
    Class which creates a client to connect to MQTT subscriber and decode the messages
    """

    def __init__(self, host, port, user, password, client, topic, influx_database=InfluxController):
        """
        :param host: Web url for the subscriber to listen on
        :param port: Port which the web server uses for MQTT
        :param user: Username to access MQTT server
        :param password: Password to access MQTT server
        :param client: MQTT client that the class uses to run on
        :param influx_database: Database for the MQTTDecoder to write results to
        """
        self.fx_time = None
        self.mx_time = None
        self.dec_msg = None
        self.host = host
        self.port = port
        self.topic = topic
        self.user = user
        self.password = password
        self.mqtt_client = client
        self.influx_database = influx_database

    def startup(self):
        """
        Initial setup for the MQTT connector, connects to MQTT broker and failing to connect will exit the program
        """
        logging.debug("Connecting to MQTT broker")
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.username_pw_set(self.user, self.password)
        self.mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.mqtt_client.tls_insecure_set(True)
        self._connect_mqtt()

    def _connect_mqtt(self):
        """
        Connects to MQTT broker, on failure to connect it wil terminate the program
        """
        try:
            self.mqtt_client.connect(self.host, self.port)
        except Exception as err:
            logging.error(f"Failed to connect to MQTT broker", err)
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
            self.mqtt_client.subscribe(self.topic)
            logging.debug(f"Connected to MQTT broker, returned code: {rc}")
        else:
            logging.error(f"Connection to MQTT broker refused, returned code: {rc}")

    def mqtt_runtime(self):
        """
        Continuous even loop which never returns, runs the main MQTT program
        """
        self.mqtt_client.loop_forever()

    def _database_add(self, msg, msg_type):
        """
        Adds message to Influx database
        :param msg: Message for MQTTDecoder to input into the Influx Database
        :param msg_type: Type of header the msg carries, either FX, MX or DX
        """
        logging.info(msg)
        utc_time = None
        for item in msg:
            if item[0] == "utc_time":
                # TODO: Fix timestamp, breaking the write function
                utc_time = datetime.strptime(item[1], "%Y-%m-%d %H:%M:%S")
                pass
            else:
                # point = Point(msg_type).field(str(item[0]), float(item[1])).time(utc_time)
                point = Point(msg_type).field(str(item[0]), float(item[1]))
                logging.info(point.to_line_protocol())
                try:
                    self.influx_database.write_api.write(bucket=self.influx_database.bucket, record=point)
                except Exception as err:
                    logging.error(f"Failed to write {point.to_line_protocol()} to {self.influx_database.bucket}", err)

    @staticmethod
    def _fx_decoder(msg=b""):
        """
        Decoder for FX objects
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        key_list = []
        obj_properties = ["buy_power", "chg_power", "input_voltage", "inv_power", "output_voltage", "sell_power",
                          "error_mode", "warnings", "operational_mode"]
        fx_packet = MateFX.from_buffer(msg)
        for key, value in fx_packet.__dict__.items():
            if key in obj_properties:
                key_list.append((key, value))
        return key_list

    @staticmethod
    def _mx_decoder(msg=b""):
        """
        Decoder for MX objects
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        key_list = []
        obj_properties = ["bat_voltage", "kilowatt_hours", "pv_voltage", "bat_current", "pb_current", "errors",
                          "status"]
        mx_packet = MateMX.from_buffer(msg)
        for key, value in mx_packet.__dict__.items():
            if key in obj_properties:
                key_list.append((key, value))
        return key_list

    # @staticmethod
    # def _dc_decoder(msg=b""):
    #     # TODO: Include DC Packets in decoder
    #     """
    #     Decoder for DC objects
    #     :param msg: Input message to decode
    #     :return: List of decoded objects
    #     """
    #     key_list = []
    #     obj_properties = []
    #     dc_packet = MateDC.from_buffer(msg)
    #     for key, value in dc_packet.__dict__.items():
    #         if key in obj_properties:
    #             key_list.append((key, value))
    #     return key_list

    def _on_message(self, _client, _userdata, msg):
        """
        Called everytime a message is received which it then decodes
        :param msg: Message to partition into categories and decode
        """
        # FX Packets
        if msg.topic == "mate/fx-1/stat/ts":
            self.fx_time = int(msg.payload.decode("ascii"))
            self.fx_time = datetime.fromtimestamp(self.fx_time).strftime('%Y-%m-%d %H:%M:%S')
        elif msg.topic == "mate/fx-1/stat/raw":
            if self.fx_time is None:
                return
            dec_msg = self._fx_decoder(msg.payload)
            dec_msg.insert(0, ("utc_time", self.fx_time))
            self._database_add(dec_msg, "fx-1")
        # MX Packets
        elif msg.topic == "mate/mx-1/stat/ts":
            self.mx_time = int(msg.payload.decode("ascii"))
            self.mx_time = datetime.fromtimestamp(self.mx_time).strftime('%Y-%m-%d %H:%M:%S')
        elif msg.topic == 'mate/mx-1/stat/raw':
            if self.mx_time is None:
                return
            dec_msg = self._mx_decoder(msg.payload)
            dec_msg.insert(0, ("utc_time", self.mx_time))
            self._database_add(dec_msg, "mx-1")
        # DC Packets
        # elif msg.topic == "mate/dc-1/stat/ts":
        #     self.dc_time = int(msg.payload.decode("ascii"))
        #     self.dc_time = datetime.fromtimestamp(self.dc_time).strftime('%Y-%m-%d %H:%M:%S')
        # elif msg.topic == 'mate/dc-1/stat/raw':
        #     if self.mx_time is None:
        #         return
        #     dec_msg = self._dc_decoder(msg.payload)
        #     dec_msg.insert(0, ("utc_time", self.dc_time))
        #     self._database_add(dec_msg)
