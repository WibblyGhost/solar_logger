"""
classes program which initializes and runs both the MQTT and InfluxDB controllers
"""

import queue
import signal
import sys
import threading
import time

from classes.influx_classes import create_influx_connector, influx_db_write_points
from classes.mqtt_classes import MqttConnector
from classes.py_functions import SecretStore
from classes.py_logger import create_logger
from config.consts import (
    EXIT_APP,
    SOLAR_DEBUG_CONFIG_TITLE,
    THREADED_QUEUE,
)


def sigterm_handler(_signo, _stack_frame) -> None:
    """
    Handling SIGTERM signals
    """
    logging.critical("Received SIGTERM, shutting down")
    EXIT_APP.exit = True
    time.sleep(0.5)
    logging.info("Application exited with code 0")
    sys.exit(0)


def sigint_handler(_signo, _stack_frame) -> None:
    """
    Handling SIGINT or CTRL + C signals
    """
    logging.critical("Received SIGINT/CTRL+C quit code, shutting down")
    EXIT_APP.exit = True
    time.sleep(0.5)
    logging.info("Application exited with code 0")
    sys.exit(0)


def run_threaded_influx_writer() -> None:
    """
    Writes point data received from the MQTT._on_message in a threaded process
    """
    logging.info("Created Influx thread")
    while not EXIT_APP.exit:
        try:
            popped_value = THREADED_QUEUE.get(timeout=1.0)
        except queue.Empty:
            continue
        if popped_value:
            logging.debug(f"Popped value off queue: {popped_value}")
            influx_db_write_points(
                msg_time=popped_value[0],
                msg_payload=popped_value[1],
                msg_type=popped_value[2],
                influx_connector=popped_value[3],
            )
            time.sleep(0.2)
    logging.info("Exited Influx thread")


def main() -> None:
    """
    Classes function which calls both the Influx database controller and the MQTT controller
    and runs them in separate threads
    """
    secret_store = SecretStore(read_mqtt=True, read_influx=True)
    influx_connector = create_influx_connector(
        influx_secrets=secret_store.influx_secrets
    )
    mqtt_connector = MqttConnector(
        mqtt_secrets=secret_store.mqtt_secrets,
        influx_connector=influx_connector,
    )

    # Properly contain termination events and kill of child threads
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    try:
        thread_influx = threading.Thread(target=run_threaded_influx_writer)
        thread_influx.start()
        mqtt_connector.run_mqtt_listener()

    except Exception:
        logging.exception("Caught unknown exception")
        EXIT_APP.exit = True


if __name__ == "__main__":
    logging = create_logger(SOLAR_DEBUG_CONFIG_TITLE)
    main()
