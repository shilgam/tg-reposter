import os
import pytest
from unittest.mock import patch, AsyncMock
from src.reposter import get_sleep_interval, repost_from_file

# Test constants to replace magic numbers and strings
PUBLIC_CHANNEL = "@dummy_channel991"


class TestSleepIntervalUtility:
    """Test the sleep interval utility function"""

    def test_cli_value_takes_priority(self):
        """Test that CLI value takes priority over environment and default"""
        with patch.dict(os.environ, {"REPOST_SLEEP_INTERVAL": "5.0"}):
            result = get_sleep_interval(2.5)
            assert result == 2.5

    def test_environment_variable_used_when_no_cli(self):
        """Test that environment variable is used when CLI value is None"""
        with patch.dict(os.environ, {"REPOST_SLEEP_INTERVAL": "3.0"}):
            result = get_sleep_interval(None)
            assert result == 3.0

    def test_default_value_when_no_cli_or_env(self):
        """Test that default value (0.1) is used when no CLI or env value"""
        with patch.dict(os.environ, {}, clear=True):
            result = get_sleep_interval(None)
            assert result == 0.1

    def test_invalid_environment_variable_falls_back_to_default(self):
        """Test that invalid environment variable falls back to default"""
        with patch.dict(os.environ, {"REPOST_SLEEP_INTERVAL": "invalid"}):
            result = get_sleep_interval(None)
            assert result == 0.1

    def test_zero_cli_value_is_respected(self):
        """Test that zero CLI value is respected (for tests)"""
        result = get_sleep_interval(0.0)
        assert result == 0.0

    def test_negative_values_not_validated_in_utility(self):
        """Test that negative values are not validated in utility function (validation is in CLI)"""
        result = get_sleep_interval(-1.0)
        assert result == -1.0


@pytest.mark.asyncio
class TestSleepIntervalIntegration:
    """Test sleep interval integration in repost_from_file function"""

    async def test_sleep_called_between_messages(self, temp_dirs, mock_telethon_client, mock_asyncio_sleep):
        """Test that sleep is called between messages but not after the last one"""
        # Create test input with 3 URLs
        temp_input, temp_output = temp_dirs
        source_file = os.path.join(temp_input, "source_urls.txt")
        with open(source_file, "w") as f:
            f.write("https://t.me/test/1\n")
            f.write("https://t.me/test/2\n")
            f.write("https://t.me/test/3\n")

        # Call repost with custom sleep interval
        await repost_from_file(PUBLIC_CHANNEL, source_file, sleep_interval=1.5)

        # Verify sleep was called exactly 2 times (between 3 messages)
        assert mock_asyncio_sleep.call_count == 2
        # Verify sleep was called with correct interval
        for call in mock_asyncio_sleep.call_args_list:
            assert call[0][0] == 1.5

    async def test_no_sleep_for_single_message(self, temp_dirs, mock_telethon_client, mock_asyncio_sleep):
        """Test that no sleep is called for single message"""
        temp_input, temp_output = temp_dirs
        source_file = os.path.join(temp_input, "source_urls.txt")
        with open(source_file, "w") as f:
            f.write("https://t.me/test/1\n")

        await repost_from_file(PUBLIC_CHANNEL, source_file, sleep_interval=1.0)

        # No sleep should be called for single message
        assert mock_asyncio_sleep.call_count == 0

    async def test_environment_variable_override_in_integration(self, temp_dirs, mock_telethon_client, mock_asyncio_sleep):
        """Test that environment variable is used when no CLI sleep provided"""
        temp_input, temp_output = temp_dirs
        source_file = os.path.join(temp_input, "source_urls.txt")
        with open(source_file, "w") as f:
            f.write("https://t.me/test/1\n")
            f.write("https://t.me/test/2\n")

        with patch.dict(os.environ, {"REPOST_SLEEP_INTERVAL": "2.5"}):
            await repost_from_file(PUBLIC_CHANNEL, source_file, sleep_interval=None)

        # Verify sleep was called with environment variable value
        assert mock_asyncio_sleep.call_count == 1
        assert mock_asyncio_sleep.call_args[0][0] == 2.5

    async def test_default_sleep_interval_used(self, temp_dirs, mock_telethon_client, mock_asyncio_sleep):
        """Test that default sleep interval (0.1) is used when no CLI or env value"""
        temp_input, temp_output = temp_dirs
        source_file = os.path.join(temp_input, "source_urls.txt")
        with open(source_file, "w") as f:
            f.write("https://t.me/test/1\n")
            f.write("https://t.me/test/2\n")

        with patch.dict(os.environ, {}, clear=True):
            await repost_from_file(PUBLIC_CHANNEL, source_file, sleep_interval=None)

        # Verify sleep was called with default value
        assert mock_asyncio_sleep.call_count == 1
        assert mock_asyncio_sleep.call_args[0][0] == 0.1

    async def test_zero_sleep_interval_for_tests(self, temp_dirs, mock_telethon_client, mock_asyncio_sleep):
        """Test that zero sleep interval works (for test environments)"""
        temp_input, temp_output = temp_dirs
        source_file = os.path.join(temp_input, "source_urls.txt")
        with open(source_file, "w") as f:
            f.write("https://t.me/test/1\n")
            f.write("https://t.me/test/2\n")

        await repost_from_file(PUBLIC_CHANNEL, source_file, sleep_interval=0.0)

        # Verify sleep was called with zero value
        assert mock_asyncio_sleep.call_count == 1
        assert mock_asyncio_sleep.call_args[0][0] == 0.0
