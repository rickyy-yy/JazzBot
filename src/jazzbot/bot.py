"""Main bot file for JazzBot."""

import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
import wavelink

# PyNaCl is required for voice support in discord.py
try:
    import nacl
except ImportError:
    raise ImportError(
        "PyNaCl is required for voice support. Install it with: pip install PyNaCl"
    )

from .config import Config
from .embeds import error_embed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class JazzBot(commands.Bot):
    """Main bot class for JazzBot."""

    def __init__(self) -> None:
        """Initialize the bot."""
        intents = discord.Intents.default()
        intents.message_content = False  # No message content needed
        intents.voice_states = True

        super().__init__(
            command_prefix="!",  # Not used, but required by commands.Bot
            intents=intents,
            help_command=None,  # Disable default help command
        )

        self.initial_extensions = ["src.jazzbot.commands"]

    async def setup_hook(self) -> None:
        """Setup hook called when bot is starting."""
        # Load extensions
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")

        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_ready(self) -> None:
        """Called when bot is ready."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")  # type: ignore
        logger.info(f"Connected to {len(self.guilds)} guild(s)")

        # Connect to Lavalink
        await self.connect_lavalink()

    async def connect_lavalink(self) -> None:
        """Connect to Lavalink server."""
        try:
            nodes = [
                wavelink.Node(
                    uri=f"https://{Config.LAVALINK_HOST}:{Config.LAVALINK_PORT}",
                    password=Config.LAVALINK_PASSWORD,
                )
            ]
            await wavelink.Pool.connect(nodes=nodes, client=self)
            logger.info("Connected to Lavalink server")
        except Exception as e:
            logger.error(f"Failed to connect to Lavalink: {e}")

    async def on_wavelink_node_ready(
        self, payload: wavelink.NodeReadyEventPayload
    ) -> None:
        """Called when a Lavalink node is ready."""
        logger.info(f"Lavalink node ready: {payload.node.identifier}")

    async def on_wavelink_track_exception(
        self, payload: wavelink.TrackExceptionEventPayload
    ) -> None:
        """Handle track exception events."""
        logger.error(f"Track exception: {payload.exception}")

    async def on_wavelink_track_stuck(
        self, payload: wavelink.TrackStuckEventPayload
    ) -> None:
        """Handle track stuck events."""
        logger.warning(f"Track stuck: {payload.threshold}ms")

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors

        logger.error(f"Command error: {error}", exc_info=error)

    async def on_interaction_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Handle interaction errors."""
        logger.error(f"Interaction error: {error}", exc_info=error)

        if interaction.response.is_done():
            await interaction.followup.send(
                embed=error_embed(
                    "An Error Occurred",
                    "Something went wrong while processing your command.",
                )
            )
        else:
            await interaction.response.send_message(
                embed=error_embed(
                    "An Error Occurred",
                    "Something went wrong while processing your command.",
                )
            )


async def main() -> None:
    """Main entry point for the bot."""
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return

    # Create and run bot
    bot = JazzBot()
    await bot.start(Config.DISCORD_TOKEN)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

