"""
File for storing constant variables
"""

from queue import Queue

# Configs
CONFIG_FILENAME = "config/config.ini"  # Py Functions
INFLUX_QUERY_CONFIG_TITLE = "query_settings"  # Influx Query
INFLUX_DEBUG_CONFIG_TITLE = "influx_debugger"  # Influx Query
SOLAR_DEBUG_CONFIG_TITLE = "solar_debugger"  # Solar Runtime

# Additional Consts
MAX_PORT_RANGE = 65535

# Multi-Threading Processing
# Size of queue, needs to be quite large for the volume of data
MAX_QUEUE_LENGTH = 100
# Time to wait when queue is full
QUEUE_WAIT_TIME = 1
THREADED_QUEUE = Queue(
    maxsize=MAX_QUEUE_LENGTH
)
