# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

import logging
import os
from unittest import mock

import pytest
from pytest import LogCaptureFixture

from classes.custom_exceptions import MissingCredentialsError
from classes.py_functions import SecretStore, read_query_settings, write_results_to_csv
from tests.config.consts import FAKE, TEST_ENV_FULL, TEST_INFLUX_ENV, TEST_MQTT_ENV


@mock.patch("classes.py_functions.os.path.exists")
@mock.patch("classes.py_functions.open", mock.mock_open())
def test_passes_write_to_csv(exists, caplog: LogCaptureFixture):
    exists.return_value = True
    caplog.set_level(logging.INFO)
    with mock.patch(
        "configparser.ConfigParser.read", return_value=FAKE.pystr()
    ) and mock.patch("configparser.ConfigParser.get", return_value=FAKE.pystr()):
        write_results_to_csv(FAKE.pystr(), FAKE.pydict())

    assert "Wrote rows into CSV file at:" in caplog.text


def test_passes_read_query_settings():
    with mock.patch(
        "configparser.ConfigParser.read", return_value=FAKE.pystr()
    ) and mock.patch("configparser.ConfigParser.get", return_value=FAKE.pystr()):
        result = read_query_settings("query_settings")

    assert result is not None


def test_passes_secret_store_reads_env(caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)

    with mock.patch.dict(os.environ, TEST_ENV_FULL):
        secret_store = SecretStore(has_mqtt_access=True, has_influx_access=True)
    joined_secret_store = dict(secret_store.influx_secrets, **secret_store.mqtt_secrets)
    test_env_copy = TEST_ENV_FULL.copy()
    test_env_copy["mqtt_port"] = int(TEST_ENV_FULL["mqtt_port"])

    assert "Reading MQTT environment variables" in caplog.text
    assert "Reading Influx environment variables" in caplog.text
    assert joined_secret_store == test_env_copy


def test_passes_secret_store_reads_mqtt_env(caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)

    with mock.patch.dict(os.environ, TEST_ENV_FULL):
        secret_store = SecretStore(has_mqtt_access=True)
    mqtt_env_copy = TEST_MQTT_ENV.copy()
    mqtt_env_copy["mqtt_port"] = int(TEST_MQTT_ENV["mqtt_port"])

    assert "Reading MQTT environment variables" in caplog.text
    assert "Reading Influx environment variables" not in caplog.text
    assert secret_store.mqtt_secrets == mqtt_env_copy


def test_passes_secret_store_reads_influx_env(caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)

    with mock.patch.dict(os.environ, TEST_ENV_FULL):
        secret_store = SecretStore(has_influx_access=True)

    assert "Reading MQTT environment variables" not in caplog.text
    assert "Reading Influx environment variables" in caplog.text
    assert secret_store.influx_secrets == TEST_INFLUX_ENV


def test_fails_secret_store_reads_none(caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)

    with mock.patch.dict(os.environ, TEST_ENV_FULL):
        _ = SecretStore()

    assert "Reading MQTT environment variables" not in caplog.text
    assert "Reading Influx environment variables" not in caplog.text


def test_fails_secret_store_empty_values(caplog: LogCaptureFixture):
    caplog.set_level(logging.CRITICAL)

    mqtt_env_copy = TEST_ENV_FULL.copy()
    mqtt_env_copy["mqtt_user"] = ""
    mqtt_env_copy["influx_url"] = ""

    with mock.patch.dict(os.environ, mqtt_env_copy):
        with pytest.raises(MissingCredentialsError) as err:
            _ = SecretStore(has_mqtt_access=True, has_influx_access=True)

    assert "Ran into error when reading environment variables" in caplog.text
    assert str(err.value) == "Ran into error when reading environment variables"
