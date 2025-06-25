import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture(autouse=True)
def mock_telethon_client():
    with patch('telethon.TelegramClient', autospec=True) as mock_client_cls:
        mock_client = mock_client_cls.return_value
        # Mock async context manager
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        # Mock send methods
        mock_client.send_message = AsyncMock()
        mock_client.send_file = AsyncMock()
        mock_client.send_media_group = AsyncMock()
        yield mock_client