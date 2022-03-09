"""
classes program which initialises and runs both the MQTT and InfluxDB controllers
"""

from classes.influx_classes import InfluxController, create_influx_controller
from classes.mqtt_classes import MQTTDecoder
from classes.py_functions import create_logger, get_mqtt_secrets, get_influx_secrets
from config.consts import SOLAR_DEBUG_CONFIG_TITLE
from private.private import INFLUX_BUCKET, INFLUX_ORG, INFLUX_TOKEN, INFLUX_URL, MQTT_HOST, MQTT_LOGIN, MQTT_PORT, MQTT_TOKEN, MQTT_TOPIC


def start_mqtt_server(mqtt_secret: dict, influx_database: InfluxController) -> None:
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
    mqtt.start_mqtt_service()


def main() -> None:
    """
    classes function which calls both the Influx database controller and the MQTT controller
    """
    influx_secrets = get_influx_secrets()
    mqtt_secrets = get_mqtt_secrets()
    influx_database = create_influx_controller(influx_secrets)
    start_mqtt_server(mqtt_secrets, influx_database)


if __name__ == "__main__":
    logging = create_logger(SOLAR_DEBUG_CONFIG_TITLE)
    main()
