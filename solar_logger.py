"""
classes program which initializes and runs both the MQTT and InfluxDB controllers
"""

import queue
import signal
import sys
import threading
import time

from classes.influx_classes import InfluxConnector
from classes.mqtt_classes import MqttConnector
from classes.py_functions import SecretStore
from classes.py_logger import create_logger
from config.consts import (
    EXIT_APP,
    MAX_INFLUX_ERRORS,
    SOLAR_DEBUG_CONFIG_TITLE,
    THREADED_QUEUE,
)


def shutdown_threads() -> None:
    """
    Default shutdown action for uncaught exceptions and signals
    """
    EXIT_APP.exit = True
    time.sleep(0.5)
    logging.info("Application exited with code 0")
    sys.exit(0)


def sigterm_handler(_signo, _stack_frame) -> None:
    """
    Handling SIGTERM signals
    """
    logging.critical("Received SIGTERM, shutting down")
    shutdown_threads()


def sigint_handler(_signo, _stack_frame) -> None:
    """
    Handling SIGINT or CTRL + C signals
    """
    logging.critical("Received SIGINT/CTRL+C quit code, shutting down")
    shutdown_threads()


def run_threaded_influx_writer(secret_store: SecretStore) -> None:
    """
    Secondary thread which runs the InfluxDB connector
    Writes point data received from the MQTT._on_message in a threaded process
    """
    logging.info("Created Influx thread")
    influx_connector = InfluxConnector(secret_store=secret_store)
    contiguous_errors = 0

    logging.info("Attempting health check for InfluxDB")
    try:
        influx_connector.health_check()
        logging.info("Successfully connected to InfluxDB server")
    except Exception as err:
        logging.critical("Failed to connect InfluxDB server\n--quitting--")
        raise err

    while not EXIT_APP.exit:
        try:
            popped_packet: dict = THREADED_QUEUE.get(timeout=1.0)
            logging.debug(f"Popped packet off queue: {popped_packet}")

            if popped_packet:
                logging.debug(
                    f"Writing points to InfluxDB: ("
                    f"{popped_packet['msg_time']}, {popped_packet['msg_type']})"
                )
                influx_connector.write_points(
                    msg_time=popped_packet["msg_time"],
                    msg_type=popped_packet["msg_type"],
                    msg_payload=popped_packet["msg_payload"],
                )
                contiguous_errors = 0
        except queue.Empty:
            continue
        except Exception as err:
            contiguous_errors += 1
            logging.warning(f"Failed to run write, returned error: {err}")
            logging.warning(
                f"Contiguous Influx errors increased to {contiguous_errors}"
            )
        finally:
            if contiguous_errors >= MAX_INFLUX_ERRORS:
                logging.critical(
                    f"Contiguous Influx errors has exceeded max count, "
                    f"{MAX_INFLUX_ERRORS}\n--quitting--"
                )
                shutdown_threads()
        time.sleep(0.2)
    logging.info("Exited Influx thread")


def run_main_process_mqtt_client(secret_store: SecretStore):
    """
    Main process which runs the MQTT connector
    Listens to a MQTT broken then decodes received packets
    """
    mqtt_connector = MqttConnector(
        secret_store=secret_store,
    )
    mqtt_connector.run_mqtt_listener()


def main() -> None:
    """
    Calls both the Influx database connector and the MQTT connector
    and runs them in separate threads
    """
    secret_store = SecretStore(read_mqtt=True, read_influx=True)

    # Properly contain termination events and kill child threads
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    try:
        thread_influx = threading.Thread(
            target=run_threaded_influx_writer, args=(secret_store,)
        )
        thread_influx.start()
        time.sleep(0.1)
        run_main_process_mqtt_client(secret_store=secret_store)
    except Exception:
        logging.exception("Caught unknown exception")
        shutdown_threads()


if __name__ == "__main__":
    logging = create_logger(SOLAR_DEBUG_CONFIG_TITLE)
    main()
