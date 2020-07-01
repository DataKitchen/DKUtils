from unittest import TestCase

from dkutils.validation import get_max_concurrency, validate_globals


class TestValidation(TestCase):

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
            f"\n\tGlobal variables with values that need to be changed: ['FOO']",
            cm.exception.args[0]
        )
