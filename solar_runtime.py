"""
classes program which initialises and runs both the MQTT and InfluxDB controllers
"""

from classes.influx_classes import InfluxController
from classes.py_functions import create_logger, get_mqtt_secrets, get_influx_secrets
from classes.solar_classes import MQTTDecoder
from config.consts import SOLAR_DEBUG_CONFIG_TITLE


def create_influx_controller(influx_secret):
    """
    classes function that creates a InfluxController for use
    :param influx_secret: Secret passwords nad logins for Influx database
    :return: A database object which can be used to write/read data points
    """
    for _, value in influx_secret.items():
        if not value:
            logging.error("Missing secret credential for InfluxDB in the .env")
            raise ValueError("Missing secret credential for InfluxDB in the .env")
    
    database = InfluxController(
        influx_secret["influx_url"],
        influx_secret["influx_org"],
        influx_secret["influx_bucket"],
        influx_secret["influx_token"]
    )
    database.startup()
    return database


def mqtt_runtime(mqtt_secret, influx_database):
    """
    classes function that creates a MQTT client
    :param mqtt_secret: Secret passwords nad logins for MQTT subscriber
    :param influx_database: An Influx database object for the MQTTDecoder to write to
    :return: Never returns (see mq.mqtt_runtime())
    """
    for _, value in mqtt_secret.items():
        if not value:
            logging.error("Missing secret credential for MQTT in the .env")
            raise ValueError("Missing secret credential for MQTT in the .env")

    mqtt = MQTTDecoder(
        mqtt_secret["mqtt_host"],
        mqtt_secret["mqtt_port"],
        mqtt_secret["mqtt_user"],
        mqtt_secret["mqtt_password"],
        mqtt_secret["mqtt_topic"],
        influx_database,
    )
    mqtt.startup()
    mqtt.mqtt_runtime()


def main():
    """
    classes function which calls both the Influx database controller and the MQTT controller
    """
    influx_secrets = get_influx_secrets()
    mqtt_secrets = get_mqtt_secrets()
    influx_database = create_influx_controller(influx_secrets)
    mqtt_runtime(mqtt_secrets, influx_database)


if __name__ == "__main__":
    logging = create_logger(SOLAR_DEBUG_CONFIG_TITLE)
    main()
