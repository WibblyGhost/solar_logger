"""
classes program which initializes and runs both the MQTT and InfluxDB controllers
"""

import logging
import signal
import threading
import time

from src.classes.common_classes import QueuePackage, SecretStore
from src.classes.influx_classes import InfluxConnector
from src.classes.mqtt_classes import MqttConnector
from src.helpers.consts import SOLAR_DEBUG_CONFIG_TITLE, THREADED_QUEUE
from src.helpers.py_logger import create_logger


class ThreadedRunner:
    """
    Class containing the threading operations to run the combined MQTT & Influx services
    """

    def __init__(self) -> None:
        self.log = create_logger(SOLAR_DEBUG_CONFIG_TITLE)
        self.thread_events = threading.Event()
        logging.logThreads = True

    def sigterm_handler(self, _signo, _stack_frame) -> None:
        """
        Handling SIGTERM signals
        """
        logging.critical("Received SIGTERM, shutting down")
        time.sleep(1)
        self.thread_events.clear()

    def sigint_handler(self, _signo, _stack_frame) -> None:
        """
        Handling SIGINT or CTRL + C signals
        """
        logging.critical("Received SIGINT/CTRL+C quit code, shutting down")
        time.sleep(1)
        self.thread_events.clear()

    def start(self) -> None:
        """
        Calls both the Influx database connector and the MQTT connector
        and runs them in separate threads
        NOTE: This program actually uses four threads not three due to the behavior
            of the MQTT loop_start() function
        """
        self.thread_events.set()
        logging.info("Created thread list")
        thread_list = [
            threading.Thread(
                name="Thread-Influx",
                target=self.run_threaded_influx_writer,
            ),
            threading.Thread(
                name="Thread-MQTT", target=self.run_threaded_mqtt_client, daemon=True
            ),
        ]

        signal.signal(signal.SIGTERM, self.sigterm_handler)
        signal.signal(signal.SIGINT, self.sigint_handler)

        # Starting threads
        logging.info("Starting threads")
        for thread in thread_list:
            thread.start()
            logging.info(f"Started thread: {thread.name}")

        # Put main thread to sleep
        logging.info("Main thread entering blocking loop")
        while self.thread_events.is_set():
            time.sleep(1)
        logging.info("Main thread exited blocking loop")

        # Gracefull terminate all threads
        logging.info("Clearing thread events, gracefully terminating all threads")
        self.thread_events.clear()

        # Closing threads
        for thread in thread_list:
            thread.join()
            logging.info(f"Joined thread: {thread.name}")
        logging.info("All threads have closed")
        logging.info("Exited application with exit code 0")

    def run_threaded_influx_writer(self) -> None:
        """
        Secondary thread which runs the InfluxDB connector
        Writes point data received from the MQTT._on_message in a threaded process
        NOTE: Since this program needs to indefinitely run all
        exceptions will just be logged instead of exiting the program.
        """
        try:
            secret_store = SecretStore(has_influx_access=True)
            influx_connector = InfluxConnector(secret_store=secret_store)
            logging.info("Attempting health check for InfluxDB")
        except Exception:
            logging.exception("Failed to setup environment")
            self.thread_events.clear()
            return
        try:
            influx_connector.health_check()
            logging.info("InfluxDB health check succeeded")
        except Exception:
            logging.exception("Failed to complete InfluxDB health check")
            self.thread_events.clear()
            return

        while self.thread_events.is_set():
            if not THREADED_QUEUE.empty():
                queue_package: QueuePackage = THREADED_QUEUE.get(timeout=1.0)
                logging.debug(
                    f"Popped packet off queue, queue now has {THREADED_QUEUE.qsize()} items"
                )
                try:
                    influx_connector.write_points(queue_package=queue_package)
                except Exception:
                    logging.exception(
                        "Failed to run write to Influx server, returned error"
                    )
                    time.sleep(1)
                if THREADED_QUEUE.empty():
                    logging.info("Popped all packets off queue and wrote to InfluxDB")
            else:
                time.sleep(0.5)
        self.thread_events.clear()

    def run_threaded_mqtt_client(self):
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
        except Exception:
            logging.exception("Failed to create MQTT listening service")
            self.thread_events.clear()
            return

        # Start MQTT-Listener thread to indefinitely listen to the broker
        # NOTE: This actually runs another thread as a Daemon due to the behavior of loop_start
        logging.info("Started thread: MQTT-Listener")
        # Running loop_start() will enter into a confection state and
        # enter on_message() every time a new message comes in. Because
        # of this all error/exception handing must be done in the on_message()
        # command, in our case we don't want the program to exit so we just log the error.
        try:
            mqtt_client.loop_start()
        except Exception:
            logging.exception("MQTT listener exited with a fatal error")
            self.thread_events.clear()
            return

        # Sleep Thread-MQTT
        while self.thread_events.is_set():
            time.sleep(1)

        # Stops the extra MQTT-Listener thread gracefully
        if mqtt_client:
            mqtt_client.loop_stop()
        logging.info("Joined thread: MQTT-Listener")
        self.thread_events.clear()


def main():
    """
    Main runtime for solar logger, called from start_logger.py
    """
    thread_runner = ThreadedRunner()
    thread_runner.start()
