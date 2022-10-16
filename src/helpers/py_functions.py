"""
Contains all functions that aren't directly correlated to Influx, MQTT, or logging
"""

import csv
import logging
import os
from configparser import ConfigParser

from src.helpers.consts import CONFIG_FILENAME


def write_results_to_csv(config_name: str, table: dict) -> None:
    """
    Writes a CSV file from an Influx query
    :param config_name: Section under the config for the configuration to pull data from
    :param table: Resultant CSV query from the Influx database
    """
    try:
        config_parser = ConfigParser()
        config_parser.read(CONFIG_FILENAME)
        file_location = config_parser.get(config_name, "csv_location")
        filename = config_parser.get(config_name, "csv_name")
        full_path = file_location + filename
        filemode = config_parser.get(config_name, "csv_mode")
        if not os.path.exists(file_location):
            os.makedirs(file_location)
        with open(full_path, filemode) as file_instance:
            writer = csv.writer(file_instance)
            for row in table:
                writer.writerow(row)
        logging.info(f"Wrote rows into CSV file at: {full_path}")
    except Exception as err:
        logging.critical("Failed to write CSV")
        raise err


def read_query_settings(config_name: str) -> any:
    """
    :param config_name: Section under the config for the configuration to pull data from
    :return: Query variables
    """
    config_parser = ConfigParser()
    config_parser.read(CONFIG_FILENAME)
    return config_parser.get(section=config_name, option="query_mode")
