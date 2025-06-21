# Telegram Message Copier – Project Context

> **Quick Summary:**
> Copy messages from a private Telegram channel to a public one _as brand-new posts_, using Python + Telethon.

## 1. Purpose
This repository contains a CLI tool that mirrors content from one Telegram channel to another while stripping all original-sender metadata. It solves the “manual repost” problem for channel admins who need clean, attribution-free copies.

## 2. Core Capabilities
- Repost text, captions, and media (single images & albums).
- Preserve Markdown/HTML formatting.
- Never forward; always send as new `send_*` messages.
- Optional deletion of destination messages via input list.
- Adjustable delay between sends.

## 3. Inputs & Outputs

- **Input Files**
    - `source_urls.txt`: One URL per line from the private channel.
    - `dest_urls_to_delete.txt` (Optional): URLs in the public channel to delete.

- **Output File**
    - `new_dest_urls.txt`: Contains URLs of the successfully reposted messages.

## 4. Tech Stack
- Python ≥ 3.10
- [Telethon](https://github.com/LonamiWebs/Telethon) for Telegram RPC
- Click CLI + Makefile wrappers (cross-platform; tested on macOS)

## 5. Security / Privacy
- Session file (`*.session`) created on first login – **git-ignored**.
- No tokens or phone numbers hard-coded in source.

## 6. Out of Scope
- Telegram Bot API (user sessions only).
- Real-time sync/daemon mode.
- GUI or web dashboard.

## 7. Available Commands:
```bash
make login        # one-time user auth
make repost SRC=source_urls.txt
make delete LIST=dest_urls_to_delete.txt
make sync SRC=source_urls.txt DEL=dest_urls_to_delete.txt
```
