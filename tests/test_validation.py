from unittest import TestCase

from dkutils.validation import validate_globals


class TestValidation(TestCase):

    def test_valid_global(self):
        validate_globals(['__name__'], globals())

    def test_valid_globals(self):
        validate_globals(['__name__', '__file__'], globals())

    def test_invalid_global(self):
        with self.assertRaises(NameError):
            validate_globals(['Foo'], globals())

    def test_invalid_globals(self):
        with self.assertRaises(NameError):
            validate_globals(['Foo', 'Bar', '__name__'], globals())
