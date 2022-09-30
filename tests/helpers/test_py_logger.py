# pylint: disable=missing-function-docstring, missing-module-docstring, no-self-use
import logging

import pytest
from pytest import LogCaptureFixture
from tests.config.consts import APP_CONFIG, TEST_CONFIG

from src.helpers.py_logger import create_logger


class TestPyLogger:
    """Test class for Py Logger"""

    def test_passes_config_files_are_consistent(self):
        app_config = None
        test_config = None

        with open(APP_CONFIG) as app_fh:
            app_config = app_fh.read()
        with open(TEST_CONFIG) as test_fh:
            test_config = test_fh.read()

        assert (
            app_config == test_config
        ), "Configurations files are different between environments"

    @pytest.mark.xfail(reason="Py Logger testing not implemented yet")
    def test_todo(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO)
        _ = create_logger(config_name=TEST_CONFIG)
