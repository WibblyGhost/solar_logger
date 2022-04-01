"""
classes program which initialises and runs both the MQTT and InfluxDB controllers
"""

from classes.py_functions import SecretStore
from classes.custom_exceptions import MissingCredentialsError
from classes.influx_classes import InfluxController, create_influx_controller
from classes.mqtt_classes import MQTTDecoder
from classes.py_logger import create_logger
from config.consts import SOLAR_DEBUG_CONFIG_TITLE


def start_mqtt_server(mqtt_secrets: dict, influx_database: InfluxController) -> None:
    """
    classes function that creates a MQTT client
    :param mqtt_secret: Secret passwords nad logins for MQTT subscriber
    :param influx_database: An Influx database object for the MQTTDecoder to write to
    :return: Never returns (see mq.mqtt_runtime())
    """
    for key, value in mqtt_secrets.items():
        if not value:
            logging.error(f"Missing secret credential for MQTT in the .env, {key}")
            raise MissingCredentialsError(f"Missing secret credential for MQTT in the .env, {key}")

    mqtt = MQTTDecoder(
        host=mqtt_secrets["mqtt_host"],
        port=mqtt_secrets["mqtt_port"],
        user=mqtt_secrets["mqtt_user"],
        token=mqtt_secrets["mqtt_token"],
        topic=mqtt_secrets["mqtt_topic"],
        influx_database=influx_database,
    )
    mqtt.startup()
    mqtt.start_mqtt_service()


# def get_local_secrets() -> None:
#     """
#     For running the program locally instead of through docker.
#     """
#     from private.private import (
#         INFLUX_BUCKET,
#         INFLUX_ORG,
#         INFLUX_TOKEN,
#         INFLUX_URL,
#         MQTT_HOST,
#         MQTT_PORT,
#         MQTT_TOKEN,
#         MQTT_TOPIC,
#         MQTT_USER,
#     )

#     influx_secrets = {
#         "influx_bucket": INFLUX_BUCKET,
#         "influx_org": INFLUX_ORG,
#         "influx_token": INFLUX_TOKEN,
#         "influx_url": INFLUX_URL,
#     }
#     mqtt_secrets = {
#         "mqtt_host": MQTT_HOST,
#         "mqtt_user": MQTT_USER,
#         "mqtt_port": MQTT_PORT,
#         "mqtt_token": MQTT_TOKEN,
#         "mqtt_topic": MQTT_TOPIC,
#     }
#     return influx_secrets, mqtt_secrets


def main() -> None:
    """
    Classes function which calls both the Influx database controller and the MQTT controller
    """
    secret_store = SecretStore(read_mqtt=True, read_influx=True)
    influx_controller = create_influx_controller(influx_secret=secret_store.influx_secrets)
    start_mqtt_server(mqtt_secrets=secret_store.mqtt_secrets, influx_database=influx_controller)


if __name__ == "__main__":
    logging = create_logger(SOLAR_DEBUG_CONFIG_TITLE)
    main()

# TODO: Create multi-threaded program
# async, await
