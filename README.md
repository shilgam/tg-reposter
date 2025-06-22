# tg-reposter

A simple Telegram bot to automatically repost messages from a source channel to a destination channel.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/tg-reposter.git
    cd tg-reposter
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Obtain Credentials:**

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
        1.  Find a bot like `@userinfobot` on Telegram.
        2.  The bot may ask you to subscribe to another channel (e.g., `t.me/ChatIDBots`) to use its service. This is a common practice for free bots. It is safe to subscribe, get the IDs, and then unsubscribe.
        3.  For the **source channel**, forward any message from that channel to `@userinfobot`. It will reply with the channel's ID.
        4.  Do the same for the **destination channel**.
        5.  **Note**: For private channels, the ID will be a negative number and might start with `-100`. The bot should handle this correctly.

4.  **Create a `.env` file:**
    Create a `.env` file in the root of the project and add your credentials:
    ```
    API_ID=...
    API_HASH=...
    SOURCE_CHANNEL_ID=...
    DESTINATION_CHANNEL_ID=...
    ```

## Usage

Run the script:
```bash
python src/main.py
```

**First-Time Run**

The first time you run the script, Telethon will need to create a session file. It will prompt you interactively in your terminal:
1.  **Enter your phone number**: Provide the phone number associated with your Telegram account (e.g., `+12223334444`).
2.  **Enter the code**: Telegram will send a login code to your Telegram app. Enter it.
3.  **Enter your password**: If you have 2-Factor Authentication enabled, enter your password.

This will create an `anon.session` file in your project directory. Subsequent runs will use this file and will not require you to log in again.

The script will fetch the latest message from the source channel and send it to the destination channel.
