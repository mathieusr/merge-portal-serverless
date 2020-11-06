import tempfile
import os
from . import handler

def test_make_empty_dir():

    with tempfile.TemporaryDirectory() as temp_dir_path:

        os.mkdir(os.path.join(temp_dir_path, "unit_test"))

        with open(os.path.join(temp_dir_path, "unit_test", "test.txt"), "w"):

            pass

        assert len(os.listdir(os.path.join(temp_dir_path, "unit_test"))) == 0