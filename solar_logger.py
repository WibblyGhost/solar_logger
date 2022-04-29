"""
classes program which initializes and runs both the MQTT and InfluxDB controllers
"""

import logging
import signal
import threading
import time

from classes.common_classes import QueuePackage
from classes.influx_classes import InfluxConnector
from classes.mqtt_classes import MqttConnector
from classes.py_functions import SecretStore
from classes.py_logger import create_logger
from classes.consts import (
    SOLAR_DEBUG_CONFIG_TITLE,
    THREADED_QUEUE,
)


def run_threaded_influx_writer() -> None:
    """
    Secondary thread which runs the InfluxDB connector
    Writes point data received from the MQTT._on_message in a threaded process
    NOTE: Since this program needs to indefinitely run all
    exceptions will just be logged instead of exiting the program.
    """
    secret_store = SecretStore(has_influx_access=True)
    influx_connector = InfluxConnector(secret_store=secret_store)
    logging.info("Attempting health check for InfluxDB")
    try:
        influx_connector.health_check()
        logging.info("Influx health check succeeded")
    except:
        logging.exception(f"Failed to complete health check")
        thread_events.clear()
        raise

    while thread_events.is_set():
        if not THREADED_QUEUE.empty():
            queue_package: QueuePackage = THREADED_QUEUE.get(timeout=1.0)
            logging.debug(
                f"Popped packet off queue, queue now has {THREADED_QUEUE.qsize()} items"
            )
            try:
                influx_connector.write_points(queue_package=queue_package)
            except:
                logging.exception(
                    f"Failed to run write to Influx server, returned error"
                )
                time.sleep(1)
            if THREADED_QUEUE.empty():
                logging.info("Popped all packets off queue and wrote to InfluxDB")
        else:
            time.sleep(0.5)
    thread_events.clear()


def run_threaded_mqtt_client():
    """
    Main process which runs the MQTT connector
    Listens to a MQTT broken then decodes received packets
    NOTE: Since this program needs to indefinitely run all
    exceptions will just be logged instead of exiting the program.
    """
    secret_store = SecretStore(has_mqtt_access=True)
    mqtt_connector = MqttConnector(
        secret_store=secret_store,
    )
    mqtt_client = None
    logging.info("Creating MQTT listening service")
    try:
        mqtt_client = mqtt_connector.get_mqtt_client()
    except:
        logging.exception(f"Failed to create MQTT listening service")
        thread_events.clear()
        raise

    # Start MQTT-Listener thread to indefinitley listen to the broker
    # NOTE: This actually runs another thread as a Daemon due to the behavior of loop_start
    logging.info("Started thread: MQTT-Listener")
    # Running loop_start() will enter into a confection state and enter on_message() every time
    # a new message comes in. Because of this all error/exception handing must be done in the
    # on_message() command, in our case we don't want the program to exit so we just log the error.
    try:
        mqtt_client.loop_start()
    except:
        logging.exception(f"MQTT listener exited with a fatal error")
        thread_events.clear()
        raise

    # Sleep Thread-MQTT
    while thread_events.is_set():
        time.sleep(1)

    # Stops the extra MQTT-Listener thread gracefully
    if mqtt_client:
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
