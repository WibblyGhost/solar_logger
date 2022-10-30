# pylint: disable=missing-function-docstring, missing-module-docstring, redefined-outer-name
import logging
from configparser import ConfigParser

from pytest import LogCaptureFixture, fixture, raises
from pytest_mock import MockerFixture

from src.helpers.py_functions import read_query_settings, write_results_to_csv
from tests.config.consts import APP_CONFIG, FAKE, TEST_CONFIG


@fixture
def config_parser_fixture(mocker: MockerFixture):
    file_path = FAKE.pystr()
    config_parser = mocker.patch(
        "src.helpers.py_functions.ConfigParser", return_value=file_path
    )
    new_parser = mocker.MagicMock(ConfigParser)
    config_parser.return_value = new_parser
    new_parser.get.return_value = file_path
    file_exists = mocker.patch("src.helpers.py_functions.os.path.exists")
    open_file = mocker.patch("src.helpers.py_functions.open", mocker.mock_open())
    makedirs = mocker.patch("src.helpers.py_functions.os.makedirs")
    makedirs.side_effect = mocker.MagicMock()
    mocker.patch("configparser.ConfigParser.read", return_value=FAKE.pystr())
    return (file_path, file_exists, open_file, makedirs)


def test_writes_to_csv(config_parser_fixture, caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)
    (file_path, file_exists, open_file, _makedirs) = config_parser_fixture

    write_results_to_csv(FAKE.pystr(), FAKE.pydict())

    file_exists.assert_called_once_with(file_path)
    open_file.assert_called_once()
    assert "Wrote rows into CSV file at:" in caplog.text
    assert "Failed to write CSV" not in caplog.text


def test_makes_dir_when_not_existent(config_parser_fixture, caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)
    (file_path, file_exists, open_file, makedirs) = config_parser_fixture
    file_exists.return_value = False

    write_results_to_csv(FAKE.pystr(), FAKE.pydict())

    file_exists.assert_called_once_with(file_path)
    makedirs.assert_called_once_with(file_path)
    open_file.assert_called_once()

    assert f"Wrote rows into CSV file at: {file_path}" in caplog.text
    assert "Failed to write CSV" not in caplog.text


def test_fails_write_to_csv(config_parser_fixture, caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)
    (_file_path, _file_exists, open_file, _makedirs) = config_parser_fixture
    open_file.side_effect = FileNotFoundError

    with raises(FileNotFoundError):
        write_results_to_csv(FAKE.pystr(), FAKE.pydict())

    assert "Failed to write CSV" in caplog.text


def test_read_query_settings(mocker: MockerFixture):
    mocker.patch("configparser.ConfigParser.read", return_value=FAKE.pystr())
    mocker.patch("configparser.ConfigParser.get", return_value=FAKE.pystr())

    result = read_query_settings("query_settings")

    assert result is not None


def test_config_files_are_consistent():
    app_config = None
    test_config = None

    with open(APP_CONFIG) as app_fh:
        app_config = app_fh.read()
    with open(TEST_CONFIG) as test_fh:
        test_config = test_fh.read()

    assert (
        app_config == test_config
    ), "Configurations files are different between environments"
