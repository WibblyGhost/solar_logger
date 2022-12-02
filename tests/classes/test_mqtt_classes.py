# pylint: disable=missing-function-docstring, missing-module-docstring, redefined-outer-name, protected-access, duplicate-code
import logging
from datetime import datetime

from paho.mqtt.client import Client, MQTTMessage
from pymate.value import Value
from pytest import LogCaptureFixture, fixture, mark, raises
from pytest_mock import MockerFixture

from src.classes.common_classes import QueuePackage
from src.classes.mqtt_classes import MqttConnector, MqttTopics, PyMateDecoder
from src.helpers.consts import THREADED_QUEUE
from tests.config.consts import (
    FAKE,
    TEST_MAX_QUEUE_LENGTH,
    TestDC,
    TestFX,
    TestMqttTopics,
    TestMX,
    TestSecretStore,
)


class TestError(Exception):
    """Custom exception for use in tests"""


def dict_to_str(dictionary: dict):
    result = {}
    for key, value in dictionary.items():
        result[key] = str(value)
    return result


@fixture
def mqtt_fixture():
    mqtt_connector = MqttConnector(secret_store=TestSecretStore)
    return mqtt_connector


def create_mqtt_message(mocker: MockerFixture, topic: str, payload: str) -> MQTTMessage:
    mqtt_message = mocker.MagicMock(MQTTMessage)
    mqtt_message.topic = topic
    mqtt_message.payload = bytes(payload, "ascii")
    return mqtt_message


def setup_service_status(mqtt_fixture: MqttConnector, status: str) -> None:
    status_values = [
        TestMqttTopics.mate_status,
        TestMqttTopics.dc_status,
        TestMqttTopics.fx_status,
        TestMqttTopics.mx_status,
    ]
    for value in status_values:
        mqtt_fixture._status[value] = status


class TestPyMateDecoder:
    """Test class for PyMate Decoder"""

    def test_passes_detach_time(self):
        pymate_decoder = PyMateDecoder()
        result = pymate_decoder.detach_time(msg=TestFX.bytearray, padding_at_end=2)

        assert result == (67108864, b"t\x00\x04\x00\x02\x01\x12")

    def test_passes_dc_decoder(self):
        pymate_decoder = PyMateDecoder()
        decoded_result = pymate_decoder.dc_decoder(TestDC.bytearray)
        str_decoded_result = dict_to_str(decoded_result)
        str_dc_array = dict_to_str(TestDC.array)

        assert isinstance(decoded_result["bat_current"], Value)
        assert str_decoded_result == str_dc_array

    def test_passes_fx_decoder(self):
        pymate_decoder = PyMateDecoder()
        decoded_result = pymate_decoder.fx_decoder(TestFX.bytearray)
        str_decoded_result = dict_to_str(decoded_result)
        str_fx_array = dict_to_str(TestFX.array)

        assert isinstance(decoded_result["output_voltage"], Value)
        assert str_decoded_result == str_fx_array

    def test_passes_mx_decoder(self):
        pymate_decoder = PyMateDecoder()
        decoded_result = pymate_decoder.mx_decoder(TestMX.bytearray)
        str_decoded_result = dict_to_str(decoded_result)
        str_mx_array = dict_to_str(TestMX.array)

        assert isinstance(decoded_result["amp_hours"], Value)
        assert str_decoded_result == str_mx_array


def test_mqtt_topics_consistent():
    def get_custom_attributes(cls):
        return {func: getattr(cls, func) for func in dir(cls) if func[0] != "_"}

    defined_vars = get_custom_attributes(MqttTopics)
    test_dict = get_custom_attributes(TestMqttTopics)
    assert defined_vars == test_dict


class TestMqttConnector:
    """Test class for MQTT Connector"""

    def test_logs_on_socket_open(
        self, mqtt_fixture: MqttConnector, caplog: LogCaptureFixture
    ):
        caplog.set_level(logging.DEBUG)
        userdata = FAKE.pystr()
        sock = FAKE.pystr()

        mqtt_fixture._on_socket_open(_client=FAKE.pystr(), userdata=userdata, sock=sock)

        assert f"Socket open debug args, {userdata}, {sock}" in caplog.text

    def test_logs_on_socket_close(
        self, mqtt_fixture: MqttConnector, caplog: LogCaptureFixture
    ):
        caplog.set_level(logging.DEBUG)
        userdata = FAKE.pystr()
        sock = FAKE.pystr()

        mqtt_fixture._on_socket_close(
            _client=FAKE.pystr(), userdata=userdata, sock=sock
        )

        assert f"Socket close debug args, {userdata}, {sock}" in caplog.text

    def test_logs_on_subscribe(
        self, mqtt_fixture: MqttConnector, caplog: LogCaptureFixture
    ):
        caplog.set_level(logging.DEBUG)
        granted_qos = FAKE.pyint()
        mid = FAKE.pystr()
        userdata = FAKE.pystr()

        mqtt_fixture._on_subscribe(
            _client=FAKE.pystr(), userdata=userdata, mid=mid, granted_qos=granted_qos
        )

        assert "Subscribed to MQTT topic" in caplog.text
        assert f"MQTT topic returns QoS level of {granted_qos}" in caplog.text
        assert f"Subscribe debug args, {userdata}, {mid}, {granted_qos}" in caplog.text

    def test_logs_on_unsubscribe(
        self, mqtt_fixture: MqttConnector, caplog: LogCaptureFixture
    ):
        caplog.set_level(logging.DEBUG)
        mid = FAKE.pystr()
        userdata = FAKE.pystr()

        mqtt_fixture._on_unsubscribe(_client=FAKE.pystr(), userdata=userdata, mid=mid)

        assert "Unsubscribed from MQTT topic" in caplog.text
        assert f"Unsubscribe debug args, {userdata}, {mid}" in caplog.text

    def test_on_connect_calls_subscribe(
        self,
        mocker: MockerFixture,
        mqtt_fixture: MqttConnector,
        caplog: LogCaptureFixture,
    ):
        caplog.set_level(logging.INFO)
        subscribe = mocker.patch("src.classes.mqtt_classes.Client.subscribe")
        userdata = FAKE.pystr()
        flags = FAKE.pystr()
        return_code = 0

        mqtt_fixture._on_connect(
            _client=FAKE.pystr(),
            userdata=userdata,
            flags=flags,
            return_code=return_code,
        )

        subscribe.assert_called_once_with(
            topic=f"{TestSecretStore.mqtt_secrets['mqtt_topic']}"
        )
        assert "Connecting to MQTT broker" in caplog.text

    @mark.parametrize("return_code", [1, 2, 3, 4, 5])
    def test_on_connect_fails_with_bad_return_code(
        self,
        mqtt_fixture: MqttConnector,
        return_code: int,
        caplog: LogCaptureFixture,
    ):
        caplog.set_level(logging.DEBUG)
        userdata = FAKE.pystr()
        flags = FAKE.pystr()
        return_codes = {
            0: "Connection successful",
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorized",
        }

        mqtt_fixture._on_connect(
            _client=FAKE.pystr(),
            userdata=userdata,
            flags=flags,
            return_code=return_code,
        )

        assert (
            f"Couldn't connect to MQTT broker returned code: {return_code}\n"
            f"{return_codes[return_code]}"
        ) in caplog.text
        assert f"Connect debug args, {userdata}, {flags}, {return_code}" in caplog.text

    def test_logs_on_disconnect(
        self, mqtt_fixture: MqttConnector, caplog: LogCaptureFixture
    ):
        caplog.set_level(logging.DEBUG)
        userdata = FAKE.pystr()
        return_code = FAKE.pyint()

        mqtt_fixture._on_disconnect(
            _client=FAKE.pystr(), userdata=userdata, return_code=return_code
        )

        assert "Disconnected from MQTT broker" in caplog.text
        assert f"Disconnect debug args, {userdata}, {return_code}" in caplog.text

    @mark.parametrize(
        "status",
        [
            "online",
            "offline",
        ],
    )
    @mark.parametrize(
        "topic",
        [
            TestMqttTopics.mate_status,
            TestMqttTopics.dc_status,
            TestMqttTopics.fx_status,
            TestMqttTopics.mx_status,
        ],
    )
    def test_check_status_goes_offline(
        self,
        mocker: MockerFixture,
        mqtt_fixture: MqttConnector,
        topic: str,
        status: str,
        caplog: LogCaptureFixture,
    ):
        caplog.set_level(logging.INFO)
        # Force everything online and test the change to offline
        if status == "online":
            setup_service_status(mqtt_fixture=mqtt_fixture, status="offline")
        else:
            setup_service_status(mqtt_fixture=mqtt_fixture, status="online")
        mqtt_message = create_mqtt_message(mocker=mocker, topic=topic, payload=status)

        mqtt_fixture._check_status(msg=mqtt_message)

        if status == "online":
            assert f"{topic} is now {status}" in caplog.text
            assert f"{topic} has gone {status}" not in caplog.text
        else:
            assert f"{topic} is now {status}" not in caplog.text
            assert f"{topic} has gone {status}" in caplog.text
        assert mqtt_fixture._status[topic] == status

    def test_passes_load_queue(
        self, mqtt_fixture: MqttConnector, caplog: LogCaptureFixture
    ):
        caplog.set_level(logging.INFO)
        measurement = FAKE.pystr()
        time_field = FAKE.date()
        payload_key = FAKE.pystr()
        payload_value = FAKE.pyfloat()

        mqtt_fixture.load_queue(
            measurement=measurement,
            time_field=time_field,
            payload={
                payload_key: str(payload_value),
            },
        )

        assert QueuePackage(
            measurement=measurement,
            time_field=time_field,
            field={payload_key: float(payload_value)},
        ) == THREADED_QUEUE.get(timeout=5)
        assert "Pushed items onto queue, queue now has 1 items" in caplog.text

    def test_waits_on_max_queue(
        self,
        mocker: MockerFixture,
        mqtt_fixture: MqttConnector,
        caplog: LogCaptureFixture,
    ):
        caplog.set_level(logging.INFO)
        measurement = FAKE.pystr()
        time_field = FAKE.date()
        payload_key = FAKE.pystr()
        payload_value = FAKE.pyfloat()

        test_queue = []
        mocker.patch("src.classes.mqtt_classes.time.sleep", side_effect=TestError)
        with raises(TestError):
            for _ in range(0, TEST_MAX_QUEUE_LENGTH + 1):
                mqtt_fixture.load_queue(
                    measurement=measurement,
                    time_field=time_field,
                    payload={
                        payload_key: str(payload_value),
                    },
                )
                test_queue.append(
                    QueuePackage(
                        measurement=measurement,
                        time_field=time_field,
                        field={payload_key: float(payload_value)},
                    )
                )

        result_queue = []
        while not THREADED_QUEUE.empty():
            result_queue.append(THREADED_QUEUE.get(timeout=1))
        zipped_queues = zip(test_queue, result_queue)

        for test_item, result_item in zipped_queues:
            assert test_item == result_item
        assert (
            f"Pushed items onto queue, queue now has {TEST_MAX_QUEUE_LENGTH - 1} items"
            in caplog.text
        )

    @mark.parametrize(
        "message_type",
        [TestMqttTopics.dc_data, TestMqttTopics.fx_data, TestMqttTopics.mx_data],
    )
    def test_no_messsage_decoding_when_offline(
        self,
        mocker: MockerFixture,
        mqtt_fixture: MqttConnector,
        message_type: str,
    ):
        payload = FAKE.pystr()
        detach_time = mocker.patch("src.classes.mqtt_classes.PyMateDecoder.detach_time")
        detach_time.side_effect = AssertionError
        setup_service_status(mqtt_fixture=mqtt_fixture, status="offline")
        mqtt_message = create_mqtt_message(
            mocker=mocker, topic=message_type, payload=payload
        )

        mqtt_fixture._decode_message(msg=mqtt_message)

        detach_time.assert_not_called()

    def test_passes_decode_message_dc(
        self,
        mocker: MockerFixture,
        mqtt_fixture: MqttConnector,
        caplog: LogCaptureFixture,
    ):
        caplog.set_level(logging.DEBUG)
        msg_time = FAKE.unix_time()
        msg_timestamp = datetime.fromtimestamp(msg_time)
        payload = FAKE.pystr()
        detach_time = mocker.patch("src.classes.mqtt_classes.PyMateDecoder.detach_time")
        load_queue = mocker.patch("src.classes.mqtt_classes.MqttConnector._load_queue")
        detach_time.return_value = (msg_time, FAKE.pystr())
        dc_decoder = mocker.patch("src.classes.mqtt_classes.PyMateDecoder.dc_decoder")
        dc_decoder.return_value = payload
        setup_service_status(mqtt_fixture=mqtt_fixture, status="online")
        mqtt_message = create_mqtt_message(
            mocker=mocker, topic=TestMqttTopics.dc_data, payload=payload
        )

        mqtt_fixture._decode_message(msg=mqtt_message)

        detach_time.assert_called_once()
        dc_decoder.assert_called_once()
        assert f"Received {TestMqttTopics.dc_name} data packet" in caplog.text
        assert f"{TestMqttTopics.dc_name} payload: {payload}" in caplog.text
        assert (
            f"Decoded and split {TestMqttTopics.dc_name} payload: {payload} at {msg_timestamp}"
            in caplog.text
        )
        load_queue.assert_called_with(
            measurement=TestMqttTopics.dc_name,
            time_field=msg_timestamp,
            payload=payload,
        )

    def test_passes_decode_message_fx(
        self,
        mocker: MockerFixture,
        mqtt_fixture: MqttConnector,
        caplog: LogCaptureFixture,
    ):
        caplog.set_level(logging.DEBUG)

        msg_time = FAKE.unix_time()
        msg_timestamp = datetime.fromtimestamp(msg_time)
        payload = FAKE.pystr()
        detach_time = mocker.patch("src.classes.mqtt_classes.PyMateDecoder.detach_time")
        load_queue = mocker.patch("src.classes.mqtt_classes.MqttConnector._load_queue")
        detach_time.return_value = (msg_time, FAKE.pystr())
        fx_decoder = mocker.patch("src.classes.mqtt_classes.PyMateDecoder.fx_decoder")
        fx_decoder.return_value = payload
        setup_service_status(mqtt_fixture=mqtt_fixture, status="online")
        mqtt_message = create_mqtt_message(
            mocker=mocker, topic=TestMqttTopics.fx_data, payload=payload
        )

        mqtt_fixture._decode_message(msg=mqtt_message)

        detach_time.assert_called_once()
        fx_decoder.assert_called_once()
        assert f"Received {TestMqttTopics.fx_name} data packet" in caplog.text
        assert f"{TestMqttTopics.fx_name} payload: {payload}" in caplog.text
        assert (
            f"Decoded and split {TestMqttTopics.fx_name} payload: {payload} at {msg_timestamp}"
            in caplog.text
        )
        load_queue.assert_called_with(
            measurement=TestMqttTopics.fx_name,
            time_field=msg_timestamp,
            payload=payload,
        )

    def test_passes_decode_message_mx(
        self,
        mocker: MockerFixture,
        mqtt_fixture: MqttConnector,
        caplog: LogCaptureFixture,
    ):
        caplog.set_level(logging.DEBUG)

        msg_time = FAKE.unix_time()
        msg_timestamp = datetime.fromtimestamp(msg_time)
        payload = FAKE.pystr()
        detach_time = mocker.patch("src.classes.mqtt_classes.PyMateDecoder.detach_time")
        load_queue = mocker.patch("src.classes.mqtt_classes.MqttConnector._load_queue")
        detach_time.return_value = (msg_time, FAKE.pystr())
        mx_decoder = mocker.patch("src.classes.mqtt_classes.PyMateDecoder.mx_decoder")
        mx_decoder.return_value = payload
        setup_service_status(mqtt_fixture=mqtt_fixture, status="online")
        mqtt_message = create_mqtt_message(
            mocker=mocker, topic=TestMqttTopics.mx_data, payload=payload
        )

        mqtt_fixture._decode_message(msg=mqtt_message)

        detach_time.assert_called_once()
        mx_decoder.assert_called_once()
        assert f"Received {TestMqttTopics.mx_name} data packet" in caplog.text
        assert f"{TestMqttTopics.mx_name} payload: {payload}" in caplog.text
        assert (
            f"Decoded and split {TestMqttTopics.mx_name} payload: {payload} at {msg_timestamp}"
            in caplog.text
        )
        load_queue.assert_called_with(
            measurement=TestMqttTopics.mx_name,
            time_field=msg_timestamp,
            payload=payload,
        )

    def test_on_message_calls_decode(
        self,
        mocker: MockerFixture,
        mqtt_fixture: MqttConnector,
        caplog: LogCaptureFixture,
    ):
        caplog.set_level(logging.INFO)
        check_status = mocker.patch(
            "src.classes.mqtt_classes.MqttConnector._check_status"
        )
        decode_messages = mocker.patch(
            "src.classes.mqtt_classes.MqttConnector._decode_message"
        )
        setup_service_status(mqtt_fixture=mqtt_fixture, status="online")
        mqtt_message = create_mqtt_message(
            mocker=mocker, topic=TestMqttTopics.dc_name, payload=FAKE.pystr()
        )

        mqtt_fixture._on_message(
            _client=FAKE.pystr(), _userdata=FAKE.pystr(), msg=mqtt_message
        )

        check_status.assert_called_once_with(msg=mqtt_message)
        decode_messages.assert_called_once_with(msg=mqtt_message)
        assert caplog.text == ""

    def test_on_message_warns_when_offline(
        self,
        mocker: MockerFixture,
        mqtt_fixture: MqttConnector,
        caplog: LogCaptureFixture,
    ):
        caplog.set_level(logging.INFO)
        check_status = mocker.patch(
            "src.classes.mqtt_classes.MqttConnector._check_status"
        )
        decode_messages = mocker.patch(
            "src.classes.mqtt_classes.MqttConnector._decode_message"
        )
        error_message = "Testing error"
        decode_messages.side_effect = AssertionError(error_message)
        setup_service_status(mqtt_fixture=mqtt_fixture, status="offline")
        mqtt_message = create_mqtt_message(
            mocker=mocker, topic=TestMqttTopics.dc_name, payload=FAKE.pystr()
        )

        mqtt_fixture._on_message(
            _client=FAKE.pystr(), _userdata=FAKE.pystr(), msg=mqtt_message
        )

        check_status.assert_called_once_with(msg=mqtt_message)
        decode_messages.assert_not_called()
        assert f"{TestMqttTopics.mate_status} is offline" in caplog.text

    def test_on_message_skips_exceptions(
        self,
        mocker: MockerFixture,
        mqtt_fixture: MqttConnector,
        caplog: LogCaptureFixture,
    ):
        caplog.set_level(logging.INFO)
        check_status = mocker.patch(
            "src.classes.mqtt_classes.MqttConnector._check_status"
        )
        decode_messages = mocker.patch(
            "src.classes.mqtt_classes.MqttConnector._decode_message"
        )
        error_message = "Testing error"
        decode_messages.side_effect = AssertionError(error_message)
        setup_service_status(mqtt_fixture=mqtt_fixture, status="online")
        mqtt_message = create_mqtt_message(
            mocker=mocker, topic=TestMqttTopics.dc_name, payload=FAKE.pystr()
        )

        mqtt_fixture._on_message(
            _client=FAKE.pystr(), _userdata=FAKE.pystr(), msg=mqtt_message
        )

        check_status.assert_called_once_with(msg=mqtt_message)
        decode_messages.assert_called_once_with(msg=mqtt_message)
        assert "MQTT on_message raised an exception:" in caplog.text
        assert error_message in caplog.text

    def test_passes_get_mqtt_client(self, mocker: MockerFixture):
        mqtt_connector = MqttConnector(TestSecretStore)
        mocker.patch("src.classes.mqtt_classes.Client.connect")

        result = mqtt_connector.get_mqtt_client()

        assert isinstance(result, Client)
