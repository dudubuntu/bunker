import sys, os
import pytest


class FileHelper():
    def __init__(self, api):
        self.api = api

    def remove_file(self, filepath):
        if os.path.isfile(filepath):
            print(f'Removing the file "{filepath}"...')
            os.unlink(filepath)
        else:
            print(f'No such file "{filepath}"')


@pytest.fixture
def tmp_file(tmp_path):
    f = tmp_path / 'fh.txt'
    f.write_text('Content')
    return f
    


class TestFileHelper:
    def test_init(self):
        api = object()
        fh = FileHelper(api)
        assert fh.api is api

    def test_remove_file(self, tmp_file):
        api = object()
        fh = FileHelper(api)
        fh.remove_file(tmp_file)
        assert os.path.exists(tmp_file) is False