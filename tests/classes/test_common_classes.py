# pylint: disable=missing-function-docstring, missing-module-docstring
import logging
import os

from pytest import LogCaptureFixture, raises
from pytest_mock import MockerFixture

from src.classes.common_classes import SecretStore
from src.classes.custom_exceptions import MissingCredentialsError
from tests.config.consts import (
    TEST_EMPTY_ENV,
    TEST_ENV_FULL,
    TEST_INFLUX_ENV,
    TEST_MAX_PORT_RANGE,
    TEST_MQTT_ENV,
)


class TestSecretStore:
    """Test class for the Secret Store"""

    def test_passes_secret_store_reads_full_env(
        self, mocker: MockerFixture, caplog: LogCaptureFixture
    ):
        caplog.set_level(logging.INFO)
        full_env_copy = TEST_ENV_FULL.copy()
        full_env_copy["MQTT_PORT"] = int(TEST_ENV_FULL["MQTT_PORT"])
        full_env_copy = {key.lower(): value for key, value in full_env_copy.items()}
        mocker.patch.dict(os.environ, TEST_ENV_FULL)

        secret_store = SecretStore(has_mqtt_access=True, has_influx_access=True)
        joined_secret_store = dict(
            secret_store.influx_secrets, **secret_store.mqtt_secrets
        )

        assert "Reading MQTT environment variables" in caplog.text
        assert "Reading Influx environment variables" in caplog.text
        assert joined_secret_store == full_env_copy

    def test_passes_secret_store_reads_mqtt_env(
        self, mocker: MockerFixture, caplog: LogCaptureFixture
    ):
        caplog.set_level(logging.INFO)
        mqtt_env_copy = TEST_MQTT_ENV.copy()
        mqtt_env_copy["MQTT_PORT"] = int(TEST_MQTT_ENV["MQTT_PORT"])
        mqtt_env_copy = {key.lower(): value for key, value in mqtt_env_copy.items()}
        mocker.patch.dict(os.environ, TEST_MQTT_ENV)

        secret_store = SecretStore(has_mqtt_access=True)

        assert "Reading MQTT environment variables" in caplog.text
        assert "Reading Influx environment variables" not in caplog.text
        assert secret_store.mqtt_secrets == mqtt_env_copy

    def test_passes_secret_store_reads_influx_env(
        self, mocker: MockerFixture, caplog: LogCaptureFixture
    ):
        caplog.set_level(logging.INFO)
        influx_env_copy = TEST_INFLUX_ENV.copy()
        influx_env_copy = {key.lower(): value for key, value in influx_env_copy.items()}
        mocker.patch.dict(os.environ, TEST_INFLUX_ENV)

        secret_store = SecretStore(has_influx_access=True)

        assert "Reading MQTT environment variables" not in caplog.text
        assert "Reading Influx environment variables" in caplog.text
        assert secret_store.influx_secrets == influx_env_copy

    def test_fails_mqtt_env_contains_bad_port(
        self, mocker: MockerFixture, caplog: LogCaptureFixture
    ):
        caplog.set_level(logging.CRITICAL)
        mqtt_env_copy = TEST_MQTT_ENV.copy()
        mqtt_env_copy["MQTT_PORT"] = str(TEST_MAX_PORT_RANGE + 5)
        mocker.patch.dict(os.environ, mqtt_env_copy)

        with raises(MissingCredentialsError):
            _ = SecretStore(has_mqtt_access=True)

        assert (
            f"MQTT port outside maximum port range, 0-{TEST_MAX_PORT_RANGE}"
            in caplog.text
        )

    def test_fails_secret_store_reads_none(
        self, mocker: MockerFixture, caplog: LogCaptureFixture
    ):
        caplog.set_level(logging.INFO)
        mocker.patch.dict(os.environ, TEST_ENV_FULL)

        _ = SecretStore()

        assert "Reading MQTT environment variables" not in caplog.text
        assert "Reading Influx environment variables" not in caplog.text

    def test_fails_secret_store_reads_empty_mqtt_env(
        self, mocker: MockerFixture, caplog: LogCaptureFixture
    ):
        caplog.set_level(logging.CRITICAL)
        mocker.patch.dict(os.environ, TEST_EMPTY_ENV)

        with raises(MissingCredentialsError):
            _ = SecretStore(has_mqtt_access=True)

        assert "Ran into error when reading environment variables" in caplog.text

    def test_fails_secret_store_reads_empty_influx_env(
        self, mocker: MockerFixture, caplog: LogCaptureFixture
    ):
        caplog.set_level(logging.CRITICAL)
        mocker.patch.dict(os.environ, TEST_EMPTY_ENV)

        with raises(MissingCredentialsError):
            _ = SecretStore(has_influx_access=True)

        assert "Ran into error when reading environment variables" in caplog.text

    def test_fails_secret_store_empty_values(
        self, mocker: MockerFixture, caplog: LogCaptureFixture
    ):
        caplog.set_level(logging.CRITICAL)
        mqtt_env_copy = TEST_ENV_FULL.copy()
        mqtt_env_copy["MQTT_USER"] = ""
        mqtt_env_copy["INFLUX_URL"] = ""
        mocker.patch.dict(os.environ, mqtt_env_copy)

        with raises(MissingCredentialsError) as err:
            _ = SecretStore(has_mqtt_access=True, has_influx_access=True)

        assert "Ran into error when reading environment variables" in caplog.text
        assert str(err.value) == "Ran into error when reading environment variables"
