# pylint: disable=missing-function-docstring, missing-module-docstring

import logging
import time
from unittest import mock

import pytest
from pytest import LogCaptureFixture
from faker import Faker

from config.consts import ERROR_COUNTS
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
def test_influx_startup_fails(influx_ready, caplog: LogCaptureFixture):
    influx_ready.side_effect = Exception
    caplog.set_level(logging.WARNING)
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
    assert ERROR_COUNTS.contiguous_influx_errors == 0


def test_influx_write_exception_count_increases_on_error(caplog: LogCaptureFixture):
    caplog.set_level(logging.WARNING)
    msg_time = FAKE.date_time()
    msg_payload_bad = {"fields": FAKE.pystr()}
    msg_type = FAKE.pystr()
    influx_connector = mock.MagicMock(InfluxConnector)

    influx_db_write_points(
        msg_time=msg_time,
        msg_payload=msg_payload_bad,
        msg_type=msg_type,
        influx_connector=influx_connector,
    )

    assert "Failed to run write, returned error:" in caplog.text
    assert (
        f"Contiguous Influx errors increased to {ERROR_COUNTS.contiguous_influx_errors}"
        in caplog.text
    )
    assert ERROR_COUNTS.contiguous_influx_errors > 0


def test_influx_write_exception_count_exceeds_max(caplog: LogCaptureFixture):
    caplog.set_level(logging.CRITICAL)
    msg_time = FAKE.date_time()
    msg_payload_bad = {"fields": FAKE.pystr()}
    msg_type = FAKE.pystr()
    influx_connector = mock.MagicMock(InfluxConnector)

    with pytest.raises(Exception):
        for _ in range(0, ERROR_COUNTS.max_influx_errors):
            influx_db_write_points(
                msg_time=msg_time,
                msg_payload=msg_payload_bad,
                msg_type=msg_type,
                influx_connector=influx_connector,
            )

    assert (
        f"Contiguous Influx errors has exceceded max count, \
                    {ERROR_COUNTS.max_influx_errors}\n--quitting--"
        in caplog.text
    )
    assert ERROR_COUNTS.contiguous_influx_errors > 0


def test_influx_write_exception_count_resets(caplog: LogCaptureFixture):
    caplog.set_level(logging.WARNING)
    msg_time = FAKE.date_time()
    msg_payload_good = {"fields": FAKE.pyint()}
    msg_payload_bad = {"fields": FAKE.pystr()}
    msg_type = FAKE.pystr()
    influx_connector = mock.MagicMock(InfluxConnector)

    for _ in range(0, ERROR_COUNTS.max_influx_errors):
        influx_db_write_points(
            msg_time=msg_time,
            msg_payload=msg_payload_bad,
            msg_type=msg_type,
            influx_connector=influx_connector,
        )
        time.sleep(0.2)
        influx_db_write_points(
            msg_time=msg_time,
            msg_payload=msg_payload_good,
            msg_type=msg_type,
            influx_connector=influx_connector,
        )
        time.sleep(0.2)

    assert ERROR_COUNTS.contiguous_influx_errors < ERROR_COUNTS.max_influx_errors
