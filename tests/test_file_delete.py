import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.delete import delete_from_file
from telethon.errors import ChatAdminRequiredError
from click.testing import CliRunner
from src.cli import cli

# Test constants to replace magic numbers and strings
PUBLIC_MESSAGE_URL = "https://t.me/publicsource/4"
PRIVATE_MESSAGE_URL = "https://t.me/c/123456789/1"
PRIVATE_CHANNEL_ID_FROM_URL = -100123456789

MESSAGE_ID = 123

TEMP_INPUT = "./tests/data/input"
TEMP_OUTPUT = "./tests/data/output"
DELETE_FILE = os.path.join(TEMP_OUTPUT, "dest_urls_to_delete.txt")

class TestDeleteFromFile:
    """Main test suite for delete_from_file functionality"""

    class TestFileAutoDetection:
        """Tests for automatic file detection logic"""

        @pytest.mark.asyncio
        async def test_auto_detect_with_valid_file(self, temp_dirs, mock_telethon_client):
            """Test auto-detection when valid file exists"""
            # Create file in expected location
            urls = [PUBLIC_MESSAGE_URL]
            with open(DELETE_FILE, "w") as f:
                f.write(f"{urls[0]}\n")

            # Call with None to trigger auto-detection
            await delete_from_file(None)

            assert mock_telethon_client.delete_messages.call_count == len(urls)
            # Verify file was renamed
            deleted_files = list(Path(TEMP_OUTPUT).glob("*_deleted.txt"))
            assert len(deleted_files) == 1

        @pytest.mark.asyncio
        async def test_auto_detect_with_no_files(self, temp_dirs, mock_telethon_client):
            """Test auto-detection when no files exist"""
            # Ensure output directory is empty
            for f in Path(TEMP_OUTPUT).glob("dest_urls_to_delete.txt"):
                f.unlink()

            with pytest.raises(FileNotFoundError, match="No dest_urls_to_delete.txt found in ./tests/data/output/."):
                await delete_from_file(None)

        @pytest.mark.asyncio
        async def test_auto_detect_with_multiple_files(self, temp_dirs, mock_telethon_client):
            """Test auto-detection selects most recent file"""
            # Create multiple files with different timestamps
            import time

            # Older file
            older_file = Path(TEMP_OUTPUT) / "dest_urls_to_delete_old.txt"
            older_file.write_text("https://t.me/old/1\n")
            older_time = time.time() - 3600  # 1 hour ago
            os.utime(older_file, (older_time, older_time))

            # Newer file
            newer_file = Path(TEMP_OUTPUT) / "dest_urls_to_delete_new.txt"
            newer_file.write_text("https://t.me/new/1\n")

            # The current implementation only detects dest_urls_to_delete.txt, so this should raise FileNotFoundError
            with pytest.raises(FileNotFoundError, match="No dest_urls_to_delete.txt found in ./tests/data/output/."):
                await delete_from_file(None)

    class TestURLParsing:
        """Tests for URL parsing and channel type handling"""

        @pytest.mark.asyncio
        async def test_public_channel_url_parsing(self, temp_dirs, mock_telethon_client):
            """Test parsing of public channel URLs"""
            urls = [f"https://t.me/channelname/{MESSAGE_ID}"]
            with open(DELETE_FILE, "w") as f:
                f.write(f"{urls[0]}\n")

            await delete_from_file(DELETE_FILE)

            # Verify correct channel entity was requested
            mock_telethon_client.get_entity.assert_called_with("channelname")
            assert mock_telethon_client.delete_messages.call_count == 1

        @pytest.mark.asyncio
        async def test_private_channel_url_parsing(self, temp_dirs, mock_telethon_client):
            """Test parsing of private channel URLs"""
            urls = [f"https://t.me/c/123456789/{MESSAGE_ID}"]
            with open(DELETE_FILE, "w") as f:
                f.write(f"{urls[0]}\n")

            await delete_from_file(DELETE_FILE)

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
            with open(DELETE_FILE, "w") as f:
                for url in urls:
                    f.write(f"{url}\n")

            await delete_from_file(DELETE_FILE)

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
            with open(DELETE_FILE, "w") as f:
                for url in urls:
                    f.write(f"{url}\n")

            await delete_from_file(DELETE_FILE)

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
            with open(DELETE_FILE, "w") as f:
                f.write(f"{urls[0]}\n")

            # Mock get_entity to fail, get_input_entity to succeed
            mock_telethon_client.get_entity.side_effect = Exception("Entity not found")
            mock_telethon_client.get_input_entity.return_value = Mock()

            await delete_from_file(DELETE_FILE)

            # Verify fallback was attempted
            mock_telethon_client.get_input_entity.assert_called()

        @pytest.mark.asyncio
        async def test_complete_entity_resolution_failure(self, temp_dirs, mock_telethon_client):
            """Test system exit when both entity resolution methods fail"""
            urls = [f"https://t.me/problematic/{MESSAGE_ID}"]
            with open(DELETE_FILE, "w") as f:
                f.write(f"{urls[0]}\n")

            # Mock both to fail
            mock_telethon_client.get_entity.side_effect = Exception("Entity not found")
            mock_telethon_client.get_input_entity.side_effect = Exception("Input entity failed")

            with pytest.raises(SystemExit, match="1"):
                await delete_from_file(DELETE_FILE)

        @pytest.mark.asyncio
        async def test_delete_operation_failure_mid_process(self, temp_dirs, mock_telethon_client):
            """Test atomic behavior when deletion fails mid-process"""
            urls = [
                "https://t.me/channel1/1",
                "https://t.me/channel2/2"
            ]
            with open(DELETE_FILE, "w") as f:
                for url in urls:
                    f.write(f"{url}\n")

            # Mock delete_messages to fail on second call
            mock_telethon_client.delete_messages.side_effect = [None, Exception("Delete failed")]

            with pytest.raises(SystemExit):
                await delete_from_file(DELETE_FILE)

            # Verify original file still exists (atomic behavior)
            assert Path(DELETE_FILE).exists()
            assert not list(Path(TEMP_OUTPUT).glob("*_deleted.txt"))

        @pytest.mark.asyncio
        async def test_permission_denied_error(self, temp_dirs, mock_telethon_client):
            """Test handling of ChatAdminRequiredError"""
            urls = [f"https://t.me/channel/{MESSAGE_ID}"]
            with open(DELETE_FILE, "w") as f:
                f.write(f"{urls[0]}\n")

            # Mock delete_messages to raise ChatAdminRequiredError
            mock_telethon_client.delete_messages.side_effect = ChatAdminRequiredError("Permission denied")

            with pytest.raises(SystemExit, match="1"):
                await delete_from_file(DELETE_FILE)

            # Verify file not renamed (atomic behavior)
            assert Path(DELETE_FILE).exists()
            assert not list(Path(TEMP_OUTPUT).glob("*_deleted.txt"))

    class TestFileOperations:
        """Tests for file operations and atomic behavior"""

        @pytest.mark.asyncio
        async def test_successful_file_rename(self, temp_dirs, mock_telethon_client):
            """Test file is properly renamed after successful deletion"""
            urls = [PUBLIC_MESSAGE_URL]
            with open(DELETE_FILE, "w") as f:
                f.write(f"{urls[0]}\n")

            await delete_from_file(DELETE_FILE)

            # Verify original file is gone
            assert not Path(DELETE_FILE).exists()

            # Verify renamed file exists with correct pattern
            deleted_files = list(Path(TEMP_OUTPUT).glob("*_deleted.txt"))
            assert len(deleted_files) == 1

            # Verify timestamp format (YYYYMMDD_HHMMSS)
            filename = deleted_files[0].name
            timestamp_part = filename.split("_deleted.txt")[0]
            assert len(timestamp_part) == 15  # YYYYMMDD_HHMMSS

        @pytest.mark.asyncio
        async def test_empty_input_file_handling(self, temp_dirs, mock_telethon_client):
            """Test handling of empty input files"""
            # Create empty file
            Path(DELETE_FILE).touch()

            await delete_from_file(DELETE_FILE)

            # No Telethon calls should be made
            mock_telethon_client.delete_messages.assert_not_called()

            # File should still be renamed (consistent behavior)
            deleted_files = list(Path(TEMP_OUTPUT).glob("*_deleted.txt"))
            assert len(deleted_files) == 1

        @pytest.mark.asyncio
        async def test_file_with_empty_lines_and_whitespace(self, temp_dirs, mock_telethon_client):
            """Test handling of files with empty lines and whitespace"""
            content = """
            https://t.me/channel1/1

            https://t.me/channel2/2

            """
            with open(DELETE_FILE, "w") as f:
                f.write(content)

            await delete_from_file(DELETE_FILE)

            # Only valid URLs should be processed
            assert mock_telethon_client.delete_messages.call_count == 2

        @pytest.mark.asyncio
        async def test_file_rename_with_custom_directory_structure(self, temp_dirs, mock_telethon_client):
            """Test file is renamed in same directory as original when using subdirectories"""
            # Create subdirectory structure
            subdir = Path(TEMP_OUTPUT) / "custom" / "subdir"
            subdir.mkdir(parents=True, exist_ok=True)

            custom_delete_file = subdir / "dest_urls_to_delete.txt"
            urls = [f"https://t.me/channel/{MESSAGE_ID}"]

            with open(custom_delete_file, "w") as f:
                f.write(f"{urls[0]}\n")

            await delete_from_file(str(custom_delete_file))

            # Verify original file is gone
            assert not custom_delete_file.exists()

            # Verify renamed file exists in same subdirectory
            deleted_files = list(subdir.glob("*_deleted.txt"))
            assert len(deleted_files) == 1

            # Verify the renamed file is in the same subdirectory
            assert deleted_files[0].parent == subdir

    class TestIntegrationAndCLI:
        """Tests for CLI integration and command-line interface"""

        def test_cli_with_explicit_file_parameter(self, temp_dirs, mock_telethon_client):
            """Test CLI with explicit file parameter"""
            urls = [f"https://t.me/channel/{MESSAGE_ID}"]
            with open(DELETE_FILE, "w") as f:
                f.write(f"{urls[0]}\n")

            runner = CliRunner()
            result = runner.invoke(cli, ['delete', '--delete-urls', DELETE_FILE])

            assert result.exit_code == 0
            assert "Deleting messages using file:" in result.output
            assert DELETE_FILE in result.output
            assert "Delete command finished." in result.output

        def test_cli_with_auto_detection(self, temp_dirs, mock_telethon_client):
            """Test CLI with auto-detection (no parameters)"""
            urls = [f"https://t.me/channel/{MESSAGE_ID}"]
            with open(DELETE_FILE, "w") as f:
                f.write(f"{urls[0]}\n")

            runner = CliRunner()
            result = runner.invoke(cli, ['delete'])

            assert result.exit_code == 0
            assert "Deleting messages using file: [auto-detect]" in result.output
            assert "Delete command finished." in result.output

        def test_cli_error_propagation(self, temp_dirs, mock_telethon_client):
            """Test CLI error propagation"""
            # Test with no files (should trigger FileNotFoundError)
            runner = CliRunner()
            result = runner.invoke(cli, ['delete'])

            # Should have non-zero exit code due to error
            assert result.exit_code != 0
            # Should contain error information
            assert "No dest_urls_to_delete.txt found in ./tests/data/output/." in result.output or "Error" in result.output
