"""
Classes file, contains methods for the Influx database controller to do writes and queries to the database
"""
# Imports for Influx
from influxdb_client import InfluxDBClient
import logging


class InfluxController:
    """
    Class which creates a client to access and modify a connected database
    """
    influx_client = None
    influx_bucket = None
    influx_org = None

    def __init__(self, token, org, bucket, url):
        """
        :param token: Secret password to login to database with
        :param org: Organisation of the bucket to login to
        :param bucket: Database source
        :param url: Web address to connect to database
        """
        self._influx_token = token
        self._influx_url = url
        self.influx_org = org
        self.influx_bucket = bucket
        self.influx_client = InfluxDBClient

    def startup(self):
        """
        Defines the initialization of the InfluxController, invoking the connection to the InfluxDB and write API
        """
        logging.info('Connecting to InfluxDB')
        self._create_client()

    def _create_client(self):
        """
        :return: Client api which act commands on given database,
            on failure to connect it wil terminate the program
        """
        client = None
        try:
            client = InfluxDBClient(url=self._influx_url, token=self._influx_token, org=self.influx_org)
            logging.info(f'Connected to bucket: {self.influx_bucket}')
        except Exception as err:
            logging.error(f'Failed to connect to bucket: {self.influx_bucket}', err)
            raise ConnectionError
        finally:
            self.influx_client = client


class QueryBuilder:
    """
    Class which creates a query to send to the Influx database
    """
    query_string = None

    def __init__(self, bucket, start_range, end_range=None):
        """
        :param bucket:  Influx database bucket for query
        :param start_range: The earliest time to include in results
        :param end_range: The latest time to include in results, defaults to now()
        """
        self._filter_field = ''
        self._aggregate_field = ''
        self._sort_field = ''
        self._bucket = bucket
        self._start_range = start_range
        self._end_range = end_range

    def __str__(self):
        """
        :return: String representation of the query
        """
        return self._build_string()

    def __repr__(self):
        """
        :return: Raw representation of the query
        """
        return repr(self.__str__())

    def _build_string(self):
        """
        Creates basic string from set function variables
        :return: Built query in string form
        """
        self.query_string = self._append_from
        self.query_string += self._append_time_range
        self.query_string += self._filter_field
        self.query_string += self._aggregate_field
        self.query_string += self._sort_field
        return self.query_string

    @property
    def _append_from(self):
        """
        Adds from field to query, takes bucket attribute and appends to main string
        :param self.bucket: Influx database bucket to query
        """
        logging.debug('Created query from field')
        return f'from(bucket: "{self._bucket}")'

    @property
    def _append_time_range(self):
        """
        Adds time range to query, takes start range and optional end range
        Can use queries like '-10m' or datetime stamps
        :param self.start_range: The earliest time to include in results
        :param self.end_range: The latest time to include in results, defaults to now()
        """
        logging.debug('Created query time range field')
        if self._end_range:
            return f'\n\t|> range(start: {self._start_range}, stop: {self._end_range})'
        else:
            return f'\n\t|> range(start: {self._start_range})'

    def append_filter(self, field_1, value_1, joiner=None, new_band=False):
        """
        Adds filter fields to the query, function is repeatable and can therefore add  multiple filters
        :param new_band: If true, creates a new filter field instead of appending the filter field
        :param field_1: Takes _measurement, _tag or _field
        :param value_1: Value you want the field to equal
        :param joiner: Optional join operator, can be 'And' / 'Or'
        """
        logging.debug('Created query filter field')
        if not self._filter_field or new_band:
            self._filter_field += '\n\t|> filter(fn: (r) => '
        self._filter_field += f'r["{field_1}"] == "{value_1}")'
        if joiner:
            self._filter_field = self._filter_field[:-1]
            self._filter_field += f' {joiner} '

    def append_aggregate(self, collection_window, aggregate_function):
        """
        Adds an aggregation field to the query
        :param collection_window: Time frame for the data to aggregate
        :param aggregate_function: What function to apply to the window
        """
        logging.debug('Created query aggregate field')
        self._aggregate_field = f'\n\t|> aggregateWindow(every: {collection_window}, fn: {aggregate_function}'

    def append_sort(self, field, desc=False):
        """
        Adds a sort field to a query
        :param field: Field to sort results by
        :param desc: Ascending or descending
        """
        logging.debug('Created query sort field')
        self._sort_field = f'\n\t|> sort(columns: ["{field}"], desc: {desc}'
