"""
Main program which initialises and runs both the MQTT and InfluxDB controllers
"""
from SolarClasses import MQTTDecoder, InfluxController
from SecretStore import Secrets
import logging
import sys

FILE_LOGGING = False
DEBUG_LEVEL = logging.DEBUG
# Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL


def influx_runtime(influx_secret):
    """
    Main function that creates a InfluxController for use
    :param influx_secret: Secret passwords nad logins for Influx database
    :return: A database object which can be used to write/read data points
    """
    database = InfluxController(influx_secret.token,
                                influx_secret.org,
                                influx_secret.bucket,
                                influx_secret.url)
    database.startup()
    return database


def mqtt_runtime(mqtt_secret, influx_database):
    """
    Main function that creates a MQTT client
    :param mqtt_secret: Secret passwords nad logins for MQTT subscriber
    :param influx_database: An Influx database object for the MQTTDecoder to write to
    :return: Never returns (see mq.mqtt_runtime())
    """
    mq = MQTTDecoder(mqtt_secret.host,
                     mqtt_secret.port,
                     mqtt_secret.user,
                     mqtt_secret.password,
                     mqtt_secret.topic,
                     influx_database)
    mq.startup()
    mq.mqtt_runtime()


def main():
    """
    Main function which calls both the Influx database controller and the MQTT controller
    """
    if sys.gettrace() and not FILE_LOGGING:
        logging.basicConfig(stream=sys.stdout, level=DEBUG_LEVEL)
    elif sys.gettrace() and FILE_LOGGING:
        logging.basicConfig(filename='../SolarLogs.log',
                            filemode='a',
                            format='%(asctime)s, %(name)s, %(levelname)s, %(message)s',
                            datefmt='%H:%M:%S',
                            level=DEBUG_LEVEL)
    influx_database = influx_runtime(Secrets.InfluxSecret)
    mqtt_runtime(Secrets.MQTTSecret, influx_database)


if __name__ == '__main__':
    main()
