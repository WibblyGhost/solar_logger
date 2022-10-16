# pylint: disable=missing-function-docstring, missing-module-docstring
import logging

from influxdb_client import QueryApi, WriteApi
from pytest import LogCaptureFixture, mark, raises
from pytest_mock import MockerFixture

from src.classes.common_classes import QueuePackage
from src.classes.influx_classes import InfluxConnector
from tests.config.consts import FAKE, TestSecretStore


class TestInfluxConnector:
    """Test class for Influx Connector"""

    def test_passes_connector_init(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO)

        _ = InfluxConnector(secret_store=TestSecretStore)

        assert "Initializing InfluxDB client" in caplog.text
        assert "Initializing Influx write api" in caplog.text
        assert "Initializing Influx query api" in caplog.text

    def test_passes_health_check(
        self,
        mocker: MockerFixture,
        caplog: LogCaptureFixture,
    ):
        caplog.set_level(logging.INFO)
        influx_connector = InfluxConnector(secret_store=TestSecretStore)
        mocker.patch("src.classes.influx_classes.InfluxDBClient.ready")

        influx_connector.health_check()

    def test_passes_write_points(
        self, mocker: MockerFixture, caplog: LogCaptureFixture
    ):
        write_api = mocker.patch("src.classes.influx_classes.InfluxDBClient.write_api")
        write_api.return_value = mocker.MagicMock(WriteApi, return_value=None)
        caplog.set_level(logging.DEBUG)
        influx_connector = InfluxConnector(secret_store=TestSecretStore)
        queue_package = QueuePackage(
            measurement=FAKE.pystr(),
            time_field=FAKE.date_time(),
            field={FAKE.pystr(): FAKE.pyfloat(4)},
        )

        influx_connector.write_points(queue_package=queue_package)

    @mark.parametrize(
        "queue_package, error_message",
        [
            [None, "The received queue_packed has malformed data: queue_package empty"],
            [
                QueuePackage(
                    measurement=None,  # Bad data
                    time_field=FAKE.date_time(),
                    field={FAKE.pystr(): FAKE.pyfloat(4)},
                ),
                "The received queue_packed has malformed data: type of measurement not str",
            ],
            [
                QueuePackage(
                    measurement=FAKE.pystr(),
                    time_field=None,  # Bad data
                    field={FAKE.pystr(): FAKE.pyfloat(4)},
                ),
                "The received queue_packed has malformed data: type of time_field not, datetime",
            ],
            [
                QueuePackage(
                    measurement=FAKE.pystr(),
                    time_field=FAKE.date_time(),
                    field=None,  # Bad data
                ),
                "The received queue_packed has malformed data: type of field not, dict | str",
            ],
        ],
    )
    def test_fails_write_points_bad_data(
        self,
        mocker: MockerFixture,
        queue_package: str,
        error_message: str,
        caplog: LogCaptureFixture,
    ):
        write_api = mocker.patch("src.classes.influx_classes.InfluxDBClient.write_api")
        write_api.return_value = mocker.MagicMock(WriteApi, return_value=None)
        caplog.set_level(logging.DEBUG)
        influx_connector = InfluxConnector(secret_store=TestSecretStore)

        with raises(Exception) as err:
            influx_connector.write_points(queue_package=queue_package)
        assert str(err.value) == error_message

    @mark.parametrize("query_mode", ["csv", "flux", "stream"])
    def test_passes_query_database_modes_return(
        self, mocker: MockerFixture, query_mode: str, caplog: LogCaptureFixture
    ):
        query_api = mocker.patch("src.classes.influx_classes.InfluxDBClient.query_api")
        query_api.return_value = mocker.MagicMock(QueryApi)
        queue_package = FAKE.pystr()
        query_api.return_value.query_csv.return_value = queue_package
        query_api.return_value.query.return_value = queue_package
        query_api.return_value.query_stream.return_value = queue_package
        caplog.set_level(logging.DEBUG)

        caplog.set_level(logging.DEBUG)
        influx_connector = InfluxConnector(secret_store=TestSecretStore)
        result = influx_connector.query_database(
            query_mode=query_mode, query=queue_package
        )

        assert result is queue_package
        assert "Query to Influx server was successful" in caplog.text
