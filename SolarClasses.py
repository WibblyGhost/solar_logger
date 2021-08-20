from datetime import datetime
# Imports for Influx
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
# Imports for MQTT
from pymate.matenet.fx import FXStatusPacket as MateFX
from pymate.matenet.mx import MXStatusPacket as MateMX
# TODO: from pymate.matenet.dc import DCStatusPacket as mate_dc
import ssl


class InfluxController:
    """
    Class which creates a client to access and modify a connected database
    """

    def __init__(self, token, org, bucket, bucket_id, host, client=None):
        """
        :param token: Secret password to login to database with
        :param org: Organisation of the bucket to login to
        :param bucket: Database source
        :param bucket_id: Identification of bucket
        :param host: Web address to connect to database
        :param client: Existing database connection, default is None
        """
        self.token = token
        self.org = org
        self.bucket = bucket
        self.bucket_id = bucket_id
        self.host = host
        self.client = client

    def connect_db(self):
        """
        :return: Success of database connection
        """
        try:
            self.client = InfluxDBClient(url=self.host, token=self.token)
            # TODO: Print a connected message
            # print("Connected to {self.bucket}")
            return True
        except:
            return False

    def query_db(self, query):
        """
        :param query: Query string to send to database
        :return q_result: Result of the query
        """
        try:
            tables = self.client.query_api().query(query, self.org)
            # tables = client.query_api().query(query, org=org)
            pass
        except:
            return None

    def write_db(self, db_point):
        """
        :param db_point:
        :return: Success of database write
        """
        try:
            write_api = self.client.write_api(write_options=SYNCHRONOUS)

            point = Point("mem") \
                .field("used_allocation", 200) \
                .time(datetime.utcnow(), WritePrecision.NS)

            write_api.write(self.bucket, self.org, point)
            return True
        except:
            return False


class MQTTDecoder:
    """
    Class which creates a client to connect to MQTT subscriber and decode the messages
    """
    # TODO: Fix MQTT class

    def __init__(self, host, port, user, password, client, topic, database):
        """
        :param host: Web url for the subscriber to listen on
        :param port: Port which the web server uses for MQTT
        :param user: Username to access MQTT server
        :param password: Password to access MQTT server
        :param client: MQTT client that the class uses to run on
        :param database: Database for the MQTTDecoder to write results to
        """
        self.fx_time = None
        self.mx_time = None
        self.dec_msg = None
        self.host = host
        self.port = port
        self.topic = topic
        self.user = user
        self.password = password
        self.client = client
        self.database = database

    def setup_mqtt(self):
        """
        Initial setup for the MQTT connector
        """
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.username_pw_set(self.user, self.password)
        self.client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.client.tls_insecure_set(True)
        self.client.connect(self.host, self.port)

    def _on_connect(self, client, userdata, flags, rc):
        """Subscribes client to MQTT broker"""
        if rc == 0:
            print("Connected to MQTT Broker")
        else:
            print("Failed to connect, return code %d\n, rc")
        # Connect to the mate tree
        self.client.subscribe(self.topic)

    def mqtt_runtime(self):
        """
        Continuous even loop which never returns, runs the main MQTT program
        """
        self.client.loop_forever()

    @staticmethod
    def _fx_decoder(msg=b""):
        """
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        key_list = []
        obj_properties = ["buy_power", "chg_power", "input_voltage", "inv_power", "output_voltage", "sell_power", "error_mode", "warnings", "operational_mode"]
        fx_packet = MateFX.from_buffer(msg)
        for key, value in fx_packet.__dict__.items():
            if key in obj_properties:
                key_list.append((key, value))
        return key_list

    @staticmethod
    def _mx_decoder(msg=b""):
        """
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        key_list = []
        obj_properties = ["bat_voltage", "kilowatt_hours", "pv_voltage", "bat_current", "pb_current", "errors", "status"]
        mx_packet = MateMX.from_buffer(msg)
        for key, value in mx_packet.__dict__.items():
            if key in obj_properties:
                key_list.append((key, value))
        return key_list

    @staticmethod
    def _dc_decoder(msg=b""):
        # TODO: Include DC Packets in decoder
        """
        :param msg: Input message to decode
        :return: List of decoded objects
        """
        pass

    @staticmethod
    def _database_add(msg):
        """
        :param msg: Message for MQTTDecoder to input into the Influx Database
        :return: Never returns
        """
        # TODO: Insert into database
        print(msg)
        pass

    def _on_message(self, client, userdata, msg):
        """
        :param msg: Message to partition into categories and decode
        :return: Never returns
        """
        if msg.topic == "mate/fx-1/stat/ts":
            self.fx_time = int(msg.payload.decode("ascii"))
            self.fx_time = datetime.fromtimestamp(self.fx_time).strftime('%Y-%m-%d %H:%M:%S')
        elif msg.topic == "mate/fx-1/stat/raw":
            if self.fx_time is None:
                # TODO: Does this need to apply to ts as well
                return
            dec_msg = self._fx_decoder(msg.payload)
            dec_msg.insert(0, self.fx_time)
            self._database_add(dec_msg)

        elif msg.topic == "mate/mx-1/stat/ts":
            self.mx_time = int(msg.payload.decode("ascii"))
            self.mx_time = datetime.fromtimestamp(self.mx_time).strftime('%Y-%m-%d %H:%M:%S')
        elif msg.topic == 'mate/mx-1/stat/raw':
            if self.mx_time is None:
                return
            dec_msg = self._mx_decoder(msg.payload)
            dec_msg.insert(0, self.mx_time)
            self._database_add(dec_msg)
