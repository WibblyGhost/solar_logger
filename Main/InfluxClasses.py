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
        self.filter_field = ''
        self.bucket = bucket
        self.start_range = start_range
        self.end_range = end_range

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
        :return:
        """
        self.query_string = self._append_from
        self.query_string += self._append_time_range
        self.query_string += self.filter_field
        return self.query_string

    @property
    def _append_from(self):
        """
        Adds from field to query, takes bucket attribute and appends to main string
        :param self.bucket: Influx database bucket to query
        """
        return f'from(bucket: "{self.bucket}")'

    @property
    def _append_time_range(self):
        """
        Adds time range to query, takes start range and optional end range
        Can use queries like '-10m' or datetime stamps
        :param self.start_range: The earliest time to include in results
        :param self.end_range: The latest time to include in results, defaults to now()
        """
        if self.end_range:
            return f'\n\t|> range(start: {self.start_range}, stop: {self.end_range})'
        else:
            return f'\n\t|> range(start: {self.start_range})'

    def append_filter(self, field_1, value_1, joiner=None):
        """
        Adds filter fields to the query, function is repeatable and cna therefore add  multiple filters
        :param field_1: Takes _measurement, _tag or _field
        :param value_1: Value you want the field to equal
        :param joiner: Optional join operator, can be 'And' / 'Or'
        """
        if not self.filter_field:
            self.filter_field = '\n\t|> filter(fn: (r) => '
        self.filter_field += f'["{field_1}"] == "{value_1}")'
        if joiner:
            self.filter_field = self.filter_field[:-1]
            self.filter_field += f' {joiner} '
