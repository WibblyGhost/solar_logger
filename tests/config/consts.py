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
    "MQTT_HOST": FAKE.pystr(),
    "MQTT_PORT": str(FAKE.pyint(6)),
    "MQTT_USER": FAKE.pystr(),
    "MQTT_TOKEN": FAKE.pystr(),
    "MQTT_TOPIC": FAKE.pystr(),
}

TEST_INFLUX_ENV = {
    "INFLUX_URL": FAKE.url(),
    "INFLUX_ORG": FAKE.pystr(),
    "INFLUX_BUCKET": FAKE.pystr(),
    "INFLUX_TOKEN": FAKE.pystr(),
}

TEST_EMPTY_ENV = {
    "MQTT_HOST": "",
    "MQTT_PORT": str(FAKE.pyint(6)),
    "MQTT_USER": "",
    "MQTT_TOKEN": "",
    "MQTT_TOPIC": "",
    "INFLUX_URL": "",
    "INFLUX_ORG": "",
    "INFLUX_BUCKET": "",
    "INFLUX_TOKEN": "",
}

TEST_ENV_FULL = dict(TEST_MQTT_ENV, **TEST_INFLUX_ENV)
TEST_MAX_PORT_RANGE = 65535
