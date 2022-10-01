"""
Program which creates and runs Influx database queries
Check the Influx query documentation for query syntax:
https://docs.influxdata.com/influxdb/v2.0/api-guide/client-libraries/python/#query-data-from-influxdb-with-python
"""

from src.classes.common_classes import SecretStore
from src.classes.influx_classes import InfluxConnector
from src.classes.query_classes import QueryBuilder
from src.helpers.consts import INFLUX_DEBUG_CONFIG_TITLE, INFLUX_QUERY_CONFIG_TITLE
from src.helpers.py_functions import read_query_settings, write_results_to_csv
from src.helpers.py_logger import create_logger


class QueryParser:
    """
    Contains all subfunctions which parse the query results
    """

    @staticmethod
    def parse_csv(query_result: dict) -> None:
        """
        Creating a CSV file from query results
        :param query_result: Input query result to write to CSV file
        """
        logging.info("Creating CSV file")
        try:
            write_results_to_csv(
                config_name=INFLUX_QUERY_CONFIG_TITLE, table=query_result
            )
        except IOError as err:
            logging.critical("Failed to write CSV file")
            raise err

    @staticmethod
    def parse_flux(query_result: dict) -> list:
        """
        Converts input flux string into a readable dictionary
        :param query_result: Input query result to write to readable format
        :return: Dictionary of key fields from the query
        # Dictionary format [{measurement, timestamp, field, value}, [...], [...]]
        """
        result_list = []
        for table in query_result:
            for record in table.records:
                result_list.append(
                    {
                        "_measurement": record.get_measurement(),
                        "_timestamp": record.get_time(),
                        "_field": record.get_field(),
                        "_value": record.get_value(),
                    }
                )
        return result_list

    @staticmethod
    def parse_stream(query_result: dict):
        """
        Not implemented
        :param query_result: Input stream string to read
        """
        raise NotImplementedError("parse_stream not implemented")


def execute_query(query: QueryBuilder) -> None:
    """
    Run command to be used under python interactive mode
    """
    query_mode = read_query_settings(INFLUX_QUERY_CONFIG_TITLE)
    query_result = None
    try:
        logging.info(f"Running query on in mode: {query_mode}")
        influx_connector.query_database(query_mode=query_mode, query=query)
        logging.info("Successfully ran query")
    except Exception as err:
        logging.critical(f"Failed to run query: {query}")
        raise err

    if query_mode == "csv":
        QueryParser.parse_csv(query_result=query_result)
    elif query_mode == "flux":
        flux = QueryParser.parse_flux(query_result=query_result)
        print(flux)
    else:
        QueryParser.parse_stream(query_result=query_result)


def run_example() -> None:
    """
    Use example query
    """
    print("Running example query")
    # from(bucket: "Bucket")
    #     |> range(start: -5m)
    #     |> filter(fn: (r) => r["_measurement"] == "fx-1" or r["_measurement"] == "mx-1")
    query_builder = QueryBuilder(bucket="Bucket", start_range="-5m")
    query_builder.append_filter(field="_measurement", value="fx-1", joiner="or")
    query_builder.append_filter(field="_measurement", value="mx-1")
    query_builder.append_filter("_measurement", "dc-1", new_band=True)
    execute_query(query_builder)


logging = create_logger(INFLUX_DEBUG_CONFIG_TITLE)
secret_store = SecretStore(has_mqtt_access=False, has_influx_access=True)
influx_connector = InfluxConnector(secret_store.influx_secrets)
logging.info("Attempting health check for InfluxDB")
try:
    influx_connector.health_check()
    logging.info("Successfully connected to InfluxDB server")
except Exception as error:
    logging.critical("Failed to connect InfluxDB server")
    raise error


def main() -> None:
    """
    Classes runtime which creates a query to an Influx database to view the tables
    """
    print(
        "To start run this file with 'python -i ./influx_query.py'\n"
        "Build a query using QueryBuilder() run QueryBuilder.help() for info\n"
        "***************\n"
        "Then run the following with your created query: run_int_query(query)\n"
        "Or run run_default() to run an example piece"
    )
    run_example()
