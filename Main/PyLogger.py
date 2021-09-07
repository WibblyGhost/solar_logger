import distutils.util
import logging
import configparser
import sys

CONFIG_FILENAME = 'config.ini'


def create_logger(program_name):
    """
    Creates a logging instance, can be customised through the config.ini
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
    return logging
