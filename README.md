# JazzBot

A Discord music bot built with Python that responds exclusively to slash commands and plays music in Discord voice channels. JazzBot focuses on reliability, clarity of user feedback, and high-quality audio playback from multiple sources.

## Features

- 🎵 **Slash Commands Only** - Modern Discord interaction system
- 🎨 **Rich Embeds** - Beautiful, consistent visual responses
- 🎧 **Multi-Source Support** - YouTube and Spotify (metadata resolution)
- 🔄 **Queue Management** - Per-guild independent queues
- ✅ **Smart Validation** - Voice channel and permission checks
- 🎹 **High-Quality Audio** - Powered by Lavalink and Wavelink

## Commands

- `/play <query>` - Plays a song immediately or starts playback if idle
- `/queue <query>` - Adds a song to the queue (behaves like /play if queue is empty)
- `/pause` - Pauses the currently playing track
- `/unpause` - Resumes paused playback
- `/skip` - Skips the currently playing track
- `/jump <songIndex>` - Jumps to a specific position in the queue
- `/shuffle` - Randomizes the order of the remaining queue
- `/quit` - Stops playback, clears the queue, and disconnects

## Prerequisites

- Python 3.10 or higher
- A Discord Bot Token ([Discord Developer Portal](https://discord.com/developers/applications))
- A Lavalink server (self-hosted or managed)
- (Optional) Spotify API credentials for metadata resolution

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv
```

3. **Activate the virtual environment**:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. **Install dependencies**:
```bash
pip install -r requirements.txt
```

5. **Set up environment variables**:
   - Copy `.env.example` to `.env`
   - Fill in your Discord bot token and Lavalink configuration
   - Optionally add Spotify API credentials

6. **Set up Lavalink**:
   - Download Lavalink from [Lavalink Releases](https://github.com/lavalink-devs/Lavalink/releases)
   - Run Lavalink with your configured password
   - Default configuration: `localhost:2333` with password `youshallnotpass`

## Running the Bot

```bash
python -m src.jazzbot.bot
```

Or if you prefer:

```bash
python src/jazzbot/bot.py
```

## Configuration

### Environment Variables

- `DISCORD_TOKEN` - Your Discord bot token (required)
- `LAVALINK_HOST` - Lavalink server hostname (default: localhost)
- `LAVALINK_PORT` - Lavalink server port (default: 2333)
- `LAVALINK_PASSWORD` - Lavalink server password (default: youshallnotpass)
- `SPOTIFY_CLIENT_ID` - Spotify API client ID (optional)
- `SPOTIFY_CLIENT_SECRET` - Spotify API client secret (optional)

### Discord Bot Permissions

Your bot needs the following permissions:
- View Channels
- Connect
- Speak
- Send Messages
- Embed Links
- Use Application Commands

## Project Structure

```
JazzBot/
├── src/
│   └── jazzbot/
│       ├── __init__.py
│       ├── bot.py           # Main bot file
│       ├── commands.py      # Slash command implementations
│       ├── config.py        # Configuration management
│       ├── embeds.py        # Embed utilities
│       ├── queue.py         # Queue management
│       ├── spotify.py       # Spotify metadata resolution
│       └── voice.py         # Voice channel validation
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## How It Works

1. **Voice Channel Validation**: Before playing music, JazzBot validates that:
   - The user is in a voice channel
   - The bot can see, join, and speak in that channel
   - The bot is either not connected or in the same channel

2. **Queue Management**: Each Discord server (guild) maintains an independent queue that persists until `/quit` is called or the bot disconnects.

3. **Music Sources**: 
   - YouTube URLs and searches are handled directly
   - Spotify URLs are resolved to metadata, then searched on YouTube for playback

4. **Error Handling**: All errors are presented as user-friendly embeds with consistent styling.

## Troubleshooting

### Bot doesn't respond to commands
- Ensure the bot has "Use Application Commands" permission
- Check that commands have been synced (check bot logs)
- Verify the bot is online and connected

### Cannot connect to voice channel
- Check bot permissions (Connect, Speak)
- Ensure the bot can see the voice channel
- Verify the user is in a voice channel

### Lavalink connection fails
- Verify Lavalink is running
- Check host, port, and password configuration
- Ensure firewall allows the connection

### Spotify links don't work
- Spotify API credentials are optional
- Without credentials, Spotify links will be treated as regular searches
- Add credentials to `.env` for proper metadata resolution

## Development

This project follows clean code principles:
- Type hints throughout
- Comprehensive error handling
- Modular architecture
- Consistent code style

## License

This project is provided as-is for educational and personal use.

## Support

For issues or questions, please refer to the PRD document or check the code comments for implementation details.

