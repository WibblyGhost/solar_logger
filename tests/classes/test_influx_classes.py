# pylint: disable=missing-function-docstring

import logging
from unittest import mock

import pytest
from config.consts import MaxErrorCounts
from faker import Faker
from pytest import LogCaptureFixture

from classes.custom_exceptions import MissingCredentialsError
from classes.influx_classes import (
    InfluxConnector,
    create_influx_connector,
    influx_db_write_points,
)

FAKE = Faker()


@mock.patch("classes.influx_classes.InfluxDBClient.ready", mock.MagicMock())
def test_influx_startup_succeeds(caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)
    url = FAKE.url()
    org = FAKE.pystr()
    bucket = FAKE.pystr()
    token = FAKE.pystr()
    influx_connector = InfluxConnector(url=url, org=org, bucket=bucket, token=token)

    try:
        influx_connector.influx_startup()
    except Exception as err:
        assert False, f"influx_startup failed {err}"
    assert "Attempting to connect to InfluxDB server" in caplog.text
    assert "Successfully connected to InfluxDB server" in caplog.text


@mock.patch("classes.influx_classes.InfluxDBClient.ready")
def test_influx_startup_fails(mocked_ready, caplog: LogCaptureFixture):
    mocked_ready.side_effect = Exception
    caplog.set_level(logging.ERROR)
    url = FAKE.url()
    org = FAKE.pystr()
    bucket = FAKE.pystr()
    token = FAKE.pystr()

    influx_connector = InfluxConnector(url=url, org=org, bucket=bucket, token=token)

    with pytest.raises(Exception):
        influx_connector.influx_startup()
    assert "Failed to connect InfluxDB server" in caplog.text


def test_create_influx_connector_succeeds():
    influx_secrets = {
        "influx_url": FAKE.url(),
        "influx_org": FAKE.pystr(),
        "influx_bucket": FAKE.pystr(),
        "influx_token": FAKE.pystr(),
    }

    with mock.patch("classes.influx_classes.InfluxConnector.influx_startup"):
        influx_connector = create_influx_connector(influx_secrets=influx_secrets)

    assert isinstance(influx_connector, InfluxConnector)


def test_create_influx_connector_fails():
    influx_secrets = {
        "influx_url": "",
        "influx_org": FAKE.pystr(),
        "influx_bucket": FAKE.pystr(),
        "influx_token": FAKE.pystr(),
    }

    with mock.patch("classes.influx_classes.InfluxConnector.influx_startup"):
        with pytest.raises(MissingCredentialsError) as err:
            _ = create_influx_connector(influx_secrets=influx_secrets)
    assert "Missing secret credential for InfluxDB in the .env," in str(err.value)


def test_influx_write_points_succeed(caplog: LogCaptureFixture):
    caplog.set_level(logging.DEBUG)
    msg_time = FAKE.date_time()
    msg_payload = {"fields": FAKE.pyint()}
    msg_type = FAKE.pystr()
    influx_connector = mock.MagicMock(InfluxConnector)

    influx_db_write_points(
        msg_time=msg_time,
        msg_payload=msg_payload,
        msg_type=msg_type,
        influx_connector=influx_connector,
    )

    assert "Creating database points from" in caplog.text
    assert "Wrote point: " in caplog.text
    assert MaxErrorCounts.continuous_influx_errors == 0


def test_influx_write_exception_logs_error(caplog: LogCaptureFixture):
    caplog.set_level(logging.ERROR)
    msg_time = FAKE.date_time()
    msg_payload = {"fields": FAKE.pystr()}
    msg_type = FAKE.pystr()
    influx_connector = mock.MagicMock(InfluxConnector)

    influx_db_write_points(
        msg_time=msg_time,
        msg_payload=msg_payload,
        msg_type=msg_type,
        influx_connector=influx_connector,
    )

    assert "Failed to run write, returned error:" in caplog.text
    assert (
        f"Continuous influx errors increased to {MaxErrorCounts.continuous_influx_errors}"
        in caplog.text
    )
    assert MaxErrorCounts.continuous_influx_errors > 0


def test_influx_write_exception_exceeds_no_max_errors(caplog: LogCaptureFixture):
    caplog.set_level(logging.CRITICAL)
    msg_time = FAKE.date_time()
    msg_payload = {"fields": FAKE.pystr()}
    msg_type = FAKE.pystr()
    influx_connector = mock.MagicMock(InfluxConnector)

    with pytest.raises(Exception):
        for _ in range(0, MaxErrorCounts.max_influx_errors):
            influx_db_write_points(
                msg_time=msg_time,
                msg_payload=msg_payload,
                msg_type=msg_type,
                influx_connector=influx_connector,
            )

    assert (
        f"Continuous influx errors has exceceded max count, {MaxErrorCounts.max_influx_errors}"
        in caplog.text
    )
    assert MaxErrorCounts.continuous_influx_errors > 0
