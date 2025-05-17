import os
import unittest
from unittest.mock import patch, mock_open, MagicMock
from app.packfile import unpack_packfile
from app.objects import hash_object

# filepath: /Users/carsonjohnson/Documents/CodeCrafters/codecrafters-git-python/app/test_packfile.py

class TestPackfile(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data=b"PACK\x00\x00\x00\x02\x00\x00\x00\x01mock_data")
    @patch("app.objects.hash_object")
    def test_unpack_packfile(self, mock_hash_object, mock_open_file):
        # Mock hash_object to track calls
        mock_hash_object.return_value = "mock_sha"

        # Call the function
        unpack_packfile("/mock/path/packfile.pack")

        # Assertions
        mock_open_file.assert_called_once_with("/mock/path/packfile.pack", "rb")
        mock_hash_object.assert_called()  # Ensure hash_object is called

    # Skeleton for testing `process_commit`
    def test_process_commit(self):
        # TODO: Mock zlib.decompress and hash_object
        pass

    # Skeleton for testing `process_tree`
    def test_process_tree(self):
        # TODO: Mock zlib.decompress and write_tree
        pass

    # Skeleton for testing `apply_delta`
    def test_apply_delta(self):
        # TODO: Simulate delta data and base data
        pass

    # Skeleton for testing `parse_copy_instruction`
    def test_parse_copy_instruction(self):
        # TODO: Simulate instruction bytes and verify parsing
        pass

    # Skeleton for testing `clone_repo`
    def test_clone_repo(self):
        # TODO: Mock fetch_pack_file, save_pack_file, and unpack_packfile
        pass

if __name__ == "__main__":
    unittest.main()