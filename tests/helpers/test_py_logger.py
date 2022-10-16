# pylint: disable=missing-function-docstring, missing-module-docstring
import logging

import pytest
from pytest import LogCaptureFixture

from src.helpers.py_logger import create_logger
from tests.config.consts import TEST_CONFIG


class TestPyLogger:
    """Test class for Py Logger"""

    @pytest.mark.xfail(reason="Py Logger testing not implemented yet")
    def test_todo(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO)
        _ = create_logger(config_name=TEST_CONFIG)
