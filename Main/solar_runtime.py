"""
Main program which initialises and runs both the MQTT and InfluxDB controllers
"""
from solar_classes import MQTTDecoder
from influx_classes import InfluxController
from SecretStore import secrets
from py_functions import create_logger

DEBUG_CONFIG_TITLE = 'solar_debugger'


def create_influx_controller(influx_secret):
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
    influx_database = create_influx_controller(secrets.InfluxSecret)
    mqtt_runtime(secrets.MQTTSecret, influx_database)


if __name__ == '__main__':
    logging = create_logger(DEBUG_CONFIG_TITLE)
    main()
