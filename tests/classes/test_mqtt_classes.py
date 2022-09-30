# pylint: disable=missing-function-docstring, missing-module-docstring, no-self-use
from unittest import mock

from paho.mqtt.client import Client
from pymate.value import Value
from pytest import LogCaptureFixture, mark
from tests.config.consts import DC, FX, MX, TestSecretStore

from src.classes.mqtt_classes import MqttConnector, PyMateDecoder


def dict_to_str(dictionary: dict):
    result = {}
    for key, value in dictionary.items():
        result[key] = str(value)
    return result


class TestPyMateDecoder:
    """Test class for PyMate Decoder"""

    def test_passes_detach_time(self):
        pymate_decoder = PyMateDecoder()
        result = pymate_decoder.detach_time(msg=FX.bytearray, padding_at_end=2)

        assert result == (67108864, b"t\x00\x04\x00\x02\x01\x12")

    def test_passes_dc_decoder(self):
        pymate_decoder = PyMateDecoder()
        decoded_result = pymate_decoder.dc_decoder(DC.bytearray)
        str_decoded_result = dict_to_str(decoded_result)
        str_dc_array = dict_to_str(DC.array)

        assert isinstance(decoded_result["bat_current"], Value)
        assert str_decoded_result == str_dc_array

    def test_passes_fx_decoder(self):
        pymate_decoder = PyMateDecoder()
        decoded_result = pymate_decoder.fx_decoder(FX.bytearray)
        str_decoded_result = dict_to_str(decoded_result)
        str_fx_array = dict_to_str(FX.array)

        assert isinstance(decoded_result["output_voltage"], Value)
        assert str_decoded_result == str_fx_array

    def test_passes_mx_decoder(self):
        pymate_decoder = PyMateDecoder()
        decoded_result = pymate_decoder.mx_decoder(MX.bytearray)
        str_decoded_result = dict_to_str(decoded_result)
        str_mx_array = dict_to_str(MX.array)

        assert isinstance(decoded_result["amp_hours"], Value)
        assert str_decoded_result == str_mx_array


class TestMqttConnector:
    """Test class for MQTT Connector"""

    @mark.skip(reason="test_passes_on_subscribe needs to be implemented")
    def test_passes_on_subscribe(self, caplog: LogCaptureFixture):
        raise NotImplementedError

    @mark.skip(reason="test_passes_on_unsubscribe needs to be implemented")
    def test_passes_on_unsubscribe(self, caplog: LogCaptureFixture):
        raise NotImplementedError

    @mark.skip(reason="test_passes_on_connect needs to be implemented")
    def test_passes_on_connect(self, caplog: LogCaptureFixture):
        raise NotImplementedError

    @mark.skip(reason="test_passes_on_disconnect needs to be implemented")
    def test_passes_on_disconnect(self, caplog: LogCaptureFixture):
        raise NotImplementedError

    @mark.skip(reason="test_passes_check_status needs to be implemented")
    def test_passes_check_status(self):
        raise NotImplementedError

    @mark.skip(reason="test_passes_load_queue needs to be implemented")
    def test_passes_load_queue(self):
        raise NotImplementedError

    @mark.skip(reason="test_passes_decode_message needs to be implemented")
    # NOTE: This is a rather big suite of tests
    def test_passes_decode_message(self):
        raise NotImplementedError

    @mark.skip(reason="test_passes_on_message needs to be implemented")
    def test_passes_on_message(self):
        raise NotImplementedError

    def test_passes_get_mqtt_client(self):
        mqtt_connector = MqttConnector(TestSecretStore)

        with mock.patch("src.classes.mqtt_classes.Client.connect"):
            result = mqtt_connector.get_mqtt_client()

        assert isinstance(result, Client)
