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
    SOURCE_CHANNEL_ID=...
    DESTINATION_CHANNEL_ID=...
    SOURCE_MESSAGE_ID=... # Optional: for a specific message
    ```

4.  **Log in to create a session file:**
    Run the following command. You will be prompted for your phone number, password, and a 2FA code. This creates the `anon.session` file needed to run commands.
    ```bash
    make login
    ```

---

## Usage

All commands are run via `make` and executed within a Docker container to ensure a consistent environment.

### File-based Reposting Workflow

To repost multiple messages, use the new file-based workflow:

**Before you start:**
- Run `make setup` to create the required temp directories.

1. **Prepare your source URLs file:**
   - Create a file at `./temp/input/source_urls.txt` (one message URL per line).
   - Each line should be a full Telegram message URL, e.g.:
     ```
     https://t.me/source_channel/12345
     https://t.me/source_channel/12346
     ```

2. **Run the repost command:**
   - Use the Makefile target and specify your destination channel:
     ```bash
     make repost ARGS="--destination=<destination_channel>"
     ```
   - Example:
     ```bash
     make repost ARGS="--destination=my_dest_channel"
     ```

3. **Check the output:**
   - After completion, new message URLs will be written to:
     `./temp/output/new_dest_urls.txt`
   - Each line corresponds to a reposted message in the destination channel.

### Other Commands

*   `make delete ARGS="..."`: Deletes messages. (Not yet implemented)