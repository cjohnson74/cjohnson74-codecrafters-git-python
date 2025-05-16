import os
import unittest
from unittest.mock import patch, mock_open, MagicMock
from app.commands import clone_repo
from objects import read_tree_object
from packfile import fetch_pack_file, save_pack_file, unpack_packfile

class TestCloneRepo(unittest.TestCase):
    @patch("os.makesirs")
    @patch("app.network.fetch_pack_file")
    @patch("app.packfile.save_pack_file")
    @patch("app.packfile.unpack_packfile")
    @patch("app.objects.read_tree_object")
    def test_clone_repo(self, mock_read_tree_object, mock_unpack_packfile, mock_save_pack_file, mock_fetch_pack_file, mock_makedirs):
        # Mock responses
        mock_fetch_pack_file.return_value = b"mock_packfile_data"
        mock_save_pack_file.return_value = "/mock/path/packfile.pack"
        mock_unpack_packfile.return_value = [
            {"mode": "100644", "name": "file.txt", "sha": "1234567890abcdef1234567890abcdef12345678"}
        ]
        
        # Call clone_repo
        git_url = "https://example.com/repo.git"
        directory = "test_repo"
        clone_repo(git_url, directory)
        
        # Assertions
        mock_makedirs.assert_called_once_with(directory, exist_ok=True)
        mock_fetch_pack_file.assert_called_once_with(git_url)
        mock_save_pack_file.assert_called_once_with(b"mock_packfile_data", directory)
        mock_unpack_packfile.assert_called_once_with("/mock/path/packfile.pack")
        mock_read_tree_object.assert_called_once_with("1234567890abcdef1234567890abcdef12345678")        

    @patch("socket.create_connection")
    @patch("ssl.create_default_context")
    def test_fetch_pack_file(self, mock_ssl_context, mock_socket):
        mock_socket.return_value.recv.side_effect = [b"mock_response", b""]
        git_url = "https://example.com/repo.git"
        packfile_data = fetch_pack_file(git_url)
        self.assertIn(b"mock_response", packfile_data)
        
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_save_pack_file(self, mock_makedirs, mock_open_file):
        pack_file_res = b"PACKmock_data"
        directory = "test_repo"
        packfile_path = save_pack_file(pack_file_res, directory)
        mock_makedirs.assert_called_once_with(os.path.join(directory, ".git", "objects", "pack"), exist_ok=True)
        mock_open_file.assert_called_once_with(os.path.join(directory, ".git", "objects", "pack", "packfile.pack"), "wb")
        self.assertEqual(packfile_path, os.path.join(directory, ".git", "objects", "pack", "packfile.pack"))
    
    @patch("builtins.open", new_callable=mock_open, read_data=b"PACK\x00\x00\x00\x02\x00\x00\x00\x01mock_data")
    def test_unpack_packfile(self, mock_open_file):
        unpack_packfile("/mock/path/packfile.pack")
        mock_open_file.assert_called_once_with("/mock/path/packfile.pack", "rb")
        
    @patch("builtins.open", new_callable=mock_open, read_data=b"x\x9c+\xca\xcfMUH\xce\xcf-(J-.NMQHI,I\x04\x00\x1a\x0b\x04\x1d")
    @patch("os.path.exists", return_value=True)
    def test_read_tree_object(self, mock_exists, mock_open_file):
        sha = "1234567890abcdef1234567890abcdef12345678"
        entries = read_tree_object(sha)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["mode"], "100644")
        self.assertEqual(entries[0]["name"], "file.txt")
        self.assertEqual(entries[0]["sha"], "1234567890abcdef1234567890abcdef12345678")
    
if __name__ == "__main__":
    unittest.main()