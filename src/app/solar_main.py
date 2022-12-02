"""
classes program which initializes and runs both the MQTT and InfluxDB controllers
"""

import logging
import signal
import threading
import time

from src.helpers.consts import SOLAR_DEBUG_CONFIG_TITLE
from src.helpers.multithreading import ThreadedRunner


class SolarRunner(ThreadedRunner):
    """
    Class containing the threading operations to run the combined MQTT & Influx services
    """

    def __init__(self) -> None:
        super().__init__(SOLAR_DEBUG_CONFIG_TITLE)

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


def main():
    """
    Main runtime for solar logger, called from start_logger.py
    """
    thread_runner = SolarRunner()
    thread_runner.start()
