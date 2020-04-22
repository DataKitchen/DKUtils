from unittest import TestCase

from dkutils.validation import validate_globals


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
