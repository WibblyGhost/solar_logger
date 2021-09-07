"""
Contains both a logger and csv writing function for use in outside functions
"""
import distutils.util
import logging
import configparser
import sys
import csv

CONFIG_FILENAME = 'config.ini'


def create_logger(program_name):
    """
    Creates a logging instance, can be customised through the config.ini
    :param program_name: Section under the config for the configuration to pull data from
    :return: Logger for logging
    """
    config_p = configparser.ConfigParser()
    config_p.read(CONFIG_FILENAME)
    file_logging = config_p.get(program_name, 'file_logging')
    file_logging = bool(distutils.util.strtobool(file_logging))
    debug_dict = {'DEBUG': logging.DEBUG,
                  'INFO': logging.INFO,
                  'WARNING': logging.WARNING,
                  'ERROR': logging.ERROR,
                  'CRITICAL': logging.CRITICAL}
    debug_level = debug_dict[config_p.get(program_name, 'debug_level')]
    if sys.gettrace() and not file_logging:
        logging.basicConfig(stream=sys.stdout, level=debug_level)
    elif sys.gettrace() and file_logging:
        file_name = config_p.get(program_name, 'filename')
        file_mode = config_p.get(program_name, 'filemode')
        file_format = config_p.get(program_name, 'format')
        date_format = config_p.get(program_name, 'dateformat')
        logging.basicConfig(filename=file_name, filemode=file_mode, format=file_format,
                            datefmt=date_format, level=debug_level)
    logging.info('Created logger')
    return logging


def csv_writer(program_name, table):
    """
    Writes a CSV file from an Influx query
    :param program_name: Section under the config for the configuration to pull data from
    :param table: Resultant CSV query from the Influx database
    """
    config_p = configparser.ConfigParser()
    config_p.read(CONFIG_FILENAME)
    csv_location = config_p.get(program_name, 'csv_name')
    filemode = config_p.get(program_name, 'filemode')
    with open(csv_location, filemode) as file_instance:
        writer = csv.writer(file_instance)
        for row in table:
            writer.writerow(row)
    logging.info(f'Wrote rows into CSV file at: {csv_location}')

