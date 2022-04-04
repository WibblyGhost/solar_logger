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


def calculate_seconds(
    days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0
):
    """TODO"""
    _days = days * 3600 * 24
    _hours = hours * 3600
    _minutes = minutes * 60
    _seconds = seconds
    return _days + _hours + _minutes + _seconds
