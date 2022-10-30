# pylint: disable=missing-function-docstring, missing-module-docstring, protected-access, redefined-outer-name
import logging
from logging import Logger, StreamHandler

import pytest
from pytest import LogCaptureFixture, fixture, mark, raises
from pytest_mock import MockerFixture

from src.classes.custom_exceptions import MissingConfigurationError
from src.helpers.consts import SOLAR_DEBUG_CONFIG_TITLE
from src.helpers.py_logger import LoggingTools
from tests.config.consts import FAKE, TEST_CONFIG


class FakeLogger:
    """Storage class for fixture"""

    def __init__(self, logger):
        self.fake_logger = logger
        self.file_path = TEST_CONFIG
        self.log_tools = LoggingTools(
            config_name=SOLAR_DEBUG_CONFIG_TITLE,
            config_dir=TEST_CONFIG,
            logger=self.fake_logger,
        )
        self.log_tools._debug_level = logging.DEBUG
        self.log_tools._file_format = (
            "%%(asctime)s, %%(name)s, %%(threadName)s, %%(levelname)s, %%(message)s"
        )
        self.log_tools._date_format = "%%d/%%m/%%Y, %%H:%%M:%%S"
        self.log_tools._max_file_bytes = FAKE.pyint()
        self.log_tools._max_file_no = FAKE.pyint()
        self.log_tools._mode = "w"
        self.log_tools._file_path = self.file_path


@fixture
def log_fixture():
    fake_logger = logging.getLogger("Test Logger")
    yield fake_logger
    fake_logger.handlers.clear()


@fixture
def log_tools_fixture(log_fixture: Logger):
    yield FakeLogger(log_fixture)


class TestLoggingTools:
    """Test class for LoggingTools"""

    def test_pass_read_configs(self, log_tools_fixture: FakeLogger):
        log_tools = log_tools_fixture.log_tools
        log_tools.read_configs()

    def test_read_basic_configs(
        self, mocker: MockerFixture, log_tools_fixture: FakeLogger
    ):
        log_tools = log_tools_fixture.log_tools
        basic_config = mocker.Mock()
        log_tools._read_basic_config = basic_config
        log_tools.read_configs()
        basic_config.assert_called()

    def test_read_extra_configs_with_flag(
        self, mocker: MockerFixture, log_tools_fixture: FakeLogger
    ):
        log_tools = log_tools_fixture.log_tools
        extra_config = mocker.Mock()
        log_tools._read_extra_configs = extra_config
        log_tools.read_configs()
        extra_config.assert_called()

    @mark.parametrize(
        "side_effect",
        [
            # Level, Format, DateFormat, FileLogging
            [None, "b", "c", "false"],
            ["DEBUG", None, "c", "false"],
            ["DEBUG", "b", None, "false"],
            ["DEBUG", "b", None, None],
        ],
    )
    def test_read_basic_configs_raise_custom_exception_on_bad_data(
        self,
        side_effect: list,
        mocker: MockerFixture,
        log_tools_fixture: FakeLogger,
        caplog: LogCaptureFixture,
    ):
        mocker.patch("src.helpers.py_logger.ConfigParser.get", side_effect=side_effect)
        log_tools = log_tools_fixture.log_tools
        log_tools._config_name = SOLAR_DEBUG_CONFIG_TITLE

        with raises(MissingConfigurationError):
            log_tools._config_parser.read(TEST_CONFIG)
            log_tools._read_basic_config()

        assert "Failed to read basic logger configs" in caplog.messages

    @mark.parametrize(
        "side_effect",
        [
            # LogRotation, FileLocation, FileName, MaxBytes, MaxFiles, Mode
            [None, "b", "c", "5", "5", "w"],
            ["a", None, "c", "5", "5", "w"],
            ["a", "b", None, "5", "5", "w"],
            ["a", "b", "c", None, "5", "w"],
            ["a", "b", "c", "5", None, "w"],
            ["a", "b", "c", "5", "5", None],
        ],
    )
    def test_read_extra_configs_raise_custom_exception_on_bad_data(
        self,
        side_effect: list,
        mocker: MockerFixture,
        log_tools_fixture: FakeLogger,
        caplog: LogCaptureFixture,
    ):
        mocker.patch("src.helpers.py_logger.ConfigParser.get", side_effect=side_effect)
        log_tools = log_tools_fixture.log_tools
        log_tools._config_name = SOLAR_DEBUG_CONFIG_TITLE
        log_tools._config_parser.read(TEST_CONFIG)

        with pytest.raises(MissingConfigurationError):
            log_tools._read_extra_configs()

        assert "Failed to read file logger settings in configs" in caplog.messages

    def test_create_stdout_logger(
        self, log_tools_fixture: FakeLogger, caplog: LogCaptureFixture
    ):
        caplog.set_level(logging.INFO)
        log_tools = log_tools_fixture.log_tools
        fake_logger: Logger = log_tools_fixture.fake_logger

        log_tools.create_loggers()

        assert isinstance(fake_logger.handlers[0], StreamHandler)
        assert "Created stdout logger" in caplog.messages

    def test_create_rotating_file_logger_size(
        self,
        mocker: MockerFixture,
        log_tools_fixture: FakeLogger,
        caplog: LogCaptureFixture,
    ):
        caplog.set_level(logging.INFO)
        mocker.patch("src.helpers.py_logger.os.path.exists", return_value=True)
        mock_handler = mocker.patch("src.helpers.py_logger.RotatingFileHandler")
        log_tools: LoggingTools = log_tools_fixture.log_tools
        fake_logger: Logger = log_tools_fixture.fake_logger
        file_path: str = log_tools_fixture.file_path
        log_tools._is_file_logging = True
        log_tools._log_rotation = "size_based"

        log_tools.create_loggers()

        assert fake_logger.handlers[1] == mock_handler()
        assert f"Created rotating file log file at {file_path}" in caplog.messages

    def test_create_rotating_file_logger_timed(
        self,
        mocker: MockerFixture,
        log_tools_fixture: FakeLogger,
        caplog: LogCaptureFixture,
    ):
        caplog.set_level(logging.INFO)
        mocker.patch("src.helpers.py_logger.os.path.exists", return_value=True)
        mock_handler = mocker.patch("src.helpers.py_logger.TimedRotatingFileHandler")
        log_tools: LoggingTools = log_tools_fixture.log_tools
        fake_logger: Logger = log_tools_fixture.fake_logger
        file_path: str = log_tools_fixture.file_path
        log_tools._is_file_logging = True
        log_tools._log_rotation = "time_based"

        log_tools.create_loggers()

        assert fake_logger.handlers[1] == mock_handler()
        assert f"Created time rotating file log file at {file_path}" in caplog.messages
