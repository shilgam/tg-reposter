import pytest
from unittest.mock import AsyncMock, patch
import os

class MockMessage:
    def __init__(self, message_id, text="Test message", media=None):
        self.id = message_id
        self.text = text
        self.media = media
        self.raw_text = text
        self.message = text

class MockEntity:
    def __init__(self, id=None, username=None, title="Test Channel"):
        self.id = id
        self.username = username
        self.title = title

@pytest.fixture(autouse=True)
def mock_telethon_client():
    with patch('telethon.TelegramClient', autospec=True) as mock_client_cls:
        mock_client = mock_client_cls.return_value

        # Mock async context manager
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()

        # Mock authentication
        mock_client.is_user_authorized = AsyncMock(return_value=True)

        # Mock entity resolution methods
        mock_client.get_entity = AsyncMock()
        mock_client.get_input_entity = AsyncMock()

        # Mock message retrieval
        mock_client.get_messages = AsyncMock()

        # Mock send methods with realistic return values
        mock_client.send_message = AsyncMock()
        mock_client.send_file = AsyncMock()
        mock_client.send_media_group = AsyncMock()

        # Set up default mock behaviors
        def mock_get_entity(entity_id):
            if isinstance(entity_id, str) and entity_id.startswith('@'):
                return MockEntity(username=entity_id[1:], title=f"Channel {entity_id[1:]}")
            elif isinstance(entity_id, (int, str)) and str(entity_id).startswith('-100'):
                return MockEntity(id=int(entity_id), title="Private Channel")
            else:
                raise ValueError(f"Invalid entity: {entity_id}")

        def mock_get_messages(entity, ids=None):
            if ids is None:
                return [MockMessage(1), MockMessage(2)]
            elif isinstance(ids, list):
                return [MockMessage(msg_id) for msg_id in ids]
            else:
                return MockMessage(ids)

        def mock_send_message(entity, message):
            # Return a message with a realistic ID
            return MockMessage(12345, text=str(message))

        mock_client.get_entity.side_effect = mock_get_entity
        mock_client.get_messages.side_effect = mock_get_messages
        mock_client.send_message.side_effect = mock_send_message

        yield mock_client

@pytest.fixture
def temp_dirs():
    """Create and cleanup temporary test directories"""
    temp_input = "./temp/input"
    temp_output = "./temp/output"

    # Create directories
    os.makedirs(temp_input, exist_ok=True)
    os.makedirs(temp_output, exist_ok=True)

    yield temp_input, temp_output

    # Cleanup - only remove output files, preserve input directory
    import shutil
    if os.path.exists(temp_output):
        shutil.rmtree(temp_output, ignore_errors=True)

@pytest.fixture
def test_env():
    """Provide test environment variables"""
    return {
        "API_ID": "12345",
        "API_HASH": "testhash",
        "TEST_MODE": "1"
    }
