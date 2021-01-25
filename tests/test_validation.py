import json
import logging
import pathlib
from unittest import TestCase

from dkutils.validation import get_max_concurrency, validate_globals, ensure_pathlib, set_logging_level

GLOBALS_CONFIG_FILE = pathlib.Path(__file__).parent / "globals_config.json"


class TestValidation(TestCase):

    def tearDown(self):
        if GLOBALS_CONFIG_FILE.exists():
            GLOBALS_CONFIG_FILE.unlink()

    def test_valid_globals(self):
        validate_globals(['__name__', '__file__'])

    def test_invalid_globals(self):
        with self.assertRaises(NameError):
            validate_globals(['Foo', 'Bar', '__name__'])

    def test_zero_valid(self):
        global zero
        zero = 0
        validate_globals(['zero'])

    def test_empty_string_valid(self):
        global empty_string
        empty_string = ''
        validate_globals(['empty_string'])

    def test_none_valid(self):
        global none
        none = None
        validate_globals(['none'])

    def test_undefined_invalid(self):
        global undefined
        with self.assertRaises(NameError):
            validate_globals(['undefined'])

    def test_get_max_concurrency(self):
        self.assertEqual(10, get_max_concurrency(10, None))
        self.assertEqual(10, get_max_concurrency(10, 12))
        self.assertEqual(1, get_max_concurrency(10, -1))
        self.assertEqual(5, get_max_concurrency(10, 5))

    def test_valid_globals_when_value_not_changed(self):
        global FOO
        FOO = '[CHANGE_ME]'
        with self.assertRaises(NameError) as cm:
            validate_globals(['FOO'])
        self.assertEqual(
            "\n\tGlobal variables with values that need to be changed: ['FOO']",
            cm.exception.args[0]
        )

    def test_valid_globals_when_globals_config_file_exists(self):
        global_var_name = 'BAZ'
        info = {global_var_name: "somevalue"}
        with GLOBALS_CONFIG_FILE.open('w') as output:
            json.dump(info, output)
        validate_globals([global_var_name])
        self.assertEqual(info[global_var_name], globals().get(global_var_name))

    def test_ensure_pathlib_str(self):
        p = ensure_pathlib('this/that.txt')
        self.assertTrue(isinstance(p, pathlib.PurePath))

    def test_ensure_pathlib_pathlib(self):
        orig_path = pathlib.Path('this/that.txt')
        new_path = ensure_pathlib(orig_path)
        self.assertEqual(orig_path, new_path)

    def test_ensure_pathlib_None(self):
        with self.assertRaises(TypeError) as cm:
            ensure_pathlib(None)
        self.assertEqual(
            "Expected str or pathlib.PurePath type, but found <class 'NoneType'>",
            cm.exception.args[0]
        )

    def test_ensure_pathlib_int(self):
        with self.assertRaises(TypeError) as cm:
            ensure_pathlib(1)
        self.assertEqual(
            "Expected str or pathlib.PurePath type, but found <class 'int'>", cm.exception.args[0]
        )

    def test_set_logging_level_when_no_logger(self):
        global LOGGER
        if "LOGGER" in globals():
            del LOGGER
        set_logging_level()
        self.assertEqual(LOGGER.getEffectiveLevel(), logging.INFO)
        del LOGGER

    def test_set_logging_level_when_logger_exists(self):
        global LOGGER
        LOGGER = logging.getLogger()
        set_logging_level(logging.DEBUG)
        self.assertEqual(LOGGER.getEffectiveLevel(), logging.DEBUG)
        del LOGGER
