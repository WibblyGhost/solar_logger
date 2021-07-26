"""INSERT COMMENT"""
import paho.mqtt.client as mqtt
from pymate.matenet.fx import FXStatusPacket as mate_fx
from pymate.matenet.mx import MXStatusPacket as mate_mx
#TODO: from pymate.matenet.dc import DCStatusPacket as mate_dc
import secrets
import logging
import ssl

logger = logging.getLogger("mqtt")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

#class 



class MQTT_Decoder:
    """ENTER COMMENT"""

    def __init__(self) -> None:
        pass

    def main(self):
        self._main_client()

    def _on_connect(self, client, userdata, flags, rc):
        """Subscribes client to MQTT broker"""
        print("Connected with result code " + str(rc))
        # Connect to the mate tree
        client.subscribe("mate/#")

    def _decoder(self, topic="", msg=b""):
        """ENTER COMMENT
        arg1: String
        return: Tuple of decoded data"""
        fx_packet, dc_packet, mx_packet = None, None, None
        if(topic in 'mate/fx-1/stat/raw'):
            fx_packet = mate_fx.from_buffer(msg)

        #TODO: elif(topic == 'mate/dc-1/stat/raw'):
        #     print("%s, %s, %s" % (dc_packet, topic, msg))
        #     dc_packet = .from_buffer(msg)

        elif(topic == 'mate/mx-1/stat/raw'):
            mx_packet = mate_mx.from_buffer(msg)
        #TODO: return (fx_packet, dc_packet, mx_packet)
        return (fx_packet, mx_packet)

    def _on_message(self, client, userdata, msg):
        """Prints the message recieved from the broker"""
        dec_msg = self._decoder(msg.topic, msg.payload)
        if(dec_msg[0]):
            #fx_packet -> buy_power, chg_power, input_voltage, inv_power, output_voltage, sell_power, error_mode, warnings, operational_mode
            self._database_add(dec_msg[0])
            pass
        elif(dec_msg[1]):
            #mx_packet -> bat_voltage, kilowatt_hours, pv_voltage, bat_current, pb_current, errors, status
            self._database_add(dec_msg[1])
            pass
        #TODO: Include DC Packets

    def _database_add(self, msg):

        print()
        pass


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
