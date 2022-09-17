# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring


import logging
from unittest import mock

import pytest
from influxdb_client import QueryApi, WriteApi
from pytest import LogCaptureFixture

from classes.common_classes import QueuePackage
from classes.influx_classes import InfluxConnector
from tests.config.consts import FAKE, TestSecretStore


class TestInfluxConnector:
    """Test class for Influx Connector"""

    def test_passes_connector_init(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO)

        _ = InfluxConnector(secret_store=TestSecretStore)

        assert "Initializing InfluxDB client" in caplog.text
        assert "Initializing Influx write api" in caplog.text
        assert "Initializing Influx query api" in caplog.text

    def test_passes_health_check(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO)
        influx_connector = InfluxConnector(secret_store=TestSecretStore)

        with mock.patch("classes.influx_classes.InfluxDBClient.ready"):
            influx_connector.health_check()

    @mock.patch("classes.influx_classes.InfluxDBClient.write_api")
    def test_passes_write_points(self, write_api, caplog: LogCaptureFixture):
        write_api.return_value = mock.MagicMock(WriteApi, return_value=None)
        caplog.set_level(logging.DEBUG)
        influx_connector = InfluxConnector(secret_store=TestSecretStore)
        queue_package = QueuePackage(
            measurement=FAKE.pystr(),
            time_field=FAKE.date_time(),
            field={FAKE.pystr(): FAKE.pyfloat(4)},
        )

        influx_connector.write_points(queue_package=queue_package)

    @pytest.mark.parametrize(
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
    @mock.patch("classes.influx_classes.InfluxDBClient.write_api")
    def test_fails_write_points_bad_data(
        self, write_api, queue_package, error_message, caplog: LogCaptureFixture
    ):
        write_api.return_value = mock.MagicMock(WriteApi, return_value=None)
        caplog.set_level(logging.DEBUG)
        influx_connector = InfluxConnector(secret_store=TestSecretStore)

        with pytest.raises(Exception) as err:
            influx_connector.write_points(queue_package=queue_package)
        assert str(err.value) == error_message

    @pytest.mark.parametrize("query_mode", ["csv", "flux", "stream"])
    @mock.patch("classes.influx_classes.InfluxDBClient.query_api")
    def test_passes_query_database_modes_return(
        self, query_api, query_mode, caplog: LogCaptureFixture
    ):
        query_api.return_value = mock.MagicMock(QueryApi)
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
