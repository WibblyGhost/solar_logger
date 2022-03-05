"""
classes program which initialises and runs both the MQTT and InfluxDB controllers
"""


from classes.influx_classes import InfluxController
from classes.py_functions import create_logger
from classes.solar_classes import MQTTDecoder
from config.consts import SOLAR_DEBUG_CONFIG_TITLE
from private.mqtt_codenames import MQTTSecret
from private.influx_codenames import InfluxSecret


def create_influx_controller(influx_secret):
    """
    classes function that creates a InfluxController for use
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
    classes function that creates a MQTT client
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
    classes function which calls both the Influx database controller and the MQTT controller
    """
    influx_database = create_influx_controller(InfluxSecret)
    mqtt_runtime(MQTTSecret, influx_database)


if __name__ == '__main__':
    logging = create_logger(SOLAR_DEBUG_CONFIG_TITLE)
    main()
