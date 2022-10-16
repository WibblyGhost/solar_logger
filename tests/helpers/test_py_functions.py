# pylint: disable=missing-function-docstring, missing-module-docstring
import logging
from unittest import mock

from pytest import LogCaptureFixture, mark, raises

from src.helpers.py_functions import read_query_settings, write_results_to_csv
from tests.config.consts import FAKE


@mock.patch("src.helpers.py_functions.os.path.exists", return_value=True)
@mock.patch("src.helpers.py_functions.open", mock.mock_open())
def test_passes_write_to_csv(_mock_exists, caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)
    with mock.patch(
        "configparser.ConfigParser.read", return_value=FAKE.pystr()
    ) and mock.patch("configparser.ConfigParser.get", return_value=FAKE.pystr()):
        write_results_to_csv(FAKE.pystr(), FAKE.pydict())

    assert "Wrote rows into CSV file at:" in caplog.text


@mark.xfail(
    reason="test_passes_makes_dir_when_not_existent currently isn't implemented"
)
@mock.patch("src.helpers.py_functions.os.makedirs")
@mock.patch("src.helpers.py_functions.open", mock.mock_open())
def test_passes_makes_dir_when_not_existent(mock_makedirs, caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)
    mock_makedirs.side_effect = mock.MagicMock()
    file_path = FAKE.pystr()

    with mock.patch(
        "configparser.ConfigParser.read", return_value=FAKE.pystr()
    ) and mock.patch("configparser.ConfigParser.get", return_value=file_path):
        mock.patch("src.helpers.py_functions.os.path.exists", return_value=True)
        write_results_to_csv(FAKE.pystr(), FAKE.pydict())

    assert mock_makedirs.assert_called_once()


@mock.patch("src.helpers.py_functions.os.path.exists", return_value=True)
@mock.patch("src.helpers.py_functions.open", side_effect=FileNotFoundError)
def test_fails_write_to_csv(_mock_exists, _mock_open, caplog: LogCaptureFixture):
    caplog.set_level(logging.INFO)

    with mock.patch(
        "configparser.ConfigParser.read", return_value=FAKE.pystr()
    ) and mock.patch("configparser.ConfigParser.get", return_value=FAKE.pystr()):
        with raises(FileNotFoundError):
            write_results_to_csv(FAKE.pystr(), FAKE.pydict())

    assert "Failed to write CSV" in caplog.text


def test_passes_read_query_settings():
    with mock.patch(
        "configparser.ConfigParser.read", return_value=FAKE.pystr()
    ) and mock.patch("configparser.ConfigParser.get", return_value=FAKE.pystr()):
        result = read_query_settings("query_settings")

    assert result is not None
