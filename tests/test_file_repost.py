import os
import shutil
import pytest
import subprocess
import tempfile
from pathlib import Path

TEMP_INPUT = "./temp/input"
TEMP_OUTPUT = "./temp/output"
SOURCE_FILE = os.path.join(TEMP_INPUT, "source_urls.txt")
DEST_FILE = os.path.join(TEMP_OUTPUT, "new_dest_urls.txt")


def setup_temp_dirs():
    os.makedirs(TEMP_INPUT, exist_ok=True)
    os.makedirs(TEMP_OUTPUT, exist_ok=True)

def cleanup_temp_dirs():
    # Only clean up output directory, preserve input directory
    if os.path.exists(TEMP_OUTPUT):
        shutil.rmtree(TEMP_OUTPUT, ignore_errors=True)

def create_temp_source_file(urls, filename=None):
    """Create a temporary source file with unique name to avoid conflicts"""
    if filename is None:
        # Create unique filename to avoid conflicts with existing files
        import uuid
        filename = f"test_source_{uuid.uuid4().hex[:8]}.txt"

    filepath = os.path.join(TEMP_INPUT, filename)
    with open(filepath, "w") as f:
        for url in urls:
            f.write(f"{url}\n")
    return filepath

def write_source_urls(urls):
    """Helper to write source URLs to test file"""
    with open(SOURCE_FILE, "w") as f:
        for url in urls:
            f.write(f"{url}\n")

def read_dest_urls():
    """Helper to read destination URLs from output file"""
    if os.path.exists(DEST_FILE):
        with open(DEST_FILE, "r") as f:
            return [line.strip() for line in f if line.strip()]
    return []

def run_repost_command(destination, source_file=None):
    """Helper to run the repost command"""
    env = os.environ.copy()
    env.update({
        "API_ID": "12345",
        "API_HASH": "testhash",
        "TEST_MODE": "1"
    })

    cmd = ["python", "-m", "src.main", "repost", "--destination", destination]
    if source_file:
        cmd.extend(["--source", source_file])

    return subprocess.run(cmd, capture_output=True, env=env)


class TestChannelTypeCombinations:
    """Test correct reposting for each channel type combination"""

    def test_public_source_to_public_dest(self, temp_dirs, mock_telethon_client):
        """Test public channel to public channel reposting"""
        setup_temp_dirs()
        write_source_urls(["https://t.me/publicsource/4"])
        dest = "@dummy_channel991"

        result = run_repost_command(dest)

        assert result.returncode == 0, f"Command failed: {result.stderr.decode()}"
        assert mock_telethon_client.send_message.called
        assert os.path.exists(DEST_FILE)

        dest_urls = read_dest_urls()
        assert len(dest_urls) == 1
        assert dest_urls[0].startswith("https://t.me/")
        cleanup_temp_dirs()

    def test_private_source_to_private_dest(self, temp_dirs, mock_telethon_client):
        """Test private channel to private channel reposting"""
        setup_temp_dirs()
        write_source_urls(["https://t.me/c/123456789/1"])
        dest = "2763892937"  # Private channel ID

        result = run_repost_command(dest)

        assert result.returncode == 0, f"Command failed: {result.stderr.decode()}"
        assert mock_telethon_client.send_message.called
        assert os.path.exists(DEST_FILE)

        dest_urls = read_dest_urls()
        assert len(dest_urls) == 1
        cleanup_temp_dirs()

    def test_public_source_to_private_dest(self, temp_dirs, mock_telethon_client):
        """Test public channel to private channel reposting"""
        setup_temp_dirs()
        write_source_urls(["https://t.me/publicsource/4"])
        dest = "2763892937"  # Private channel ID

        result = run_repost_command(dest)

        assert result.returncode == 0, f"Command failed: {result.stderr.decode()}"
        assert mock_telethon_client.send_message.called
        assert os.path.exists(DEST_FILE)
        cleanup_temp_dirs()

    def test_private_source_to_public_dest(self, temp_dirs, mock_telethon_client):
        """Test private channel to public channel reposting"""
        setup_temp_dirs()
        write_source_urls(["https://t.me/c/123456789/1"])
        dest = "@dummy_channel991"

        result = run_repost_command(dest)

        assert result.returncode == 0, f"Command failed: {result.stderr.decode()}"
        assert mock_telethon_client.send_message.called
        assert os.path.exists(DEST_FILE)
        cleanup_temp_dirs()


class TestUrlParsingAndFormatting:
    """Test type, value, and URL format assertions"""

    def test_public_channel_url_parsing(self, temp_dirs, mock_telethon_client):
        """Verify correct URL parsing for public channels"""
        setup_temp_dirs()
        write_source_urls(["https://t.me/channel/123"])
        dest = "@dummy_channel991"

        result = run_repost_command(dest)

        assert result.returncode == 0
        assert mock_telethon_client.get_messages.called
        # Verify the channel name was extracted correctly
        call_args = mock_telethon_client.get_messages.call_args
        assert call_args[0][0] == "channel"  # First positional arg should be channel name
        cleanup_temp_dirs()

    def test_private_channel_url_parsing(self, temp_dirs, mock_telethon_client):
        """Verify correct URL parsing for private channels"""
        setup_temp_dirs()
        write_source_urls(["https://t.me/c/123456789/123"])
        dest = "@dummy_channel991"

        result = run_repost_command(dest)

        assert result.returncode == 0
        assert mock_telethon_client.get_messages.called
        # Verify the channel ID was normalized with -100 prefix
        call_args = mock_telethon_client.get_messages.call_args
        assert call_args[0][0] == "-100123456789"  # Should have -100 prefix
        cleanup_temp_dirs()

    def test_channel_id_normalization(self, temp_dirs, mock_telethon_client):
        """Verify channel ID normalization (string vs integer handling)"""
        setup_temp_dirs()
        write_source_urls(["https://t.me/c/123456789/123"])
        dest = "2763892937"  # String ID that should be normalized

        result = run_repost_command(dest)

        assert result.returncode == 0
        # Verify destination entity resolution was called with normalized ID
        assert mock_telethon_client.get_entity.called
        cleanup_temp_dirs()

    def test_output_url_format(self, temp_dirs, mock_telethon_client):
        """Verify output URL format matches expected pattern"""
        setup_temp_dirs()
        write_source_urls(["https://t.me/publicsource/4"])
        dest = "@dummy_channel991"

        result = run_repost_command(dest)

        assert result.returncode == 0
        dest_urls = read_dest_urls()
        assert len(dest_urls) == 1

        # Verify URL format: https://t.me/channel/message_id
        url = dest_urls[0]
        assert url.startswith("https://t.me/")
        assert "/" in url.split("t.me/")[1]  # Should have channel/message_id format
        cleanup_temp_dirs()


class TestErrorHandling:
    """Test graceful failure on invalid input (negative scenarios)"""

    def test_invalid_url_format(self, temp_dirs, mock_telethon_client):
        """Test invalid URL format handling"""
        setup_temp_dirs()
        write_source_urls(["not_a_valid_url"])
        dest = "@dummy_channel991"

        result = run_repost_command(dest)

        assert result.returncode != 0
        assert b"invalid" in result.stderr.lower() or b"error" in result.stderr.lower()
        assert not mock_telethon_client.send_message.called
        cleanup_temp_dirs()

    def test_nonexistent_channel_error(self, temp_dirs, mock_telethon_client):
        """Test non-existent channel error handling"""
        setup_temp_dirs()
        write_source_urls(["https://t.me/nonexistent/123"])
        dest = "@dummy_channel991"

        # Mock get_messages to return None (channel not found)
        mock_telethon_client.get_messages.return_value = None

        result = run_repost_command(dest)

        # Should handle gracefully and continue with other messages
        assert result.returncode == 0
        cleanup_temp_dirs()

    def test_permission_denied_error(self, temp_dirs, mock_telethon_client):
        """Test permission denied error handling"""
        setup_temp_dirs()
        write_source_urls(["https://t.me/privatechannel/123"])
        dest = "@dummy_channel991"

        # Mock send_message to raise permission error
        from telethon.errors import ChatAdminRequiredError
        mock_telethon_client.send_message.side_effect = ChatAdminRequiredError("Permission denied")

        result = run_repost_command(dest)

        # Should handle gracefully and continue
        assert result.returncode == 0
        cleanup_temp_dirs()

    def test_empty_input_file(self, temp_dirs, mock_telethon_client):
        """Test empty input file handling"""
        setup_temp_dirs()
        write_source_urls([])  # Empty file
        dest = "@dummy_channel991"

        result = run_repost_command(dest)

        assert result.returncode == 0  # Should handle empty file gracefully
        assert not mock_telethon_client.send_message.called
        cleanup_temp_dirs()

    def test_malformed_url_handling(self, temp_dirs, mock_telethon_client):
        """Test malformed URL handling"""
        setup_temp_dirs()
        write_source_urls([
            "https://t.me/",  # Missing channel and message
            "https://t.me/channel/",  # Missing message ID
            "https://t.me/c/",  # Missing channel ID and message
            "https://t.me/c/abc/123",  # Non-numeric channel ID
        ])
        dest = "@dummy_channel991"

        result = run_repost_command(dest)

        assert result.returncode != 0  # Should fail on invalid URLs
        assert not mock_telethon_client.send_message.called
        cleanup_temp_dirs()


class TestFileIOOperations:
    """Test file I/O operations and atomic writes"""

    def test_atomic_file_write(self, temp_dirs, mock_telethon_client):
        """Test that output file is written atomically"""
        setup_temp_dirs()
        write_source_urls(["https://t.me/publicsource/4"])
        dest = "@dummy_channel991"

        # Check that temp file exists during write
        temp_file = os.path.join(TEMP_OUTPUT, "new_dest_urls.txt.tmp")

        result = run_repost_command(dest)

        assert result.returncode == 0
        assert os.path.exists(DEST_FILE)
        # Temp file should not exist after successful write
        assert not os.path.exists(temp_file)
        cleanup_temp_dirs()

    def test_file_existence_validation(self, temp_dirs, mock_telethon_client):
        """Test file existence and content validation"""
        setup_temp_dirs()
        # Don't create source file - should fail
        dest = "@dummy_channel991"

        result = run_repost_command(dest)

        assert result.returncode != 0
        assert b"does not exist" in result.stderr
        cleanup_temp_dirs()

    def test_multiple_messages_processing(self, temp_dirs, mock_telethon_client):
        """Test processing multiple messages from input file"""
        setup_temp_dirs()
        write_source_urls([
            "https://t.me/publicsource/1",
            "https://t.me/publicsource/2",
            "https://t.me/publicsource/3"
        ])
        dest = "@dummy_channel991"

        result = run_repost_command(dest)

        assert result.returncode == 0
        dest_urls = read_dest_urls()
        assert len(dest_urls) == 3
        cleanup_temp_dirs()


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases"""

    def test_mixed_channel_types_in_single_file(self, temp_dirs, mock_telethon_client):
        """Test processing mixed public and private channel URLs in same file"""
        setup_temp_dirs()
        write_source_urls([
            "https://t.me/publicsource/1",
            "https://t.me/c/123456789/2",
            "https://t.me/anotherpublic/3"
        ])
        dest = "@dummy_channel991"

        result = run_repost_command(dest)

        assert result.returncode == 0
        dest_urls = read_dest_urls()
        assert len(dest_urls) == 3
        cleanup_temp_dirs()

    def test_custom_source_file_path(self, temp_dirs, mock_telethon_client):
        """Test using custom source file path"""
        setup_temp_dirs()
        custom_source = create_temp_source_file(["https://t.me/publicsource/4"])

        dest = "@dummy_channel991"

        result = run_repost_command(dest, custom_source)

        assert result.returncode == 0
        assert mock_telethon_client.send_message.called
        cleanup_temp_dirs()
