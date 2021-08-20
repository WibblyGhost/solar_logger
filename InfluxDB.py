"""
Program which connects to an InfluxDB and invokes querying, connection and writing commands to the database
"""

from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from secrets import InfluxDB as Secret
import json
# TODO: Fix this class


class InfluxController:
    """ Enter Comment """

    def __init__(self, token, org, bucket, bucket_id, host, client=None):
        """
        :param token: Secret password to login to database with
        :param org: Organisation of the bucket to login to
        :param bucket: Database source
        :param bucket_id: Identification of bucket
        :param host: Web address to connect to database
        :param client: Existing database connection, default is None
        """
        self.token = token
        self.org = org
        self.bucket = bucket
        self.bucket_id = bucket_id
        self.host = host
        self.client = client

    def connect_db(self):
        """
        :return: Success of database connection
        """
        try:
            self.client = InfluxDBClient(url=self.host, token=self.token)
            return True
        except:
            return False

    def query_db(self, query):
        """
        :param query: Query string to send to database
        :return q_result: Result of the query
        """
        try:
            tables = self.client.query_api().query(query, self.org)
            # tables = client.query_api().query(query, org=org)
            pass
        except:
            return None

    def write_db(self, db_point):
        """
        :param db_point:
        :return: Success of database write
        """
        try:
            write_api = self.client.write_api(write_options=SYNCHRONOUS)

            point = Point("mem") \
                .field("used_allocation", 200) \
                .time(datetime.utcnow(), WritePrecision.NS)

            write_api.write(self.bucket, self.org, point)
            return True
        except:
            return False


def main():
    print("Hello")
    database = InfluxController(Secret.token,
                                Secret.org,
                                Secret.bucket,
                                Secret.bucket_id,
                                Secret.host)
    # Write points to database
    bucket = Secret.bucket
    query = f'from(bucket: \"{bucket}\") |> range(start: -1h)'
    database.query_db(query)
    json_body = [
        {
            "measurement": "brushEvents",
            "tags": {
                "user": "Carol",
                "brushId": "6c89f539-71c6-490d-a28d-6c5d84c0ee2f"
            },
            "time": "2018-03-28T8:01:00Z",
            "fields": {
                "duration": 127
            }
        },
        {
            "measurement": "brushEvents",
            "tags": {
                "user": "Carol",
                "brushId": "6c89f539-71c6-490d-a28d-6c5d84c0ee2f"
            },
            "time": "2018-03-29T8:04:00Z",
            "fields": {
                "duration": 132
            }
        },
        {
            "measurement": "brushEvents",
            "tags": {
                "user": "Carol",
                "brushId": "6c89f539-71c6-490d-a28d-6c5d84c0ee2f"
            },
            "time": "2018-03-30T8:02:00Z",
            "fields": {
                "duration": 129
            }
        }
    ]
    # database.insert_db(json_body)


if __name__ == '__main__':
    main()
