"""
File for storing constant variables
"""

from queue import Queue


# Configs
CONFIG_FILENAME = "config/config.ini"  # Py Functions
INFLUX_QUERY_CONFIG_TITLE = "query_settings"  # Influx Query
INFLUX_DEBUG_CONFIG_TITLE = "influx_debugger"  # Influx Query
SOLAR_DEBUG_CONFIG_TITLE = "solar_debugger"  # Solar Runtime

# Multi-Threading
class ExitContition:
    """
    Stores exit condition for multi-threading
    """

    exit = False


MAX_INFLUX_ERRORS = 5
MAX_MQTT_ERRORS = 5
MAX_QUEUE_LENGTH = 20
THREADED_QUEUE = Queue()
EXIT_APP = ExitContition()
