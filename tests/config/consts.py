# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

from faker import Faker

FAKE = Faker()


class TestSecretStore:
    mqtt_secrets = {
        "mqtt_host": FAKE.url(),
        "mqtt_port": str(FAKE.pyint()),
        "mqtt_user": FAKE.pystr(),
        "mqtt_token": FAKE.pystr(),
        "mqtt_topic": FAKE.pystr(),
    }
    influx_secrets = {
        "influx_url": FAKE.url(),
        "influx_org": FAKE.pystr(),
        "influx_bucket": FAKE.pystr(),
        "influx_token": FAKE.pystr(),
    }


TEST_MQTT_ENV = {
    "mqtt_host": FAKE.pystr(),
    "mqtt_port": str(FAKE.pyint(6)),
    "mqtt_user": FAKE.pystr(),
    "mqtt_token": FAKE.pystr(),
    "mqtt_topic": FAKE.pystr(),
}

TEST_INFLUX_ENV = {
    "influx_url": FAKE.url(),
    "influx_org": FAKE.pystr(),
    "influx_bucket": FAKE.pystr(),
    "influx_token": FAKE.pystr(),
}

TEST_ENV_FULL = dict(TEST_MQTT_ENV, **TEST_INFLUX_ENV)
TEST_MAX_PORT_RANGE = 65535
