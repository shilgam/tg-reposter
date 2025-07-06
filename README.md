# tg-reposter

A simple Telegram automation script to automatically repost messages from a source channel to a destination channel using your user account.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/tg-reposter.git
    cd tg-reposter
    ```

2.  **Obtain Credentials:**
    *   **API_ID and API_HASH**:
        1.  Go to [my.telegram.org](https://my.telegram.org) and log in.
        2.  Click on "API development tools".
        3.  You will be prompted to create a new application. Fill in the form as follows:
            - **App title**: `tg-reposter`
            - **Short name**: `tg_reposter` (or any other unique name)
            - **URL**: (can be left blank)
            - **Platform**: Select `Desktop`
            - **Description**: (can be left blank)
        4.  After creating the app, you will find your `API_ID` and `API_HASH` on the next page.
    *   **Channel IDs**:
        1.  In Telegram, find a bot like `@userinfobot`.
        2.  To get the ID of a channel, you must **forward a message** from that channel to the bot.
            - **Important**: Do NOT send a link to the channel or type the channel name. You must use Telegram's "Forward" functionality.
            - Go into your source channel.
            - Tap and hold (or right-click) on any message.
            - Select "Forward".
            - Choose `@userinfobot` as the recipient.
        3.  The bot will reply with the correct Channel ID. It will likely be a negative number (e.g., `-100123456789`).
        4.  Repeat the forwarding process for your destination channel.

    *   **Finding a Specific Message ID (Optional)**:
        By default, the script reposts the latest message. To repost a specific message, you need its ID.
        1.  Go to the source channel/group and find the message.
        2.  **Right-click** on it and select **Copy Message Link**.
        3.  The link will look like `https://t.me/channel_name/12345`. The number at the end (`12345`) is the message ID.
        4.  Add this to your `.env` file as `SOURCE_MESSAGE_ID`.

3.  **Create a `.env` file:**
    Create a `.env` file in the root of the project and add your credentials.
    ```
    API_ID=...
    API_HASH=...
    ```

4.  **Log in to create a session file:**
    Run the following command. You will be prompted for your phone number, password, and a 2FA code. This creates the `anon.session` file needed to run commands.
    ```bash
    make login
    ```

---

## Usage

All commands are run via `make` and executed within a Docker container to ensure a consistent environment.

**Before you start:**
- Run `make setup` to create the required data directories.
- Run `make login` to create your Telegram session file.

### Human-in-the-loop Workflow (timestamped files)

1. `make repost ARGS="--destination=<channel>"`
   – writes a file named `YYYYMMDD_HHMMSS_{slug}.txt` in `./data/output/`.
   – if a previous un-tagged run exists for the same destination it is renamed to
     `…_{slug}.marked_for_deletion.txt`.
2. `make delete ARGS="--destination=<channel>"`
   – auto-detects the latest `…_{slug}.marked_for_deletion.txt`, deletes those
     messages, then renames that file to
     `…_{slug}.deleted_at_YYYYMMDD_HHMMSS.txt`.

> You can still supply `--delete-urls=<file>` to override auto-detection.

### Fully Automatic Workflow

A single `make sync ARGS="--destination=<channel> --source=<file>"` runs **repost** then **delete** sequentially, aborting on any error.

> **Note:** The sync command is now implemented. It accepts the same flags as repost and delete, and will abort on any error. The delete command silently ignores extra shared flags, so you can use unified ARGS for all commands.

## Command Reference

### `make repost`

Reposts messages from a source file to a destination channel.

**Usage:**
```bash
make repost ARGS="--sleep=2 --destination=<destination_channel>"
# Or, to use a custom input file:
make repost ARGS="--sleep=2 --source=./path/to/your_input.txt --destination=<destination_channel>"
# For faster testing (no delay between messages):
make repost ARGS="--sleep=0 --destination=<destination_channel>"
```

**How it works:**
1. Reads URLs from `./data/input/source_urls.txt` (or a custom `--source`).
2. Writes destination URLs to `YYYYMMDD_HHMMSS_{slug}.txt` using an atomic
   temp-file move for safety.
3. If an older un-tagged run exists it is renamed to
   `…_{slug}.marked_for_deletion.txt` so the next `make delete` will pick it up.
4. Stops immediately on first error.

### `make delete`

Deletes messages from a destination channel based on a list of URLs.

**Usage:**
```bash
make delete
# Or, to use a custom delete file:
make delete ARGS="--delete-urls=./path/to/your_delete_list.txt"
```

**How it works:**
1. If `--delete-urls` is omitted the command derives the slug from
   `--destination` and selects the most-recent
   `…_{slug}.marked_for_deletion.txt`.
2. Deletes each message listed in that file.
3. On success, renames the file to `…_{slug}.deleted_at_YYYYMMDD_HHMMSS.txt`.
4. Stops immediately on any error (atomic behaviour).

### `make sync`

Runs repost then delete operations sequentially, aborting on any error.

**Usage:**
```bash
make sync ARGS="--source=./data/input/_source_private.txt \
                --destination=2763892937 \
                --sleep=2
```

- Accepts the same flags as repost and delete.
- If repost succeeds, delete is run automatically.
- If any step fails, sync aborts and exits non-zero.

### `make delete`

**Note:** The delete command still accepts extra shared flags (`--source`, `--sleep`) and silently ignores them, enabling a single ARGS string for `make repost`, `make delete`, and `make sync` alike.
