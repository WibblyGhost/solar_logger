from datetime import datetime
# Imports for Influx
from influxdb_client import InfluxDBClient, Point
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

    def __init__(self, token, org, bucket, url, client=None):
        """
        :param token: Secret password to login to database with
        :param org: Organisation of the bucket to login to
        :param bucket: Database source
        :param url: Web address to connect to database
        :param client: Existing database connection, default is None
        """
        self.token = token
        self.org = org
        self.bucket = bucket
        self.url = url
        self.client = client

        self.write_api = None

    def __str__(self):
        # TODO: Add a string representation of database, display last 10 entries
        pass

    def connect_db(self):
        """
        :return: Success of database connection
        """
        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            print(f"Connected to bucket: {self.bucket}")

            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            return True
        except ConnectionError(f"Failed to connect to bucket: {self.bucket}"):
            return False

    # def query_db(self, query):
    #     """
    #     :param query: Query string to send to database
    #     :return q_result: Result of the query
    #     """
    #     try:
    #         tables = self.client.query_api().query(query, self.org)
    #         # tables = client.query_api().query(query, org=org)
    #         pass
    #     except:
    #         return None

    @staticmethod
    def create_point(measurement, field_title, field_value, tag_group):
        """
        # TODO: Docstrings
        :param measurement:
        :param field_title:
        :param field_value:
        :param tag_group:
        :return:
        """
        return Point(measurement)\
            .field(field_title, field_value)\
            .tag("group", tag_group)

    def write_point(self, db_point):
        """
        # TODO: Docstrings
        :param db_point:
        :return: Success of database write
        """
        try:
            # TODO: Insert datapoints
            stats = [["voltage", 2.3, "volts"], ["current", 1.8, "amps"]]
            for title, value, measurement in stats:
                p = Point(measurement) \
                    .field(title, value) \
                    .tag("group", "fx-1")
                self.write_api.write(bucket=self.bucket, org=self.org, record=p)
            print(f"Wrote point ({db_point} to bucket: {self.bucket}")
            return True
        except ConnectionError(f"Failed to write point to bucket: {self.bucket}"):
            return False


class MQTTDecoder:
    """
    Class which creates a client to connect to MQTT subscriber and decode the messages
    """
    # TODO: Fix MQTT class

    def __init__(self, host, port, user, password, client, topic, database=InfluxController):
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

    def _on_connect(self, _client, _userdata, _flags, rc):
        """
        Subscribes client to MQTT broker
        """
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

    # # @staticmethod
    # def _database_format(self, msg):
    #     """
    #     # TODO: Docstrings
    #     :param msg:
    #     :return:
    #     """
    #     # TODO: Convert the packets received into point format for the database to add
    #     # FX Data Packets
    #     # fx = [('utc_time', '2021-08-22 20:00:30'), ('warnings', 0), ('error_mode', 0), ('operational_mode', 0),
    #     # ('output_voltage', 4.0V), ('input_voltage', 6.0V)]
    #     fx = [('utc_time', '2021-08-22 20:00:30'), ('warnings', 0), ('error_mode', 0), ('operational_mode', 0),
    #           ('output_voltage', 4.0), ('input_voltage', 6.0)]
    #     # MX Data Packets
    #     # mx = [('utc_time', '2021-08-22 20:01:21'), ('kilowatt_hours', 1.2kWh), ('bat_current', 0A),
    #     # ('pv_voltage', 15.0V), ('bat_voltage', 25.7V), ('status', 0), ('errors', 0)]
    #     mx = [('utc_time', '2021-08-22 20:01:21'), ('kilowatt_hours', 1.2), ('bat_current', 0), ('pv_voltage', 15.0),
    #           ('bat_voltage', 25.7), ('status', 0), ('errors', 0)]
    #     # Cast all values to floats
    #
    #     utc_time = None
    #     for item in fx:
    #         if item[0] == "utc_time":
    #             utc_time = datetime.strptime(item[1], "%Y-%m-%d %H:%M:%S")
    #     # TODO: self.database.create_point()

    @staticmethod
    def _database_add(msg):
        """
        :param msg: Message for MQTTDecoder to input into the Influx Database
        :return: Never returns
        """
        # TODO: Insert into database
        print(msg)

        for item in msg:
            if item[0] == "utc_time":
                print(type(item[1]))
                print("<------------------->")
        pass

    @staticmethod
    def _fx_decoder(msg=b""):
        """
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
        :param msg: Message to partition into categories and decode
        :return: Never returns
        """
        # FX Packets
        if msg.topic == "mate/fx-1/stat/ts":
            self.fx_time = int(msg.payload.decode("ascii"))
            self.fx_time = datetime.fromtimestamp(self.fx_time).strftime('%Y-%m-%d %H:%M:%S')
        elif msg.topic == "mate/fx-1/stat/raw":
            if self.fx_time is None:
                # TODO: Does this need to apply to ts as well
                return
            dec_msg = self._fx_decoder(msg.payload)
            dec_msg.insert(0, ("utc_time", self.fx_time))
            self._database_add(dec_msg)
        # MX Packets
        elif msg.topic == "mate/mx-1/stat/ts":
            self.mx_time = int(msg.payload.decode("ascii"))
            self.mx_time = datetime.fromtimestamp(self.mx_time).strftime('%Y-%m-%d %H:%M:%S')
        elif msg.topic == 'mate/mx-1/stat/raw':
            if self.mx_time is None:
                return
            dec_msg = self._mx_decoder(msg.payload)
            dec_msg.insert(0, ("utc_time", self.mx_time))
            self._database_add(dec_msg)
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
