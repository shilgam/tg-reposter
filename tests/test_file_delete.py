import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.delete import delete_from_file
from telethon.errors import ChatAdminRequiredError
from click.testing import CliRunner
from src.cli import cli
from src.utils_files import dest_slug
import re
from datetime import datetime

# Test constants to replace magic numbers and strings
PUBLIC_MESSAGE_URL = "https://t.me/publicsource/4"
PRIVATE_MESSAGE_URL = "https://t.me/c/123456789/1"
PRIVATE_CHANNEL_ID_FROM_URL = -100123456789

MESSAGE_ID = 123

TEMP_INPUT = "./tests/data/input"
TEMP_OUTPUT = "./tests/data/output"
TEST_SLUG = 'testslug'
MARKED_FILE = os.path.join(TEMP_OUTPUT, f"20250101_120000_{TEST_SLUG}.marked_for_deletion.txt")
DELETED_PATTERN = f"*_{TEST_SLUG}.deleted_at_*.txt"

def make_marked_file(slug=TEST_SLUG, output_dir=TEMP_OUTPUT):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"{ts}_{slug}.marked_for_deletion.txt")
    return path, ts

def find_deleted_file(slug=TEST_SLUG, output_dir=TEMP_OUTPUT, publish_ts=None):
    pattern = f"*_{slug}.deleted_at_*.txt"
    files = list(Path(output_dir).glob(pattern))
    if publish_ts:
        files = [f for f in files if f.name.startswith(f"{publish_ts}_")]
    return files

class TestDeleteFromFile:
    """Main test suite for delete_from_file functionality"""

    class TestFileAutoDetection:
        """Tests for automatic file detection logic"""

        @pytest.mark.asyncio
        async def test_auto_detect_with_valid_file(self, temp_dirs, mock_telethon_client):
            """Test auto-detection when valid file exists"""
            urls = [PUBLIC_MESSAGE_URL]
            marked_file, ts = make_marked_file()
            with open(marked_file, "w") as f:
                f.write(f"{urls[0]}\n")
            await delete_from_file(None, destination=TEST_SLUG)
            assert mock_telethon_client.delete_messages.call_count == len(urls)
            deleted_files = find_deleted_file(publish_ts=ts)
            assert len(deleted_files) == 1

        @pytest.mark.asyncio
        async def test_auto_detect_with_no_files(self, temp_dirs, mock_telethon_client):
            for f in Path(TEMP_OUTPUT).glob(f"*_{TEST_SLUG}.marked_for_deletion.txt"):
                f.unlink()
            with pytest.raises(FileNotFoundError, match="No .marked_for_deletion.txt file found"):
                await delete_from_file(None, destination=TEST_SLUG)

        @pytest.mark.asyncio
        async def test_auto_detect_with_multiple_files(self, temp_dirs, mock_telethon_client):
            import time
            older_file = os.path.join(TEMP_OUTPUT, f"20240101_120000_{TEST_SLUG}.marked_for_deletion.txt")
            with open(older_file, "w") as f:
                f.write("https://t.me/old/1\n")
            newer_file, ts = make_marked_file()
            with open(newer_file, "w") as f:
                f.write("https://t.me/new/1\n")
            await delete_from_file(None, destination=TEST_SLUG)
            deleted_files = find_deleted_file(publish_ts=ts)
            assert len(deleted_files) == 1

    class TestURLParsing:
        """Tests for URL parsing and channel type handling"""

        @pytest.mark.asyncio
        async def test_public_channel_url_parsing(self, temp_dirs, mock_telethon_client):
            """Test parsing of public channel URLs"""
            urls = [f"https://t.me/channelname/{MESSAGE_ID}"]
            with open(MARKED_FILE, "w") as f:
                f.write(f"{urls[0]}\n")
            await delete_from_file(MARKED_FILE, destination=TEST_SLUG)

            # Verify correct channel entity was requested
            mock_telethon_client.get_entity.assert_called_with("channelname")
            assert mock_telethon_client.delete_messages.call_count == 1

        @pytest.mark.asyncio
        async def test_private_channel_url_parsing(self, temp_dirs, mock_telethon_client):
            """Test parsing of private channel URLs"""
            urls = [f"https://t.me/c/123456789/{MESSAGE_ID}"]
            with open(MARKED_FILE, "w") as f:
                f.write(f"{urls[0]}\n")
            await delete_from_file(MARKED_FILE, destination=TEST_SLUG)

            # Verify correct private channel entity was requested
            expected_channel_id = PRIVATE_CHANNEL_ID_FROM_URL
            mock_telethon_client.get_entity.assert_called_with(expected_channel_id)

        @pytest.mark.asyncio
        async def test_mixed_channel_types(self, temp_dirs, mock_telethon_client):
            """Test processing mixed public and private channel URLs"""
            urls = [
                PUBLIC_MESSAGE_URL,
                PRIVATE_MESSAGE_URL
            ]
            with open(MARKED_FILE, "w") as f:
                for url in urls:
                    f.write(f"{url}\n")

            await delete_from_file(MARKED_FILE, destination=TEST_SLUG)

            assert mock_telethon_client.delete_messages.call_count == len(urls)

        @pytest.mark.asyncio
        async def test_invalid_url_formats(self, temp_dirs, mock_telethon_client, capsys):
            """Test handling of invalid URL formats"""
            urls = [
                "https://t.me/",  # incomplete
                "not_a_url",      # invalid format
                f"https://t.me/c/abc/{MESSAGE_ID}",  # invalid private format
                f"https://t.me/validchannel/{MESSAGE_ID}"  # valid one
            ]
            with open(MARKED_FILE, "w") as f:
                for url in urls:
                    f.write(f"{url}\n")

            await delete_from_file(MARKED_FILE, destination=TEST_SLUG)

            # Only valid URL should be processed
            assert mock_telethon_client.delete_messages.call_count == 1
            # Invalid URLs should be logged
            captured = capsys.readouterr()
            assert "Invalid URL" in captured.err or "Error parsing" in captured.err

    class TestErrorHandling:
        """Tests for error handling and data integrity"""

        @pytest.mark.asyncio
        async def test_channel_entity_resolution_failure(self, temp_dirs, mock_telethon_client):
            """Test fallback when get_entity fails"""
            urls = [f"https://t.me/problematic/{MESSAGE_ID}"]
            with open(MARKED_FILE, "w") as f:
                f.write(f"{urls[0]}\n")

            # Mock get_entity to fail, get_input_entity to succeed
            mock_telethon_client.get_entity.side_effect = Exception("Entity not found")
            mock_telethon_client.get_input_entity.return_value = Mock()

            await delete_from_file(MARKED_FILE, destination=TEST_SLUG)

            # Verify fallback was attempted
            mock_telethon_client.get_input_entity.assert_called()

        @pytest.mark.asyncio
        async def test_complete_entity_resolution_failure(self, temp_dirs, mock_telethon_client):
            """Test system exit when both entity resolution methods fail"""
            urls = [f"https://t.me/problematic/{MESSAGE_ID}"]
            with open(MARKED_FILE, "w") as f:
                f.write(f"{urls[0]}\n")

            # Mock both to fail
            mock_telethon_client.get_entity.side_effect = Exception("Entity not found")
            mock_telethon_client.get_input_entity.side_effect = Exception("Input entity failed")

            with pytest.raises(SystemExit, match="1"):
                await delete_from_file(MARKED_FILE, destination=TEST_SLUG)

        @pytest.mark.asyncio
        async def test_delete_operation_failure_mid_process(self, temp_dirs, mock_telethon_client):
            """Test atomic behavior when deletion fails mid-process"""
            urls = [
                "https://t.me/channel1/1",
                "https://t.me/channel2/2"
            ]
            with open(MARKED_FILE, "w") as f:
                for url in urls:
                    f.write(f"{url}\n")

            # Mock delete_messages to fail on second call
            mock_telethon_client.delete_messages.side_effect = [None, Exception("Delete failed")]

            with pytest.raises(SystemExit):
                await delete_from_file(MARKED_FILE, destination=TEST_SLUG)

            # Verify original file still exists (atomic behavior)
            assert Path(MARKED_FILE).exists()
            assert not list(Path(TEMP_OUTPUT).glob(DELETED_PATTERN))

        @pytest.mark.asyncio
        async def test_permission_denied_error(self, temp_dirs, mock_telethon_client):
            """Test handling of ChatAdminRequiredError"""
            urls = [f"https://t.me/channel/{MESSAGE_ID}"]
            with open(MARKED_FILE, "w") as f:
                f.write(f"{urls[0]}\n")

            # Mock delete_messages to raise ChatAdminRequiredError
            mock_telethon_client.delete_messages.side_effect = ChatAdminRequiredError("Permission denied")

            with pytest.raises(SystemExit, match="1"):
                await delete_from_file(MARKED_FILE, destination=TEST_SLUG)

            # Verify file not renamed (atomic behavior)
            assert Path(MARKED_FILE).exists()
            assert not list(Path(TEMP_OUTPUT).glob(DELETED_PATTERN))

    class TestFileOperations:
        """Tests for file operations and atomic behavior"""

        @pytest.mark.asyncio
        async def test_successful_file_rename(self, temp_dirs, mock_telethon_client):
            """Test file is properly renamed after successful deletion"""
            urls = [PUBLIC_MESSAGE_URL]
            marked_file, ts = make_marked_file()
            with open(marked_file, "w") as f:
                f.write(f"{urls[0]}\n")

            await delete_from_file(marked_file, destination=TEST_SLUG)

            # Verify original file is gone
            assert not Path(marked_file).exists()

            # Verify renamed file exists with correct pattern
            deleted_files = find_deleted_file(publish_ts=ts)
            assert len(deleted_files) == 1

            # Verify timestamp format (YYYYMMDD_HHMMSS)
            filename = deleted_files[0].name
            # Check full pattern: {publish_ts}_{slug}.deleted_at_{delete_ts}.txt
            assert re.match(rf"{ts}_{TEST_SLUG}\.deleted_at_\d{{8}}_\d{{6}}\.txt", filename)

        @pytest.mark.asyncio
        async def test_empty_input_file_handling(self, temp_dirs, mock_telethon_client):
            """Test handling of empty input files"""
            marked_file, ts = make_marked_file()
            Path(marked_file).touch()
            await delete_from_file(marked_file, destination=TEST_SLUG)
            mock_telethon_client.delete_messages.assert_not_called()
            deleted_files = find_deleted_file(publish_ts=ts)
            assert len(deleted_files) == 1

        @pytest.mark.asyncio
        async def test_file_with_empty_lines_and_whitespace(self, temp_dirs, mock_telethon_client):
            """Test handling of files with empty lines and whitespace"""
            content = """
            https://t.me/channel1/1

            https://t.me/channel2/2

            """
            with open(MARKED_FILE, "w") as f:
                f.write(content)

            await delete_from_file(MARKED_FILE, destination=TEST_SLUG)

            # Only valid URLs should be processed
            assert mock_telethon_client.delete_messages.call_count == 2

        @pytest.mark.asyncio
        async def test_file_rename_with_custom_directory_structure(self, temp_dirs, mock_telethon_client):
            """Test file is renamed in same directory as original when using subdirectories"""
            # Create subdirectory structure
            subdir = Path(TEMP_OUTPUT) / "custom" / "subdir"
            subdir.mkdir(parents=True, exist_ok=True)

            custom_marked_file = subdir / f"20250101_120000_{TEST_SLUG}.marked_for_deletion.txt"
            urls = [f"https://t.me/channel/{MESSAGE_ID}"]

            with open(custom_marked_file, "w") as f:
                f.write(f"{urls[0]}\n")

            await delete_from_file(str(custom_marked_file), destination=TEST_SLUG)

            # Verify original file is gone
            assert not custom_marked_file.exists()

            # Verify renamed file exists in same subdirectory
            deleted_files = list(subdir.glob(DELETED_PATTERN))
            assert len(deleted_files) == 1

            # Verify the renamed file is in the same subdirectory
            assert deleted_files[0].parent == subdir

    class TestIntegrationAndCLI:
        """Tests for CLI integration and command-line interface"""

        def test_cli_with_explicit_file_parameter(self, temp_dirs, mock_telethon_client):
            urls = [f"https://t.me/channel/{MESSAGE_ID}"]
            marked_file, ts = make_marked_file()
            with open(marked_file, "w") as f:
                f.write(f"{urls[0]}\n")
            runner = CliRunner()
            result = runner.invoke(cli, ['delete', '--delete-urls', marked_file, '--destination', TEST_SLUG])
            assert result.exit_code == 0
            assert "Deleting messages using file:" in result.output
            assert marked_file in result.output
            assert "Delete command finished." in result.output
            deleted_files = find_deleted_file(publish_ts=ts)
            assert len(deleted_files) == 1

        def test_cli_with_auto_detection(self, temp_dirs, mock_telethon_client):
            urls = [f"https://t.me/channel/{MESSAGE_ID}"]
            marked_file, ts = make_marked_file()
            with open(marked_file, "w") as f:
                f.write(f"{urls[0]}\n")
            runner = CliRunner()
            result = runner.invoke(cli, ['delete', '--destination', TEST_SLUG])
            assert result.exit_code == 0
            assert "Deleting messages using file: [auto-detect]" in result.output
            assert "Delete command finished." in result.output
            deleted_files = find_deleted_file(publish_ts=ts)
            assert len(deleted_files) == 1

        def test_cli_error_propagation(self, temp_dirs, mock_telethon_client):
            """Test CLI error propagation"""
            # Test with no files (should trigger FileNotFoundError)
            runner = CliRunner()
            result = runner.invoke(cli, ['delete'])

            # Should have non-zero exit code due to error
            assert result.exit_code != 0
            # Should contain error information
            assert "No .marked_for_deletion.txt file found" in result.output or "Error" in result.output

        def test_cli_delete_accepts_extra_shared_flags(self, temp_dirs, mock_telethon_client):
            """Delete should return 0 when extra shared flags are supplied."""
            urls = [f"https://t.me/channel/{MESSAGE_ID}"]
            with open(MARKED_FILE, "w") as f:
                f.write(f"{urls[0]}\n")

            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    'delete',
                    '--delete-urls', MARKED_FILE,
                    '--source', 'dummy.txt',
                    '--destination', 'dummy_dest',
                    '--sleep', '2'
                ]
            )
            assert result.exit_code == 0
            assert "Delete command finished." in result.output

        def test_cli_delete_unknown_flag_fails(self, temp_dirs, mock_telethon_client):
            """Delete should exit non-zero with an unknown flag (typo)."""
            runner = CliRunner()
            result = runner.invoke(cli, ['delete', '--notaflag'])
            assert result.exit_code != 0
            assert "Error" in result.output or "no such option" in result.output.lower()
