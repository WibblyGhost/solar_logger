"""
Contains both a logger and csv writing function for use in outside functions
"""
import os
import csv
import logging
import configparser
import distutils.util

from config.consts import CONFIG_FILENAME


def create_logger(config_name):
    """
    Creates a logging instance, can be customised through the config.ini
    :param config_name: Section under the config for the configuration to pull data from
    :return: Logger for logging
    """
    config_p = configparser.ConfigParser()
    config_p.read(CONFIG_FILENAME)
    file_logging = config_p.get(config_name, 'file_logging')
    file_logging = bool(distutils.util.strtobool(file_logging))
    debug_dict = {'DEBUG': logging.DEBUG,
                  'INFO': logging.INFO,
                  'WARNING': logging.WARNING,
                  'ERROR': logging.ERROR,
                  'CRITICAL': logging.CRITICAL}
    debug_level = debug_dict[config_p.get(config_name, 'debug_level')]
    file_format = config_p.get(config_name, 'format')
    date_format = config_p.get(config_name, 'dateformat')

    logger = logging.getLogger()
    logger.setLevel(debug_level)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(debug_level)
    log_formatter = logging.Formatter(fmt=file_format, datefmt=date_format)
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)
    logging.info('Created logger')

    if file_logging:
        file_location = config_p.get(config_name, 'file_location')
        if not os.path.exists(file_location):
            os.makedirs(file_location)
        filename = config_p.get(config_name, 'filename')
        full_path = file_location + filename
        file_mode = config_p.get(config_name, 'filemode')
        file_stream_handler = logging.FileHandler(filename=full_path, mode=file_mode)
        file_stream_handler.setLevel(debug_level)
        file_stream_handler.setFormatter(log_formatter)
        logger.addHandler(file_stream_handler)
        logging.info(f'Created file logger at {full_path}')

    return logging


def csv_writer(config_name, table):
    """
    Writes a CSV file from an Influx query
    :param config_name: Section under the config for the configuration to pull data from
    :param table: Resultant CSV query from the Influx database
    """
    config_p = configparser.ConfigParser()
    config_p.read(CONFIG_FILENAME)
    file_location = config_p.get(config_name, 'csv_location')
    if not os.path.exists(file_location):
        os.makedirs(file_location)
    filename = config_p.get(config_name, 'csv_name')
    full_path = file_location + filename
    filemode = config_p.get(config_name, 'csv_mode')
    with open(full_path, filemode) as file_instance:
        writer = csv.writer(file_instance)
        for row in table:
            writer.writerow(row)
    logging.info(f'Wrote rows into CSV file at: {full_path}')


def read_query_settings(config_name):
    """
    :param config_name: Section under the config for the configuration to pull data from
    :return: Query variables
    """
    config_p = configparser.ConfigParser()
    config_p.read(CONFIG_FILENAME)
    return config_p.get(config_name, 'query_mode')
