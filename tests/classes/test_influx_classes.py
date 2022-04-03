# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring


import logging
from unittest import mock
from pytest import LogCaptureFixture
import pytest

from classes.influx_classes import InfluxConnector
from tests.config.consts import MockedSecretStore


def test_passes_connector_init(caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)
    _ = InfluxConnector(secret_store=MockedSecretStore)

    assert "Initializing InfluxDB client" in caplog.text
    assert "Initializing Influx write api" in caplog.text
    assert "Initializing Influx query api" in caplog.text


def test_passes_health_check(caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)
    influx_connector = InfluxConnector(secret_store=MockedSecretStore)

    with mock.patch("classes.influx_classes.InfluxDBClient.ready"):
        influx_connector.health_check()

    assert "Influx health check succeeded" in caplog.text


def test_fails_health_check():
    influx_connector = InfluxConnector(secret_store=MockedSecretStore)

    with mock.patch(
        "classes.influx_classes.InfluxDBClient.ready", side_effect=Exception
    ):
        with pytest.raises(Exception):
            influx_connector.health_check()


# def test_passes_write_points(caplog: LogCaptureFixture):
#     caplog.set_level(logging.DEBUG)
#     influx_connector = InfluxConnector(secret_store=MockedSecretStore)
#     queue_package = QueuePackage(
#         measurement=FAKE.pystr(),
#         time_field=FAKE.date_time(),
#         field={FAKE.pystr(): FAKE.pyfloat(4)},
#     )
#     # from influxdb_client.client.write
#     # from influxdb_client.client.write_api import WriteApi
#     with mock.patch(
#         "classes.influx_classes.InfluxDBClient.client.write", mock.MagicMock(WriteApi)
#     ):
#         influx_connector.write_points(queue_package=queue_package)

#     # assert f"Wrote point: " in caplog.text


# def test_write_points_with_bad_data_raises_exception(caplog: LogCaptureFixture):
#     caplog.set_level(logging.DEBUG)
#     influx_connector = InfluxConnector(secret_store=MockedSecretStore)
#     msg_time = FAKE.date_time()
#     msg_type = FAKE.pystr()
#     msg_payload_bad = {FAKE.pystr(): FAKE.pystr()}

#     with pytest.raises(Exception) as err:
#         influx_connector.write_points(
#             msg_time=msg_time, msg_type=msg_type, msg_payload=msg_payload_bad
#         )
#     assert err.type == ValueError


# def test_write_points_raises_connection_exception(caplog: LogCaptureFixture):
#     caplog.set_level(logging.DEBUG)
#     influx_connector = InfluxConnector(secret_store=MockedSecretStore)
#     msg_time = FAKE.date_time()
#     msg_type = FAKE.pystr()
#     msg_payload = {FAKE.pystr(): str(FAKE.pyfloat())}

#     with pytest.raises(Exception) as err:
#         influx_connector.write_points(
#             msg_time=msg_time, msg_type=msg_type, msg_payload=msg_payload
#         )
#     assert err.type == ValueError


# return_data = {FAKE.pystr(): FAKE.pystr()}


# @pytest.mark.parametrize("query_mode", ["csv", "flux", "stream"])
# @mock.patch(
#     "classes.influx_classes.InfluxDBClient.query_api.query_csv",
#     return_value=return_data,
# )
# @mock.patch(
#     "classes.influx_classes.InfluxDBClient.query_api.query", return_value=return_data
# )
# @mock.patch(
#     "classes.influx_classes.InfluxDBClient.query_api.query_stream",
#     return_value=return_data,
# )
# def test_query_succeeds(query_mode, caplog: LogCaptureFixture):
#     caplog.set_level(logging.DEBUG)
#     influx_connector = InfluxConnector(secret_store=MockedSecretStore)
#     query = FAKE.pystr()

#     result = influx_connector.query_database(query_mode=query_mode, query=query)

#     assert result == return_data
