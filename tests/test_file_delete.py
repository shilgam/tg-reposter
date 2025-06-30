import os
import shutil
import pytest
from pathlib import Path
from src.delete import delete_from_file

TEMP_INPUT = "./tests/data/input"
TEMP_OUTPUT = "./tests/data/output"
DELETE_FILE = os.path.join(TEMP_OUTPUT, "dest_urls_to_delete.txt")

@pytest.mark.asyncio
class TestDeleteFromFile:
    async def test_successful_deletion(self, temp_dirs, mock_telethon_client):
        # Prepare a file with valid Telegram message URLs
        urls = [
            "https://t.me/publicsource/4",
            "https://t.me/c/123456789/1"
        ]
        with open(DELETE_FILE, "w") as f:
            for url in urls:
                f.write(f"{url}\n")
        # Call the delete function
        delete_from_file(DELETE_FILE)
        # Check that delete_messages was called for each message
        assert mock_telethon_client.delete_messages.call_count == len(urls)
        # Check that the file was renamed to *_deleted.txt
        deleted_files = list(Path(TEMP_OUTPUT).glob("*_deleted.txt"))
        assert len(deleted_files) == 1
        # Clean up
        for f in deleted_files:
            os.remove(f) 
