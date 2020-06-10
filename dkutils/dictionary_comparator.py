class DictionaryComparator:

    def __init__(self, left, right):
        """Utility that can be used to perform a shallow comparison on two dictionaries. """
        self._left = left
        self._right = right

    def __eq__(self, other):
        if isinstance(other, DictionaryComparator):
            return self._left == other._left and self._right == other._right
        return NotImplemented

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

    def left_equals_right(self):
        """
        Test is the the left dictionary is equal to the right dictionary.

        Returns
        -------
        bool
            Returns True if the keys and values in left are equal to those in right
        """
        return self._left == self._right

    def get_keys_only_in_left(self):
        """
        Returns the set of keys that are only present in the left side

        Returns
        _______
        set
            The keys that are only present in the left
        """
        return self._left.keys() - self._right.keys()

    def get_keys_only_in_right(self):
        """
        Returns the set of keys that are only present in the right side

        Returns
        _______
        set
            The keys that are only present in the right
        """
        return self._right.keys() - self._left.keys()

    def get_keys_in_both(self):
        """
        Return the set of keys that are present on botch sides

        Returns
        _______
        set
            The keys that are present in both sides
        """
        return self._right.keys() & self._left.keys()

    def get_same_keys_different_values(self):
        """
        Get the key and values where the keys were the same for left and right but the values differed

        Returns
        -------
        dict
            A dictionary where the key is the keys that occured in both left and right and the  value is a tuple made
            up of the value from the left and the value from the right
        """
        return {
            key: (self._left[key], self._right[key])
            for key in self.get_keys_in_both()
            if self._left[key] != self._right[key]
        }

    def merge_left(self):
        """
        Merge the dictionaries with preference being given to dictionary on the right if a key exists on both sides.
        For example given:
            left = {'one': 1, 'two': 2, 'three': 3 }
            right = {'two': 2, 'three': 'III' }
        merge_left will result in the following:
            {'one': 1, 'two': 2, 'three': 'III', 'four': 4 }

        Returns
        _______
        dict
            A dictionary containing the keys and values from left and right. The value from the dictionary on the right
            will be returned if a key exists in both dictionaries
        """
        return {**self._left, **self._right}

    def merge_right(self):
        """
        Merge the dictionaries with preference being given to dictionary on the left if a key exists on both sides.
        For example given:
            left = {'one': 1, 'two': 2, 'three': 3 }
            right = {'two': 2, 'three': 'III' }
        merge_left will result in the following:
            {'one': 1, 'two': 2, 'three': '3', 'four': 4 }

        Returns
        _______
        dict
            A dictionary containing the keys and values from left and right. The value from the dictionary on the left
            will be returned if a key exists in both dictionaries
        """
        return {**self._right, **self._left}
