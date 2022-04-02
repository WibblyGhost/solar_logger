# pylint: disable=duplicate-code, missing-function-docstring, missing-module-docstring

import logging
from unittest import mock

from faker import Faker
from pymate.value import Value
from pytest import LogCaptureFixture
from paho.mqtt.client import Client, MQTTMessage
import pytest

from classes.influx_classes import InfluxConnector
from classes.mqtt_classes import MqttConnector, PyMateDecoder

FAKE = Faker()


def dict_to_str(dictionary: dict):
    result = {}
    for key, value in dictionary.items():
        result[key] = str(value)
    return result


def test_fx_decoder_succeeded():
    fx_bytearray = b"\x00\x00\x00\x04t\x00\x04\x00\x02\x01\x12\t\x00"
    fx_array = {
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

    pymate_decoder = PyMateDecoder()
    decoded_result = pymate_decoder.fx_decoder(fx_bytearray)
    str_decoded_result = dict_to_str(decoded_result)
    str_fx_array = dict_to_str(fx_array)

    assert isinstance(decoded_result["output_voltage"], Value)
    assert str_decoded_result == str_fx_array


def test_mx_decoder_succeeded():
    mx_bytearray = b"\x87\x85\x8b\x00t\x08\x02\x00 \x01\x0f\x02\xa4"
    mx_array = {
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

    pymate_decoder = PyMateDecoder()
    decoded_result = pymate_decoder.mx_decoder(mx_bytearray)
    str_decoded_result = dict_to_str(decoded_result)
    str_mx_array = dict_to_str(mx_array)

    assert isinstance(decoded_result["amp_hours"], Value)
    assert str_decoded_result == str_mx_array


def test_dx_decoder_succeeded():
    dc_bytearray = (
        b"\xff\xe8\x00l\x00\x00\x01\x11d\xff\xf9\x00\x1d\x00\x00\x00!\x00l"
        b"\x00\x18\x00T\x00\x1d\x00\x07\x00\x16\x00\x1b\x00\x0e\x00\r\x00J\x00\x1f\x00+"
        b"\x00\x0b\x00\x03\x00\t\x00\x0c\x00\x00\x00\x04\x00\x04\xff\xf7\x00\x0c\x00\x00"
        b"\xff\xfc\x00\x04\x00\x00c\x00\x00\x00\x02\x15\x00\x00\x00\x00\x00"
    )
    dc_array = {
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

    pymate_decoder = PyMateDecoder()
    decoded_result = pymate_decoder.dc_decoder(dc_bytearray)
    str_decoded_result = dict_to_str(decoded_result)
    str_dc_array = dict_to_str(dc_array)

    assert isinstance(decoded_result["bat_current"], Value)
    assert str_decoded_result == str_dc_array


@pytest.mark.parametrize(
    "topic",
    [
        b"mate/status",
        b"mate/mx-1/status",
        b"mate/fx-1/status",
        b"mate/dc-1/status",
    ],
)
def test_check_status_succeeds(topic):
    mqtt_message = MQTTMessage(topic=topic)
    mqtt_message.payload = b"online"
    pymate_decoder = PyMateDecoder()

    pymate_decoder.check_status(mqtt_message)


@pytest.mark.parametrize(
    "topic",
    [
        b"mate/status",
        b"mate/mx-1/status",
        b"mate/fx-1/status",
        b"mate/dc-1/status",
    ],
)
def test_check_status_fails(topic):
    mqtt_message = MQTTMessage(topic=topic)
    mqtt_message.payload = b"offline"
    pymate_decoder = PyMateDecoder()

    with pytest.raises(Exception) as err:
        pymate_decoder.check_status(mqtt_message)
    assert (
        str(err.value) == f"A backend MQTT service isn't online, "
        f"{topic.decode('ascii')} = offline"
    )

MQTT_ENV = {
        "mqtt_host": FAKE.url(),
        "mqtt_port": str(FAKE.pyint(4)),
        "mqtt_user": FAKE.pystr(),
        "mqtt_token": FAKE.pystr(),
        "mqtt_topic": FAKE.pystr(),
}
def test_mqtt_connect_succeeds(caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)
    influx_connector = mock.MagicMock(InfluxConnector)
    mqtt_connect = mock.MagicMock(Client.connect, return_value=mock.MagicMock())
    mqtt_loop = mock.MagicMock(Client.loop_forever, mock.MagicMock())

    with mock.patch("classes.mqtt_classes.Client.connect", mqtt_connect):
        with mock.patch("classes.mqtt_classes.Client.loop_forever", mqtt_loop):
            mqtt_connector = MqttConnector(
                mqtt_secrets=MQTT_ENV, influx_connector=influx_connector
            )
            mqtt_connector.run_mqtt_listener()

    assert "Connecting to MQTT broker" in caplog.text


def test_mqtt_connect_fails(caplog: LogCaptureFixture):
    caplog.set_level(logging.CRITICAL)
    influx_connector = mock.MagicMock(InfluxConnector)
    mqtt_connect = mock.MagicMock(Client.connect, side_effect=Exception)
    mqtt_loop = mock.MagicMock(Client.loop_forever, mock.MagicMock())

    with mock.patch("classes.mqtt_classes.Client.connect", mqtt_connect):
        with mock.patch("classes.mqtt_classes.Client.loop_forever", mqtt_loop):
            with pytest.raises(Exception):
                mqtt_connector = MqttConnector(
                    mqtt_secrets=MQTT_ENV, influx_connector=influx_connector
                )
                mqtt_connector.run_mqtt_listener()
    assert "Failed to connect to MQTT broker" in caplog.text
