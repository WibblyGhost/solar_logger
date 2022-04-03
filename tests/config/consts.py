# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

from faker import Faker

FAKE = Faker()


class MockedSecretStore:
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
