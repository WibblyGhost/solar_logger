# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

from dataclasses import dataclass

from faker import Faker

FAKE = Faker()

APP_CONFIG = "src/config/config.ini"
TEST_CONFIG = "tests/config/config.ini"


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


@dataclass
class FX:
    bytearray = b"\x00\x00\x00\x04t\x00\x04\x00\x02\x01\x12\t\x00"
    array = {
        "ac_mode": 2,
        "aux_on": False,
        "battery_voltage": "27.4V",
        "buy_current": "0.0A",
        "chg_current": "0.0A",
        "error_mode": 0,
        "input_voltage": "8V",
        "inverter_current": "0.0A",
        "is_230v": True,
        "misc": 9,
        "operational_mode": 4,
        "output_voltage": "232V",
        "sell_current": "0.0A",
        "warnings": 0,
    }


@dataclass
class MX:
    bytearray = b"\x87\x85\x8b\x00t\x08\x02\x00 \x01\x0f\x02\xa4"
    array = {
        "amp_hours": "116Ah",
        "aux_mode": 8,
        "aux_state": False,
        "bat_current": "11.7A",
        "bat_voltage": "27.1V",
        "errors": 0,
        "kilowatt_hours": "3.2kWh",
        "pv_current": "5A",
        "pv_voltage": "67.6V",
        "status": 2,
    }


@dataclass
class DC:
    bytearray = (
        b"\xff\xe8\x00l\x00\x00\x01\x11d\xff\xf9\x00\x1d\x00\x00\x00!\x00l"
        b"\x00\x18\x00T\x00\x1d\x00\x07\x00\x16\x00\x1b\x00\x0e\x00\r\x00J\x00\x1f\x00+"
        b"\x00\x0b\x00\x03\x00\t\x00\x0c\x00\x00\x00\x04\x00\x04\xff\xf7\x00\x0c\x00\x00"
        b"\xff\xfc\x00\x04\x00\x00c\x00\x00\x00\x02\x15\x00\x00\x00\x00\x00"
    )
    array = {
        "bat_ah_today": "13Ah",
        "bat_current": "8.4A",
        "bat_kwh_today": "0.43kWh",
        "bat_net_ah": "0Ah",
        "bat_net_kwh": "0.02kWh",
        "bat_power": "0.22kW",
        "bat_voltage": "27.3V",
        "days_since_full": "1.1days",
        "flags": 33,
        "in_ah_today": "27Ah",
        "in_current": "10.8A",
        "in_kwh_today": "0.74kWh",
        "in_power": "0.29kW",
        "min_soc_today": "99%",
        "out_ah_today": "14Ah",
        "out_current": "2.4A",
        "out_kwh_today": "0.31kWh",
        "out_power": "0.07kW",
        "shunta_ah_today": "-4Ah",
        "shunta_current": "-2.4A",
        "shunta_kwh_today": "-0.09kWh",
        "shunta_power": "-0.07kW",
        "shuntb_ah_today": "4Ah",
        "shuntb_current": "10.8A",
        "shuntb_kwh_today": "0.12kWh",
        "shuntb_power": "0.29kW",
        "shuntc_ah_today": "0Ah",
        "shuntc_current": "0.0A",
        "shuntc_kwh_today": "0.00kWh",
        "shuntc_power": "0.00kW",
        "state_of_charge": "100%",
    }
