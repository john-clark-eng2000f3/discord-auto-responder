# discord-auto-responder

A lightweight, zero-framework Discord auto-responder. It connects directly to the Discord Gateway using raw websockets and replies to messages using simple regex patterns defined in a text file. Built because I wanted something low-memory and dependency-light that doesn't drag in the entire discord.py ecosystem just to run a few matching rules.

## Installation

Clone the repository and install the dependencies:

```cmd
pip install -r requirements.txt
```

## Setup

1. Get a Discord bot token from the Discord Developer Portal.
2. Ensure the **Message Content Intent** is enabled for your bot under the Bot settings tab.
3. Invite the bot to your server.
4. Create a `rules.txt` file in the same folder. Each line should contain a trigger pattern and a response, separated by ` -> `:

```text
# Simple text match
hello -> Hey there!

# Regex pattern matching
(ping|pong) -> pong!

# Match help requests
!help -> You can find docs here: https://example.com/docs
```

## Running

Run the responder from the command line, providing your bot token:

```cmd
python responder.py --token YOUR_BOT_TOKEN_HERE --rules rules.txt
```

You can exit anytime with `Ctrl+C`.

<!-- verified: 2026-09-24 -->
