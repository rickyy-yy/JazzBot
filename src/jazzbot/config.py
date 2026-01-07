"""Configuration management for JazzBot."""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Bot configuration loaded from environment variables."""

    # Discord Bot Token
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")

    # Lavalink Configuration
    LAVALINK_HOST: str = os.getenv("LAVALINK_HOST", "localhost")
    LAVALINK_PORT: int = int(os.getenv("LAVALINK_PORT", "2333"))
    LAVALINK_PASSWORD: str = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

    # Spotify API (optional, for metadata)
    SPOTIFY_CLIENT_ID: Optional[str] = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET: Optional[str] = os.getenv("SPOTIFY_CLIENT_SECRET")

    # Embed Colors
    PRIMARY_COLOR: int = 0x738678
    SUCCESS_COLOR: int = 0x4A7C59  # Muted Green
    WARNING_COLOR: int = 0xD4A574  # Soft Amber
    ERROR_COLOR: int = 0x8B6F6F  # Muted Red
    INFO_COLOR: int = 0x6B7280  # Neutral Slate

    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        return True

