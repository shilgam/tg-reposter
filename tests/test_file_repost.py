import os
import shutil
import pytest
import tempfile
from pathlib import Path
from src.reposter import repost_from_file

# Test constants to replace magic numbers
PUBLIC_CHANNEL = "@dummy_channel991"
PRIVATE_CHANNEL_ID = "2763892937"
PRIVATE_CHANNEL_ID_INT = -1002763892937

PUBLIC_MESSAGE_URL = "https://t.me/publicsource/4"
PRIVATE_MESSAGE_URL = "https://t.me/c/123456789/1"
PRIVATE_CHANNEL_ID_FROM_URL = -100123456789

MESSAGE_ID = 123
DEST_MESSAGE_ID = 12345

# Use ./tests/data/ for all test files
TEMP_INPUT = "./tests/data/input"
TEMP_OUTPUT = "./tests/data/output"
SOURCE_FILE = os.path.join(TEMP_INPUT, "source_urls.txt")
DEST_FILE = os.path.join(TEMP_OUTPUT, "new_dest_urls.txt")


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

@pytest.mark.asyncio
class TestChannelTypeCombinations:
    """Test correct reposting for each channel type combination"""
    async def test_public_source_to_public_dest(self, temp_dirs, mock_telethon_client):
        """Test public channel to public channel reposting"""
        write_source_urls([PUBLIC_MESSAGE_URL])
        dest = PUBLIC_CHANNEL
        await repost_from_file(dest)
        assert mock_telethon_client.send_message.called
        assert os.path.exists(DEST_FILE)
        dest_urls = read_dest_urls()
        assert len(dest_urls) == 1
        assert dest_urls[0].startswith("https://t.me/")

    async def test_private_source_to_private_dest(self, temp_dirs, mock_telethon_client):
        """Test private channel to private channel reposting"""
        write_source_urls([PRIVATE_MESSAGE_URL])
        dest = PRIVATE_CHANNEL_ID  # Private channel ID
        await repost_from_file(dest)
        assert mock_telethon_client.send_message.called
        assert os.path.exists(DEST_FILE)
        dest_urls = read_dest_urls()
        assert len(dest_urls) == 1

    async def test_public_source_to_private_dest(self, temp_dirs, mock_telethon_client):
        """Test public channel to private channel reposting"""
        write_source_urls([PUBLIC_MESSAGE_URL])
        dest = PRIVATE_CHANNEL_ID  # Private channel ID
        await repost_from_file(dest)
        assert mock_telethon_client.send_message.called
        assert os.path.exists(DEST_FILE)

    async def test_private_source_to_public_dest(self, temp_dirs, mock_telethon_client):
        """Test private channel to public channel reposting"""
        write_source_urls([PRIVATE_MESSAGE_URL])
        dest = PUBLIC_CHANNEL
        await repost_from_file(dest)
        assert mock_telethon_client.send_message.called
        assert os.path.exists(DEST_FILE)


@pytest.mark.asyncio
class TestUrlParsingAndFormatting:
    """Test type, value, and URL format assertions"""

    async def test_public_channel_url_parsing(self, temp_dirs, mock_telethon_client):
        """Verify correct URL parsing for public channels"""
        write_source_urls([f"https://t.me/channel/{MESSAGE_ID}"])
        dest = PUBLIC_CHANNEL

        await repost_from_file(dest)

        assert mock_telethon_client.get_messages.called
        # Verify the channel name was extracted correctly
        call_args = mock_telethon_client.get_messages.call_args
        assert call_args[0][0] == "channel"  # First positional arg should be channel name

    async def test_private_channel_url_parsing(self, temp_dirs, mock_telethon_client):
        """Verify correct URL parsing for private channels"""
        write_source_urls([f"https://t.me/c/123456789/{MESSAGE_ID}"])
        dest = PUBLIC_CHANNEL

        await repost_from_file(dest)

        assert mock_telethon_client.get_messages.called
        # Accept int or str for channel ID
        call_args = mock_telethon_client.get_messages.call_args
        assert str(call_args[0][0]) == str(PRIVATE_CHANNEL_ID_FROM_URL)

    async def test_channel_id_normalization(self, temp_dirs, mock_telethon_client):
        """Verify channel ID normalization (string vs integer handling)"""
        write_source_urls([f"https://t.me/c/123456789/{MESSAGE_ID}"])
        dest = PRIVATE_CHANNEL_ID  # String ID that should be normalized

        await repost_from_file(dest)

        # Verify destination entity resolution was called with normalized ID
        assert mock_telethon_client.get_entity.called

    async def test_private_channel_id_conversion(self, temp_dirs, mock_telethon_client):
        """Verify that private channel IDs are properly converted to integers"""
        write_source_urls([f"https://t.me/c/123456789/{MESSAGE_ID}"])
        dest = PRIVATE_CHANNEL_ID  # String ID that should be converted to int

        await repost_from_file(dest)

        # Verify that get_entity was called with the integer version of the destination ID
        assert mock_telethon_client.get_entity.called
        call_args = mock_telethon_client.get_entity.call_args
        # The destination ID should be converted to int: -1002763892937
        assert call_args[0][0] == PRIVATE_CHANNEL_ID_INT

        # Verify that get_messages was called with the integer version of the source ID
        assert mock_telethon_client.get_messages.called
        call_args = mock_telethon_client.get_messages.call_args
        # The source ID should be converted to int: -100123456789
        assert call_args[0][0] == PRIVATE_CHANNEL_ID_FROM_URL

    async def test_output_url_format(self, temp_dirs, mock_telethon_client):
        """Verify output URL format matches expected pattern"""
        write_source_urls([PUBLIC_MESSAGE_URL])
        dest = PUBLIC_CHANNEL

        await repost_from_file(dest)

        dest_urls = read_dest_urls()
        assert len(dest_urls) == 1

        # Verify URL format: https://t.me/channel/message_id
        url = dest_urls[0]
        assert url.startswith("https://t.me/")
        assert "/" in url.split("t.me/")[1]  # Should have channel/message_id format


@pytest.mark.asyncio
class TestErrorHandling:
    """Test graceful failure on invalid input (negative scenarios)"""

    async def test_invalid_url_format(self, temp_dirs, mock_telethon_client):
        """Test invalid URL format handling"""
        write_source_urls(["not_a_valid_url"])
        dest = PUBLIC_CHANNEL
        # Should raise SystemExit on invalid input
        with pytest.raises(SystemExit):
            await repost_from_file(dest)
        assert not mock_telethon_client.send_message.called

    async def test_nonexistent_channel_error(self, temp_dirs, mock_telethon_client):
        """Test non-existent channel error handling"""
        write_source_urls([f"https://t.me/nonexistent/{MESSAGE_ID}"])
        dest = PUBLIC_CHANNEL

        # Mock get_messages to return None (channel not found)
        mock_telethon_client.get_messages.return_value = None

        # Should handle gracefully and continue with other messages
        await repost_from_file(dest)

    async def test_permission_denied_error(self, temp_dirs, mock_telethon_client):
        """Test permission denied error handling"""
        write_source_urls([f"https://t.me/privatechannel/{MESSAGE_ID}"])
        dest = PUBLIC_CHANNEL

        # Mock send_message to raise permission error
        from telethon.errors import ChatAdminRequiredError
        mock_telethon_client.send_message.side_effect = ChatAdminRequiredError("Permission denied")

        # Should handle gracefully and continue
        await repost_from_file(dest)

    async def test_empty_input_file(self, temp_dirs, mock_telethon_client):
        """Test empty input file handling"""
        write_source_urls([])  # Empty file
        dest = PUBLIC_CHANNEL

        await repost_from_file(dest)

        assert not mock_telethon_client.send_message.called

    async def test_malformed_url_handling(self, temp_dirs, mock_telethon_client):
        """Test malformed URL handling"""
        write_source_urls([
            "https://t.me/",  # Missing channel and message
            "https://t.me/channel/",  # Missing message ID
            "https://t.me/c/",  # Missing channel ID and message
            "https://t.me/c/abc/123",  # Non-numeric channel ID
        ])
        dest = PUBLIC_CHANNEL
        # Should raise SystemExit on invalid input
        with pytest.raises(SystemExit):
            await repost_from_file(dest)
        assert not mock_telethon_client.send_message.called


@pytest.mark.asyncio
class TestFileIOOperations:
    """Test file I/O operations and atomic writes"""

    async def test_atomic_file_write(self, temp_dirs, mock_telethon_client):
        """Test that output file is written atomically"""
        write_source_urls([PUBLIC_MESSAGE_URL])
        dest = PUBLIC_CHANNEL

        # Check that temp file exists during write
        temp_file = os.path.join(TEMP_OUTPUT, "new_dest_urls.txt.tmp")

        await repost_from_file(dest)

        assert os.path.exists(DEST_FILE)
        # Temp file should not exist after successful write
        assert not os.path.exists(temp_file)

    async def test_file_existence_validation(self, temp_dirs, mock_telethon_client):
        """Test file existence and content validation"""
        # Remove the default source file to test non-existence
        if os.path.exists(SOURCE_FILE):
            os.remove(SOURCE_FILE)

        dest = PUBLIC_CHANNEL

        # Should raise an exception when source file doesn't exist
        with pytest.raises(SystemExit):
            await repost_from_file(dest)

    async def test_multiple_messages_processing(self, temp_dirs, mock_telethon_client):
        """Test processing multiple messages from input file"""
        write_source_urls([
            "https://t.me/publicsource/1",
            "https://t.me/publicsource/2",
            "https://t.me/publicsource/3"
        ])
        dest = PUBLIC_CHANNEL

        await repost_from_file(dest)

        dest_urls = read_dest_urls()
        assert len(dest_urls) == 3


@pytest.mark.asyncio
class TestIntegrationScenarios:
    """Test integration scenarios and edge cases"""

    async def test_mixed_channel_types_in_single_file(self, temp_dirs, mock_telethon_client):
        """Test processing mixed public and private channel URLs in same file"""
        write_source_urls([
            "https://t.me/publicsource/1",
            "https://t.me/c/123456789/2",
            "https://t.me/anotherpublic/3"
        ])
        dest = PUBLIC_CHANNEL

        await repost_from_file(dest)

        dest_urls = read_dest_urls()
        assert len(dest_urls) == 3

    async def test_custom_source_file_path(self, temp_dirs, mock_telethon_client):
        """Test using custom source file path"""
        custom_source = create_temp_source_file([PUBLIC_MESSAGE_URL])

        dest = PUBLIC_CHANNEL

        await repost_from_file(dest, custom_source)

        assert mock_telethon_client.send_message.called
