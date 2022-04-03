"""
File which contains classes required by both Influx and MQTT
This file should be minimal since both MQTT and Influx is independent.
"""


from dataclasses import dataclass
from datetime import datetime


@dataclass
class QueuePackage:
    """
    Data class which defines values that are pushed and popped off the global stack
    """

    measurement: str = None
    time_field: datetime = None
    field: str = None
