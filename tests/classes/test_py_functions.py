# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

import logging
import os
from unittest import mock

import pytest
from pytest import LogCaptureFixture

from classes.custom_exceptions import MissingCredentialsError
from classes.py_functions import SecretStore, read_query_settings, write_results_to_csv
from tests.config.consts import FAKE


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


# TODO FIX THE ENV TEST CASES
def test_secret_store_reads_env(caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)
    env = {
            "mqtt_host": FAKE.pystr(),
            "mqtt_port": str(FAKE.pyint()),
            "mqtt_user": FAKE.pystr(),
            "mqtt_token": FAKE.pystr(),
            "mqtt_topic": FAKE.pystr(),
            "influx_url": FAKE.url(),
            "influx_org": FAKE.pystr(),
            "influx_bucket": FAKE.pystr(),
            "influx_token": FAKE.pystr(),
    }

    with mock.patch.dict(os.environ, env):
        secret_store = SecretStore(read_mqtt=True, read_influx=True)

    secret_env = dict(
        secret_store.mqtt_secrets,
        **secret_store.influx_secrets
    )
    assert env != secret_env
    assert "Reading MQTT environment variables" in caplog.text


# TODO FIX THE ENV TEST CASES
def test_secret_store_reads_influx_env(caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)
    env = {
            "mqtt_host": FAKE.pystr(),
            "mqtt_port": str(FAKE.pyint()),
            "mqtt_user": FAKE.pystr(),
            "mqtt_token": FAKE.pystr(),
            "mqtt_topic": FAKE.pystr(),
            "influx_url": FAKE.url(),
            "influx_org": FAKE.pystr(),
            "influx_bucket": FAKE.pystr(),
            "influx_token": FAKE.pystr(),
    }

    with mock.patch.dict(os.environ, env):
        secret_store = SecretStore(read_influx=True)
    env["mqtt_port"] = int(env["mqtt_port"])

    assert secret_store.mqtt_secrets != env
    assert secret_store.mqtt_secrets == {
        "mqtt_host": env["mqtt_host"],
        "mqtt_port": env["mqtt_port"],
        "mqtt_user": env["mqtt_user"],
        "mqtt_token": env["influx_token"],
        "mqtt_topic": env["mqtt_topic"]
    }
    assert "Reading MQTT environment variables" in caplog.text


# TODO FIX THE ENV TEST CASES
def test_secret_store_reads_influx_env(caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)


    with mock.patch.dict(os.environ, influx_env):
        secret_store = SecretStore(read_influx=True)

    assert secret_store.influx_secrets == influx_env
    assert "Reading Influx environment variables" in caplog.text

# TODO FIX THE ENV TEST CASES
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
