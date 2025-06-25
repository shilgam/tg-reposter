import os
import pytest
from pathlib import Path
import subprocess

def test_private_source_to_private_dest(tmp_path, mock_telethon_client):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    source_urls = input_dir / "source_urls.txt"
    source_urls.write_text("https://t.me/c/123456789/1\n")
    dest = "2763892937"  # Example private channel ID
    env = os.environ.copy()
    env["INPUT_DIR"] = str(input_dir)
    env["OUTPUT_DIR"] = str(output_dir)
    result = subprocess.run([
        "python", "-m", "src.main", "repost",
        "--source", str(source_urls),
        "--destination", dest
    ], env=env, capture_output=True)
    assert result.returncode == 0, result.stderr.decode()
    assert mock_telethon_client.send_message.called
    # dest_urls = output_dir / "new_dest_urls.txt"
    # assert dest_urls.exists()

def test_private_source_to_public_dest(tmp_path, mock_telethon_client):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    source_urls = input_dir / "source_urls.txt"
    source_urls.write_text("https://t.me/c/123456789/2\n")
    dest = "@antalia_sales"  # Example public channel username
    env = os.environ.copy()
    env["INPUT_DIR"] = str(input_dir)
    env["OUTPUT_DIR"] = str(output_dir)
    result = subprocess.run([
        "python", "-m", "src.main", "repost",
        "--source", str(source_urls),
        "--destination", dest
    ], env=env, capture_output=True)
    assert result.returncode == 0, result.stderr.decode()
    assert mock_telethon_client.send_message.called
    # dest_urls = output_dir / "new_dest_urls.txt"
    # assert dest_urls.exists()

def test_public_source_to_private_dest(tmp_path, mock_telethon_client):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    source_urls = input_dir / "source_urls.txt"
    source_urls.write_text("https://t.me/publicsource/3\n")
    dest = "2763892937"  # Example private channel ID
    env = os.environ.copy()
    env["INPUT_DIR"] = str(input_dir)
    env["OUTPUT_DIR"] = str(output_dir)
    result = subprocess.run([
        "python", "-m", "src.main", "repost",
        "--source", str(source_urls),
        "--destination", dest
    ], env=env, capture_output=True)
    assert result.returncode == 0, result.stderr.decode()
    assert mock_telethon_client.send_message.called
    # dest_urls = output_dir / "new_dest_urls.txt"
    # assert dest_urls.exists()

def test_public_source_to_public_dest(tmp_path, mock_telethon_client):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    source_urls = input_dir / "source_urls.txt"
    source_urls.write_text("https://t.me/publicsource/4\n")
    dest = "@antalia_sales"  # Example public channel username
    env = os.environ.copy()
    env["INPUT_DIR"] = str(input_dir)
    env["OUTPUT_DIR"] = str(output_dir)
    result = subprocess.run([
        "python", "-m", "src.main", "repost",
        "--source", str(source_urls),
        "--destination", dest
    ], env=env, capture_output=True)
    assert result.returncode == 0, result.stderr.decode()
    assert mock_telethon_client.send_message.called
    # dest_urls = output_dir / "new_dest_urls.txt"
    # assert dest_urls.exists()

def test_invalid_input_fails_gracefully(tmp_path, mock_telethon_client):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    source_urls = input_dir / "source_urls.txt"
    source_urls.write_text("not_a_valid_url\n")
    dest = "@antalia_sales"
    env = os.environ.copy()
    env["INPUT_DIR"] = str(input_dir)
    env["OUTPUT_DIR"] = str(output_dir)
    result = subprocess.run([
        "python", "-m", "src.main", "repost",
        "--source", str(source_urls),
        "--destination", dest
    ], env=env, capture_output=True)
    assert result.returncode != 0
    assert b"error" in result.stderr.lower() or b"invalid" in result.stderr.lower()
    # Optionally, assert Telethon was not called
    # assert not mock_telethon_client.send_message.called