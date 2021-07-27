"""INSERT COMMENT"""
import paho.mqtt.client as mqtt
from pymate.matenet.fx import FXStatusPacket as mate_fx
from pymate.matenet.mx import MXStatusPacket as mate_mx
#TODO: from pymate.matenet.dc import DCStatusPacket as mate_dc
import secrets
import logging
import ssl
from datetime import datetime

logger = logging.getLogger("mqtt")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

#class 



class MQTT_Decoder:
    """ENTER COMMENT"""

    def __init__(self) -> None:
        self.fx_time = None
        self.mx_time = None
        self.dec_msg = None

    def main(self):
        self._main_client()

    def _on_connect(self, client, userdata, flags, rc):
        """Subscribes client to MQTT broker"""
        print("Connected with result code " + str(rc))
        # Connect to the mate tree
        client.subscribe("mate/#")

    def _fx_decoder(self, msg=b""):
        """ENTER COMMENT"""
        key_list = []
        obj_properties = ["buy_power", "chg_power", "input_voltage", "inv_power", "output_voltage", "sell_power", "error_mode", "warnings", "operational_mode"]
        fx_packet = mate_fx.from_buffer(msg)
        for key, value in fx_packet.__dict__.items():
            if key in obj_properties:
                key_list.append((key, value))
        return key_list

    def _mx_decoder(self, msg=b""):
        """ENTER COMMENT"""
        key_list = []
        obj_properties = ["bat_voltage", "kilowatt_hours", "pv_voltage", "bat_current", "pb_current", "errors", "status"]
        mx_packet = mate_mx.from_buffer(msg)
        for key, value in mx_packet.__dict__.items():
            if key in obj_properties:
                key_list.append((key, value))
        return key_list

    def _database_add(self, msg):
        # Graphite DB, Promethius DB, Influx DB
        print(msg)
        pass

    def _on_message(self, client, userdata, msg):
        """Prints the message recieved from the broker"""
        if(msg.topic == "mate/fx-1/stat/ts") :
            self.fx_time = int(msg.payload.decode("ascii"))
            self.fx_time = datetime.fromtimestamp(self.fx_time).strftime('%Y-%m-%d %H:%M:%S')
        elif(msg.topic == "mate/fx-1/stat/raw"):
            if(self.fx_time == None): 
                return
            dec_msg = self._fx_decoder(msg.payload)
            dec_msg.insert(0, self.fx_time)
            self._database_add(dec_msg)

        elif(msg.topic == "mate/mx-1/stat/ts"):
            self.mx_time = int(msg.payload.decode("ascii"))
            self.mx_time = datetime.fromtimestamp(self.mx_time).strftime('%Y-%m-%d %H:%M:%S')
        elif(msg.topic == "mate/mx-1/stat/raw"):
            if(self.mx_time == None): 
                return
            dec_msg = self._mx_decoder(msg.payload)
            dec_msg.insert(0, self.mx_time)
            self._database_add(dec_msg)

        #TODO: Include DC Packets


    def _main_client(self):
        """Connects to broker machine and subscribes"""
        client = mqtt.Client()
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.enable_logger(logger=logger)
        # Setting user info & connect to MQTT
        client.username_pw_set(secrets.USER, secrets.PASSWORD)
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.tls_insecure_set(True)
        client.connect(secrets.URL, 8883, 60)
        client.loop_forever()


mq = MQTT_Decoder()
mq.main()
