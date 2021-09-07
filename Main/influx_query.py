"""
Program which creates and runs Influx database queries
Check the Influx query documentation for query syntax:
https://docs.influxdata.com/influxdb/v2.0/api-guide/client-libraries/python/#query-data-from-influxdb-with-python
"""
from influx_classes import InfluxController, QueryBuilder
from SecretStore import secrets
from py_functions import create_logger, csv_writer


def run_query(influx_db, query):
    """
    Runs given query on Influx database and print results
    :param influx_db: Influx controller to run queries
    :param query: Input query to run on Influx database
    """
    logging.info(f'Created write api on bucket: {influx_db.influx_bucket}')
    query_api = influx_db.influx_client.query_api()
    logging.info('Running query on bucket')
    try:
        result = query_api.query_csv(org=influx_db.influx_org, query=query)
        logging.info('Successfully ran query')
    except Exception as err:
        logging.ERROR("Failed to run query, invalid syntax", err)
        raise SyntaxError
    # Creating a CSV file from results
    logging.info('Creating csv file')
    try:
        csv_writer('query_settings', table=result)
    except IOError:
        logging.ERROR(f'Failed to write CSV file')


def create_influx(influx_secret) -> InfluxController:
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
    Main runtime which creates a query to an Influx database to view the tables
    """
    influx_secret = secrets.InfluxSecret
    influx_db = create_influx(influx_secret)
    # Creating query for Influx, see example:
    # query = 'from(bucket:"bucket_name") \
    #           |> range(start: -10m) \
    #           |> filter(fn:(r) => r._measurement == "my_measurement") \
    #           |> filter(fn: (r) => r.location == "Prague") \
    #           |> filter(fn:(r) => r._field == "temperature" )'
    qb = QueryBuilder(bucket=influx_db.influx_bucket, start_range='-20d')
    # qb.append_filter('_measurement', 'fx-1', 'or')
    qb.append_filter('_measurement', 'mx-1')
    logging.info(f"Created query:\n{qb}")
    run_query(influx_db=influx_db, query=str(qb))


if __name__ == '__main__':
    logging = create_logger('influx_debugger')
    main()
