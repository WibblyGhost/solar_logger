"""
File for storing constant variables
"""

from queue import Queue


# Configs
CONFIG_FILENAME = "config/config.ini"  # Py Functions
INFLUX_QUERY_CONFIG_TITLE = "query_settings"  # Influx Query
INFLUX_DEBUG_CONFIG_TITLE = "influx_debugger"  # Influx Query
SOLAR_DEBUG_CONFIG_TITLE = "solar_debugger"  # Solar Runtime

# Error Counts
class ErrorCounts:
    """
    Stores all error counts for various sections
    """

    max_influx_errors = 5
    max_mqtt_errors = 5
    contiguous_influx_errors = 0
    contiguous_mqtt_errors = 0


# Multi-Threading
class ExitContition:
    """
    Stores exit condition for multi-threading
    """

    exit = False


MAX_QUEUE_LENGTH = 20
THREADED_QUEUE = Queue()
EXIT_APP = ExitContition()
ERROR_COUNTS = ErrorCounts()
