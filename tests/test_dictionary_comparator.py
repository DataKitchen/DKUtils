from unittest import TestCase
from dkutils.dictionary_comparator import DictionaryComparator

THREE = 'three'
DICT_1 = {'one': 1, THREE: 3}
DICT_2 = {'two': 2, THREE: 3}
DICT_3 = {'one': 1, THREE: 'III'}
KEYS_1 = DICT_1.keys()
KEYS_2 = DICT_2.keys()


class TestDictionaryComparator(TestCase):

    def test_left_equals_right_when_both_are_empty_returns_true(self):
        self.assertTrue(DictionaryComparator({}, {}).left_equals_right())

    def test_left_equals_right_when_both_are_same_returns_true(self):
        self.assertTrue(DictionaryComparator(DICT_1, DICT_1).left_equals_right())

    def test_left_equals_right_when_different_returns_false(self):
        self.assertFalse(DictionaryComparator(DICT_1, DICT_2).left_equals_right())

    def test_left_equals_right_when_keys_are_same_but_some_values_are_different_returns_false(self):
        self.assertFalse(DictionaryComparator(DICT_1, DICT_3).left_equals_right())
    def test_get_keys_only_in_left_when_keys_same_returns_empty_set(self):
        self.assertEqual(set(), DictionaryComparator(DICT_1, DICT_1).get_keys_only_in_left())

    def test_get_keys_only_in_left_returns_keys_in_left(self):
        self.assertEqual(KEYS_1 - KEYS_2, DictionaryComparator(DICT_1, DICT_2).get_keys_only_in_left())

    def test_get_keys_only_in_right_when_keys_same_returns_empty_set(self):
        self.assertEqual(set(), DictionaryComparator(DICT_1, DICT_1).get_keys_only_in_right())

    def test_get_keys_only_in_right_returns_keys_in_right(self):
        self.assertEqual(KEYS_2 - KEYS_1, DictionaryComparator(DICT_1, DICT_2).get_keys_only_in_right())

    def test_get_keys_in_both_when_keys_same_returns_empty_set(self):
        self.assertEqual(KEYS_1, DictionaryComparator(DICT_1, DICT_1).get_keys_in_both())

    def test_get_keys_in_both_returns_keys_in_both(self):
        self.assertEqual(KEYS_2 & KEYS_1, DictionaryComparator(DICT_1, DICT_2).get_keys_in_both())

    def test_get_same_keys_different_values_when_values_are_same_returns_empty_dictionary(self):
        self.assertEqual({}, DictionaryComparator(DICT_1, DICT_1).get_same_keys_different_values())

    def test_get_same_keys_different_values_when_values_are_different_returns_values(self):
        self.assertEqual({THREE: (DICT_1[THREE], DICT_3[THREE])},
                         DictionaryComparator(DICT_1, DICT_3).get_same_keys_different_values())

    def test_merge_left(self):
        self.assertEqual({**DICT_1, **DICT_3}, DictionaryComparator(DICT_1, DICT_3).merge_left())

    def test_merge_right(self):
        self.assertEqual({**DICT_3, **DICT_1}, DictionaryComparator(DICT_1, DICT_3).merge_right())

    def test_left(self):
        self.assertEqual(DICT_1, DictionaryComparator(DICT_1, DICT_2).left)

    def test_right(self):
        self.assertEqual(DICT_2, DictionaryComparator(DICT_1, DICT_2).right)