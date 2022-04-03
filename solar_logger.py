"""
classes program which initializes and runs both the MQTT and InfluxDB controllers
"""

import logging
import queue
import signal
import threading
import time

from classes.common_classes import QueuePackage
from classes.influx_classes import InfluxConnector
from classes.mqtt_classes import MqttConnector
from classes.py_functions import SecretStore
from classes.py_logger import create_logger
from config.consts import (
    MAX_INFLUX_ERRORS,
    MAX_MQTT_ERRORS,
    SOLAR_DEBUG_CONFIG_TITLE,
    THREADED_QUEUE,
)


def run_threaded_influx_writer() -> None:
    """
    Secondary thread which runs the InfluxDB connector
    Writes point data received from the MQTT._on_message in a threaded process
    """
    secret_store = SecretStore(read_influx=True)
    influx_connector = InfluxConnector(secret_store=secret_store)
    contiguous_errors = 0
    logging.info("Attempting health check for InfluxDB")
    try:
        influx_connector.health_check()
        logging.info("Successfully connected to InfluxDB server")
    except Exception as err:
        logging.critical("Failed to connect InfluxDB server")
        raise err
    while thread_events.is_set() and contiguous_errors < MAX_INFLUX_ERRORS:
        try:
            queue_package: QueuePackage = THREADED_QUEUE.get(timeout=1.0)
            logging.debug(
                f"Popped packet off queue, queue now has {THREADED_QUEUE.qsize()} items"
            )
        except queue.Empty:
            continue
        if queue_package:
            try:
                influx_connector.write_points(queue_package=queue_package)
                contiguous_errors = 0
            except Exception as err:
                contiguous_errors += 1
                logging.warning(f"Failed to run write, returned error: \n{err}")
                logging.warning(
                    f"Contiguous Influx errors increased to {contiguous_errors}"
                )
            if contiguous_errors >= MAX_INFLUX_ERRORS:
                break
    if contiguous_errors >= MAX_INFLUX_ERRORS:
        logging.critical(
            f"Contiguous Influx errors has exceeded max count, " f"{MAX_INFLUX_ERRORS}"
        )
        thread_events.clear()


def run_threaded_mqtt_client():
    """
    Main process which runs the MQTT connector
    Listens to a MQTT broken then decodes received packets
    """
    secret_store = SecretStore(read_mqtt=True)
    mqtt_connector = MqttConnector(
        secret_store=secret_store,
    )
    mqtt_client = mqtt_connector.get_mqtt_client()
    logging.info("Started thread: MQTT-Listener")
    # NOTE: This actually runs another thread as a Daemon due to the behavior of loop_start
    mqtt_client.loop_start()
    while thread_events.is_set() and mqtt_connector.contiguous_errors < MAX_MQTT_ERRORS:
        time.sleep(1)
    if mqtt_connector.contiguous_errors >= MAX_MQTT_ERRORS:
        logging.critical(
            f"Continuous mqtt errors has exceeded max count, {MAX_MQTT_ERRORS}"
        )
    mqtt_client.loop_stop()
    logging.info("Joined thread: MQTT-Listener")
    thread_events.clear()


def sigterm_handler(_signo, _stack_frame) -> None:
    """
    Handling SIGTERM signals
    """
    logging.critical("Received SIGTERM, shutting down")
    time.sleep(1)
    thread_events.clear()


def sigint_handler(_signo, _stack_frame) -> None:
    """
    Handling SIGINT or CTRL + C signals
    """
    logging.critical("Received SIGINT/CTRL+C quit code, shutting down")
    time.sleep(1)
    thread_events.clear()


def main() -> None:
    """
    Calls both the Influx database connector and the MQTT connector
    and runs them in separate threads
    NOTE: This program actually uses four threads not three due to the behavior
        of the MQTT loop_start() function
    """
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    # Starting threads
    logging.info("Starting threads")
    for thread in thread_list:
        thread.start()
        logging.info(f"Started thread: {thread.name}")

    # Put main thread to sleep
    logging.info("Main thread entering blocking loop")
    while thread_events.is_set():
        time.sleep(1)
    logging.info("Main thread exited blocking loop")

    # Gracefull terminate all threads
    logging.info("Clearing thread events, gracefully terminating all threads")
    thread_events.clear()

    # Closing threads
    for thread in thread_list:
        thread.join()
        logging.info(f"Joined thread: {thread.name}")
    logging.info("All threads have closed")
    logging.info("Exited application with exit code 0")


if __name__ == "__main__":
    logging = create_logger(SOLAR_DEBUG_CONFIG_TITLE)
    logging.logThreads = True
    thread_events = threading.Event()
    thread_events.set()
    logging.info("Created thread list")
    thread_list = [
        threading.Thread(
            name="Thread-Influx",
            target=run_threaded_influx_writer,
        ),
        threading.Thread(
            name="Thread-MQTT", target=run_threaded_mqtt_client, daemon=True
        ),
    ]
    main()
