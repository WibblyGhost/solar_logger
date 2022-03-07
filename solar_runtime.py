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
    for key, value in influx_secret.items():
        if not value:
            logging.error(f"Missing secret credential for InfluxDB in the .env, {key}")
            raise ValueError(f"Missing secret credential for InfluxDB in the .env, {key}")

    database = InfluxController(
        url=influx_secret["INFLUX_URL"],
        org=influx_secret["INFLUX_ORG"],
        bucket=influx_secret["INFLUX_BUCKET"],
        token=influx_secret["INFLUX_TOKEN"],
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
    for key, value in mqtt_secret.items():
        if not value:
            logging.error(f"Missing secret credential for MQTT in the .env, {key}")
            raise ValueError(f"Missing secret credential for MQTT in the .env, {key}")

    mqtt = MQTTDecoder(
        host=mqtt_secret["MQTT_HOST"],
        port=mqtt_secret["MQTT_PORT"],
        user=mqtt_secret["MQTT_USER"],
        token=mqtt_secret["MQTT_TOKEN"],
        topic=mqtt_secret["MQTT_TOPIC"],
        influx_database=influx_database,
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
