"""
Program which creates and runs Influx database queries
Check the Influx query documentation for query syntax:
https://docs.influxdata.com/influxdb/v2.0/api-guide/client-libraries/python/#query-data-from-influxdb-with-python
"""
from classes.influx_classes import InfluxController, QueryBuilder
from classes.py_functions import create_logger, csv_writer, read_query_settings
import private

QUERY_CONFIG_TITLE = 'query_settings'
DEBUG_CONFIG_TITLE = 'influx_debugger'


def parse_csv(csv_file):
    """
    Creating a CSV file from query results
    :param csv_file: Input csv string to write to file
    """

    logging.info('Creating CSV file')
    try:
        csv_writer(config_name='query_settings', table=csv_file)
    except IOError:
        logging.ERROR(f'Failed to write CSV file')


def parse_flux(flux_file):
    """
    Converts input flux string into a readable dictionary
    :param flux_file: Input flux string to write to read
    :return: Dictionary of key fields from the query
    # Dictionary format [{measurement, timestamp, field, value}, [...], [...]]
    """
    result_list = []
    for table in flux_file:
        for record in table.records:
            result_list.append({'_measurement': record.get_measurement(),
                                '_timestamp': record.get_time(),
                                '_field': record.get_field(),
                                '_value': record.get_value()})
    return result_list


def parse_stream(stream_file):
    """
    TODO: Not implemented
    :param stream_file: Input stream string to read
    """
    pass


def run_query(influx_db, query, query_mode='csv'):
    """
    Runs given query on Influx database and print results
    :param query_mode: Defines what mode to run the query in, supports 'csv', 'flux' and 'stream'
    :param influx_db: Influx controller to run queries
    :param query: Input query to run on Influx database
    """
    query_result = None
    logging.info(f'Created write api on bucket: {influx_db.influx_bucket}')
    query_api = influx_db.influx_client.query_api()
    logging.info('Running query on bucket')
    try:
        logging.info(f'Running query on bucket ({influx_db.influx_bucket}) in mode: {query_mode}')
        if query_mode == 'csv':
            query_result = query_api.query_csv(org=influx_db.influx_org, query=query)
        elif query_mode == 'flux':
            query_result = query_api.query(org=influx_db.influx_org, query=query)
        elif query_mode == 'stream':
            query_result = query_api.query_stream(org=influx_db.influx_org, query=query)
        logging.info('Successfully ran query')
    except Exception as err:
        logging.ERROR("Failed to run query, invalid syntax", err)
        raise SyntaxError
    return query_result


def create_influx_controller(influx_secret) -> InfluxController:
    """
    :param influx_secret: Class of secrets to connect to the Influx database
    :return: InfluxController instance to run queries on
    """
    database = InfluxController(influx_secret.token,
                                influx_secret.org,
                                influx_secret.bucket,
                                influx_secret.url)
    database.startup()
    return database


def main():
    """
    classes runtime which creates a query to an Influx database to view the tables
    """
    influx_secret = private.InfluxSecret
    influx_db = create_influx_controller(influx_secret)
    # Creating query for Influx, see example:
    # query = 'from(bucket:"bucket_name") \
    #           |> range(start: -10m) \
    #           |> filter(fn:(r) => r._measurement == "my_measurement") \
    #           |> filter(fn: (r) => r.location == "Prague") \
    #           |> filter(fn:(r) => r._field == "temperature" )'
    qb = QueryBuilder(bucket=influx_db.influx_bucket, start_range='-20d')
    qb.append_filter('_measurement', 'fx-1', 'or')
    qb.append_filter('_measurement', 'mx-1')
    # qb.append_filter('_measurement', 'dc-1', new_band=True)
    logging.info(f"Created query:\n{qb}")
    query_mode = read_query_settings(QUERY_CONFIG_TITLE)
    query_result = run_query(influx_db=influx_db, query=str(qb), query_mode=query_mode)
    if query_mode == 'csv':
        parse_csv(query_result)
    elif query_mode == 'flux':
        flux = parse_flux(query_result)
    elif query_mode == 'stream':
        # TODO: Not implemented
        parse_stream(query_result)


if __name__ == '__main__':
    logging = create_logger(DEBUG_CONFIG_TITLE)
    main()
