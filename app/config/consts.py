"""
File for storing constant variables
"""

from queue import Queue


# Py Functions
CONFIG_FILENAME = "config/config.ini"

# Influx Query
INFLUX_QUERY_CONFIG_TITLE = "query_settings"
INFLUX_DEBUG_CONFIG_TITLE = "influx_debugger"

# Solar Runtime
SOLAR_DEBUG_CONFIG_TITLE = "solar_debugger"
MAX_WRITE_POINT_EXCEPTIONS = 5

# Multi-Threading
class ExitContition:
    """
    Stores exit condition for multi-threading
    """

    value = False


THREADED_QUEUE = Queue()
MAX_QUEUE_LENGTH = 20
EXIT_APP = ExitContition()
LOOP_FLAG = 0
