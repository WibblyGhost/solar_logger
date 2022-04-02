# pylint: disable=missing-function-docstring, missing-module-docstring

import os
import logging
from unittest import mock

from faker import Faker
from pytest import LogCaptureFixture
import pytest

from classes.custom_exceptions import MissingCredentialsError
from classes.py_functions import SecretStore, read_query_settings, write_results_to_csv

FAKE = Faker()


@mock.patch("classes.py_functions.os.path.exists")
@mock.patch("classes.py_functions.open", mock.mock_open())
def test_write_results_to_csv(exists, caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)
    exists.return_value = True

    with mock.patch(
        "configparser.ConfigParser.read", return_value=FAKE.pystr()
    ) and mock.patch("configparser.ConfigParser.get", return_value=FAKE.pystr()):
        write_results_to_csv(FAKE.pystr(), FAKE.pydict())

    assert "Wrote rows into CSV file at:" in caplog.text


def test_read_query_settings_returns_string():
    result = read_query_settings("query_settings")

    assert result is not None
    assert isinstance(result, str)


def test_secret_store_reads_mqtt_env(caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)
    mqtt_env = {
        "mqtt_host": FAKE.pystr(),
        "mqtt_port": str(FAKE.pyint(4)),
        "mqtt_user": FAKE.pystr(),
        "mqtt_token": FAKE.pystr(),
        "mqtt_topic": FAKE.pystr(),
    }

    with mock.patch.dict(os.environ, mqtt_env):
        secret_store = SecretStore(read_mqtt=True)
    mqtt_env["mqtt_port"] = int(mqtt_env["mqtt_port"])

    assert secret_store.mqtt_secrets == mqtt_env
    assert "Read MQTT environment variables" in caplog.text


def test_secret_store_reads_influx_env(caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)
    influx_env = {
        "influx_url": FAKE.url(),
        "influx_org": FAKE.pystr(),
        "influx_bucket": FAKE.pystr(),
        "influx_token": FAKE.pystr(),
    }

    with mock.patch.dict(os.environ, influx_env):
        secret_store = SecretStore(read_influx=True)

    assert secret_store.influx_secrets == influx_env
    assert "Read Influx environment variables" in caplog.text


def test_secret_store_asserts_on_empty_env():
    env_file = {
        "mqtt_host": "",
        "mqtt_port": "",
        "mqtt_user": "",
        "mqtt_token": "",
        "mqtt_topic": "",
        "influx_url": "",
        "influx_org": "",
        "influx_bucket": "",
        "influx_token": "",
    }

    with pytest.raises(MissingCredentialsError) as err:
        with mock.patch.dict(os.environ, env_file):
            SecretStore(read_influx=True, read_mqtt=True)
    assert str(err.value) == "Missing secret credential for MQTT in the .env"
