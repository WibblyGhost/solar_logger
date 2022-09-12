# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

import logging
from unittest import mock

from pytest import LogCaptureFixture

from classes.py_functions import read_query_settings, write_results_to_csv
from tests.config.consts import FAKE


@mock.patch("classes.py_functions.os.path.exists")
@mock.patch("classes.py_functions.open", mock.mock_open())
def test_passes_write_to_csv(exists, caplog: LogCaptureFixture):
    exists.return_value = True
    caplog.set_level(logging.INFO)
    with mock.patch(
        "configparser.ConfigParser.read", return_value=FAKE.pystr()
    ) and mock.patch("configparser.ConfigParser.get", return_value=FAKE.pystr()):
        write_results_to_csv(FAKE.pystr(), FAKE.pydict())

    assert "Wrote rows into CSV file at:" in caplog.text


def test_passes_read_query_settings():
    with mock.patch(
        "configparser.ConfigParser.read", return_value=FAKE.pystr()
    ) and mock.patch("configparser.ConfigParser.get", return_value=FAKE.pystr()):
        result = read_query_settings("query_settings")

    assert result is not None
