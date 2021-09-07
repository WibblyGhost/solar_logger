# from SolarClasses import InfluxController
from InfluxClasses import QueryBuilder
from SecretStore import Secrets
from PyLogger import create_logger


"""
from(bucket: "Bucket")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fx-1" or r["_measurement"] == "mx-1")
"""


def create_query():
    influx_secret = Secrets.InfluxSecret
    qb = QueryBuilder(influx_secret.bucket, '-20d')
    qb.append_filter('_measurement', 'fx-1', 'and')
    qb.append_filter('_measurement', 'mx-1')
    query = str(qb)
    logging.info(f"Created query:\n{query}")


def main():
    """
    Main runtime which creates a query to an Influx database to view the tables
    """
    create_query()


if __name__ == '__main__':
    logging = create_logger('influx_debugger')
    main()
