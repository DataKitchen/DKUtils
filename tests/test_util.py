from unittest import TestCase

from dkutils.util import FileNameGenerator


class TestFileNameGeneratorp(TestCase):

    def test_getFileName(self):
        sut = FileNameGenerator()
        extensions = ['png', 'html']
        for extension in extensions:
            for i in range(0, 1):
                self.assertEqual(f'file_00{i}.{extension}', sut.getFileName(extension))
