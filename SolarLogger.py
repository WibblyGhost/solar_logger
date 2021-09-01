"""
Main program which initialises and runs both the MQTT and InfluxDB controllers
"""

from SolarClasses import MQTTDecoder, InfluxController
import Secrets
import paho.mqtt.client as mqtt
import logging
import sys


def influx_runtime(influx_secret):
    """
    Main function that creates a InfluxController for use
    :param influx_secret: Secret passwords nad logins for Influx database
    :return: A database object which can be used to write/read data points
    """
    database = InfluxController(influx_secret.token,
                                influx_secret.org,
                                influx_secret.bucket,
                                influx_secret.url,
                                influx_secret.bucket_id)
    database.startup()
    return database


def mqtt_runtime(mqtt_secret, influx_database):
    """
    Main function that creates a MQTT client
    :param mqtt_secret: Secret passwords nad logins for MQTT subscriber
    :param influx_database: An Influx database object for the MQTTDecoder to write to
    :return: Never returns (see mq.mqtt_runtime())
    """
    mqtt_client = mqtt.Client()
    mq = MQTTDecoder(mqtt_secret.host,
                     mqtt_secret.port,
                     mqtt_secret.user,
                     mqtt_secret.password,
                     mqtt_client,
                     mqtt_secret.topic,
                     influx_database)
    mq.startup()
    mq.mqtt_runtime()


def main():
    """
    Main function which calls both the Influx database controller and the MQTT controller
    """
    if sys.gettrace():
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    influx_database = influx_runtime(Secrets.InfluxSecret)
    mqtt_runtime(Secrets.MQTTSecret, influx_database)


if __name__ == '__main__':
    main()
