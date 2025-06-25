import os
import shutil
import pytest
import subprocess

TEMP_INPUT = "./temp/input"
TEMP_OUTPUT = "./temp/output"
SOURCE_FILE = os.path.join(TEMP_INPUT, "source_urls.txt")
DEST_FILE = os.path.join(TEMP_OUTPUT, "new_dest_urls.txt")


def setup_temp_dirs():
    os.makedirs(TEMP_INPUT, exist_ok=True)
    os.makedirs(TEMP_OUTPUT, exist_ok=True)

def cleanup_temp_dirs():
    shutil.rmtree("./temp", ignore_errors=True)

def test_private_source_to_private_dest(mock_telethon_client):
    cleanup_temp_dirs()
    setup_temp_dirs()
    with open(SOURCE_FILE, "w") as f:
        f.write("https://t.me/c/123456789/1\n")
    dest = "2763892937"  # Example private channel ID
    env = os.environ.copy()
    env["API_ID"] = "12345"
    env["API_HASH"] = "testhash"
    result = subprocess.run([
        "python", "-m", "src.main", "repost",
        "--destination", dest
    ], capture_output=True, env=env)
    assert result.returncode == 0, result.stderr.decode()
    # assert mock_telethon_client.send_message.called
    # assert os.path.exists(DEST_FILE)
    cleanup_temp_dirs()

def test_private_source_to_public_dest(mock_telethon_client):
    cleanup_temp_dirs()
    setup_temp_dirs()
    with open(SOURCE_FILE, "w") as f:
        f.write("https://t.me/c/123456789/2\n")
    dest = "@antalia_sales"  # Example public channel username
    env = os.environ.copy()
    env["API_ID"] = "12345"
    env["API_HASH"] = "testhash"
    result = subprocess.run([
        "python", "-m", "src.main", "repost",
        "--destination", dest
    ], capture_output=True, env=env)
    assert result.returncode == 0, result.stderr.decode()
    # assert mock_telethon_client.send_message.called
    # assert os.path.exists(DEST_FILE)
    cleanup_temp_dirs()

def test_public_source_to_private_dest(mock_telethon_client):
    cleanup_temp_dirs()
    setup_temp_dirs()
    with open(SOURCE_FILE, "w") as f:
        f.write("https://t.me/publicsource/3\n")
    dest = "2763892937"  # Example private channel ID
    env = os.environ.copy()
    env["API_ID"] = "12345"
    env["API_HASH"] = "testhash"
    result = subprocess.run([
        "python", "-m", "src.main", "repost",
        "--destination", dest
    ], capture_output=True, env=env)
    assert result.returncode == 0, result.stderr.decode()
    # assert mock_telethon_client.send_message.called
    # assert os.path.exists(DEST_FILE)
    cleanup_temp_dirs()

def test_public_source_to_public_dest(mock_telethon_client):
    cleanup_temp_dirs()
    setup_temp_dirs()
    with open(SOURCE_FILE, "w") as f:
        f.write("https://t.me/publicsource/4\n")
    dest = "@antalia_sales"  # Example public channel username
    env = os.environ.copy()
    env["API_ID"] = "12345"
    env["API_HASH"] = "testhash"
    result = subprocess.run([
        "python", "-m", "src.main", "repost",
        "--destination", dest
    ], capture_output=True, env=env)
    assert result.returncode == 0, result.stderr.decode()
    # assert mock_telethon_client.send_message.called
    # assert os.path.exists(DEST_FILE)
    cleanup_temp_dirs()

def test_invalid_input_fails_gracefully(mock_telethon_client):
    cleanup_temp_dirs()
    setup_temp_dirs()
    with open(SOURCE_FILE, "w") as f:
        f.write("not_a_valid_url\n")
    dest = "@antalia_sales"
    env = os.environ.copy()
    env["API_ID"] = "12345"
    env["API_HASH"] = "testhash"
    result = subprocess.run([
        "python", "-m", "src.main", "repost",
        "--destination", dest
    ], capture_output=True, env=env)
    assert result.returncode != 0
    assert b"error" in result.stderr.lower() or b"invalid" in result.stderr.lower()
    # assert not mock_telethon_client.send_message.called
    cleanup_temp_dirs()