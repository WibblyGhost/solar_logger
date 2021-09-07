from datetime import datetime, timedelta

# import pandas as pd
import rx
from pytz import UTC
from rx import operators as ops

from influxdb_client import InfluxDBClient, Point, WriteOptions

with InfluxDBClient(url="http://localhost:8086", token="my-token", org="my-org") as _client:

    with _client.write_api(write_options=WriteOptions(batch_size=500,
                                                      flush_interval=10_000,
                                                      jitter_interval=2_000,
                                                      retry_interval=5_000,
                                                      max_retries=5,
                                                      max_retry_delay=30_000,
                                                      exponential_base=2)) as _write_client:

        """
        Write Line Protocol formatted as string
        """
        _write_client.write("my-bucket", "my-org", "h2o_feet,location=coyote_creek water_level=1.0 1")
        _write_client.write("my-bucket", "my-org", ["h2o_feet,location=coyote_creek water_level=2.0 2",
                                                    "h2o_feet,location=coyote_creek water_level=3.0 3"])

        """
        Write Line Protocol formatted as byte array
        """
        _write_client.write("my-bucket", "my-org", "h2o_feet,location=coyote_creek water_level=1.0 1".encode())
        _write_client.write("my-bucket", "my-org", ["h2o_feet,location=coyote_creek water_level=2.0 2".encode(),
                                                    "h2o_feet,location=coyote_creek water_level=3.0 3".encode()])

        """
        Write Dictionary-style object
        """
        _write_client.write("my-bucket", "my-org", {"measurement": "h2o_feet", "tags": {"location": "coyote_creek"},
                                                    "fields": {"water_level": 1.0}, "time": 1})
        _write_client.write("my-bucket", "my-org", [{"measurement": "h2o_feet", "tags": {"location": "coyote_creek"},
                                                     "fields": {"water_level": 2.0}, "time": 2},
                                                    {"measurement": "h2o_feet", "tags": {"location": "coyote_creek"},
                                                     "fields": {"water_level": 3.0}, "time": 3}])

        """
        Write Data Point
        """
        _write_client.write("my-bucket", "my-org",
                            Point("h2o_feet").tag("location", "coyote_creek").field("water_level", 4.0).time(4))
        _write_client.write("my-bucket", "my-org",
                            [Point("h2o_feet").tag("location", "coyote_creek").field("water_level", 5.0).time(5),
                             Point("h2o_feet").tag("location", "coyote_creek").field("water_level", 6.0).time(6)])

        """
        Write Observable stream
        """
        _data = rx \
            .range(7, 11) \
            .pipe(ops.map(lambda i: "h2o_feet,location=coyote_creek water_level={0}.0 {0}".format(i)))

        _write_client.write("my-bucket", "my-org", _data)

        # """
        # Write Pandas DataFrame
        # """
        # _now = datetime.now(UTC)
        # _data_frame = pd.DataFrame(data=[["coyote_creek", 1.0], ["coyote_creek", 2.0]],
        #                            index=[_now, _now + timedelta(hours=1)],
        #                            columns=["location", "water_level"])
        #
        # _write_client.write("my-bucket", "my-org", record=_data_frame,