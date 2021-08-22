"""
Main program which initialises and runs both the MQTT and InfluxDB controllers
"""

import Secrets
from Solar_Classes import MQTTDecoder, InfluxController
import paho.mqtt.client as mqtt


# import logging
# def enable_logging():
#     logger = logging.getLogger("mqtt")
#     logger.setLevel(logging.DEBUG)
#     ch = logging.StreamHandler()
#     ch.setLevel(logging.DEBUG)
#     logger.addHandler(ch)
#     return logger


def influx_runtime(influx_secret):
    """
    :param influx_secret: Secret passwords nad logins for Influx database
    :return: A database object which can be used to write/read data points
    """
    # token, org, bucket, url
    database = InfluxController(influx_secret.token,
                                influx_secret.org,
                                influx_secret.bucket,
                                influx_secret.url,
                                influx_secret.port)
    database.connect_db()
    return database


def mqtt_runtime(mqtt_secret, influx_database):
    """
    :param mqtt_secret: Secret passwords nad logins for MQTT subscriber
    :param influx_database: An Influx database object for the MQTTDecoder to write to
    :return: Never returns (see mq.mqtt_runtime())
    """
    client = mqtt.Client()
    mq = MQTTDecoder(mqtt_secret.host,
                     mqtt_secret.port,
                     mqtt_secret.user,
                     mqtt_secret.password,
                     client,
                     mqtt_secret.topic,
                     influx_database)
    mq.setup_mqtt()
    mq.mqtt_runtime()


def main():
    """
    Main function which calls both the Influx database controller and the MQTT controller
    """
    influx_database = influx_runtime(Secrets.InfluxSecret)
    mqtt_runtime(Secrets.MQTTSecret, influx_database)


if __name__ == '__main__':
    main()
