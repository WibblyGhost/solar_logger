"""
Program which creates and runs Influx database queries
Check the Influx query documentation for query syntax:
https://docs.influxdata.com/influxdb/v2.0/api-guide/client-libraries/python/#query-data-from-influxdb-with-python
"""

from classes.influx_classes import (
    InfluxConnector,
    create_influx_connector,
)
from classes.py_functions import SecretStore, read_query_settings, write_results_to_csv
from classes.py_logger import create_logger
from classes.query_classes import QueryBuilder
from config.consts import INFLUX_DEBUG_CONFIG_TITLE, INFLUX_QUERY_CONFIG_TITLE


def parse_csv(csv_file: dict) -> None:
    """
    Creating a CSV file from query results
    :param csv_file: Input csv string to write to file
    """
    logging.info("Creating CSV file")
    try:
        write_results_to_csv(config_name=INFLUX_QUERY_CONFIG_TITLE, table=csv_file)
    except IOError as err:
        logging.error("Failed to write CSV file")
        raise err


def parse_flux(flux_file: dict) -> list:
    """
    Converts input flux string into a readable dictionary
    :param flux_file: Input flux string to write to read
    :return: Dictionary of key fields from the query
    # Dictionary format [{measurement, timestamp, field, value}, [...], [...]]
    """
    result_list = []
    for table in flux_file:
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


def parse_stream(stream_file):
    """
    Not implemented
    :param stream_file: Input stream string to read
    """
    raise NotImplementedError("parse_stream not implemented.")


def query_influx_server(
    influx_db: InfluxConnector, query: str, query_mode: str = "csv"
) -> any:
    """
    Runs given query on Influx database and print results
    :param query_mode: Defines what mode to run the query in, supports "csv", "flux" and "stream"
    :param influx_db: Influx controller to run queries
    :param query: Input query to run on Influx database
    """
    query_result = None
    logging.info(f"Created write api on bucket: {influx_db.influx_bucket}")
    query_api = influx_db.influx_client.query_api()
    logging.info("Running query on bucket")
    try:
        logging.info(
            f"Running query on bucket ({influx_db.influx_bucket}) in mode: {query_mode}"
        )
        if query_mode == "csv":
            query_result = query_api.query_csv(org=influx_db.influx_org, query=query)
        elif query_mode == "flux":
            query_result = query_api.query(org=influx_db.influx_org, query=query)
        elif query_mode == "stream":
            query_result = query_api.query_stream(org=influx_db.influx_org, query=query)
        logging.info("Successfully ran query")
    except Exception as err:
        logging.error(f"Failed to run query, returned error: {err}\n{query}")
        raise err
    return query_result


def execute_query(query: QueryBuilder) -> None:
    """
    Run command to be used under python interactive mode.
    """
    query_mode = read_query_settings(INFLUX_QUERY_CONFIG_TITLE)
    query_result = query_influx_server(
        influx_db=influx_db_connector, query=str(query), query_mode=query_mode
    )
    if query_mode == "csv":
        parse_csv(query_result)
    elif query_mode == "flux":
        flux = parse_flux(query_result)
        print(flux)
    else:
        raise NotImplementedError(f"{query_mode} not supported.")


def run_default() -> None:
    """
    Use example query
    """
    # from(bucket: "Bucket")
    #     |> range(start: -5m)
    #     |> filter(fn: (r) => r["_measurement"] == "fx-1" or r["_measurement"] == "mx-1")
    query = QueryBuilder(bucket=influx_db_connector.influx_bucket, start_range="-5m")
    query.append_filter(field="_measurement", value="fx-1", joiner="or")
    query.append_filter(field="_measurement", value="mx-1")
    # q_b.append_filter("_measurement", "dc-1", new_band=True)
    execute_query(query)


def main() -> None:
    """
    Classes runtime which creates a query to an Influx database to view the tables.
    """
    print(
        "To start run this file with 'python -i ./influx_query.py'\n"
        "Build a query using QueryBuilder() run QueryBuilder.help() for info.\n"
        "***************\n"
        "Then run the following with your created query: run_int_query(query).\n"
        "Or run run_default() to run an example piece."
    )
    # run_default()


if __name__ == "__main__":
    logging = create_logger(INFLUX_DEBUG_CONFIG_TITLE)
    secret_store = SecretStore(read_mqtt=False, read_influx=True)
    influx_db_connector = create_influx_connector(secret_store.influx_secrets)
    main()
