"""
File which contains definitions of custom exception patterns
"""


class MissingConfigurationError(Exception):
    """
    Defines an exception class for use when the loaded configuration file contains missing data
    """


class MissingCredentialsError(Exception):
    """
    Defines an exception class for when there are credentials missing
    """


class MqttServerOfflineError(Exception):
    """
    Defines an exception class for an offline MQTT server
    """
