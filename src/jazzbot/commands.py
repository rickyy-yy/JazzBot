"""Slash command implementations for JazzBot."""

import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import wavelink

from .config import Config
from .embeds import (
    create_embed,
    error_embed,
    info_embed,
    success_embed,
    warning_embed,
)
from .queue import MusicQueue, QueueEntry
from .spotify import SpotifyResolver
from .voice import ensure_bot_voice_state, validate_voice_context


class QueuePaginationView(View):
    """View for paginating through the queue."""

    def __init__(self, cog: "MusicCommands", queue: MusicQueue, guild_id: int, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.queue = queue
        self.guild_id = guild_id
        self.current_page = 0
        self.items_per_page = 10

    def update_buttons(self) -> None:
        """Update button states based on current page."""
        total_items = len(self.queue.queue)
        total_pages = (total_items + self.items_per_page - 1) // self.items_per_page if total_items > 0 else 1

        # Enable/disable buttons based on page position
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= total_pages - 1

    async def update_message(self, interaction: discord.Interaction) -> None:
        """Update the message with current page."""
        embed = self.cog.create_queue_embed(self.queue, self.current_page, self.items_per_page)
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: Button) -> None:
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: Button) -> None:
        """Go to next page."""
        total_items = len(self.queue.queue)
        total_pages = (total_items + self.items_per_page - 1) // self.items_per_page if total_items > 0 else 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            await self.update_message(interaction)

    async def on_timeout(self) -> None:
        """Handle view timeout by disabling buttons."""
        for item in self.children:
            item.disabled = True


class MusicCommands(commands.Cog):
    """Music command handlers for JazzBot."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the music commands cog."""
        self.bot = bot
        self.queues: dict[int, MusicQueue] = {}  # guild_id -> queue
        self.spotify_resolver = SpotifyResolver(
            Config.SPOTIFY_CLIENT_ID, Config.SPOTIFY_CLIENT_SECRET
        )

    def get_queue(self, guild_id: int) -> MusicQueue:
        """Get or create a queue for a guild."""
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]

    def format_duration(self, seconds: int) -> str:
        """Format duration in seconds to MM:SS or HH:MM:SS."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def create_queue_embed(
        self, queue: MusicQueue, page: int = 0, items_per_page: int = 10
    ) -> discord.Embed:
        """
        Create an embed displaying the queue with pagination.

        Args:
            queue: The music queue
            page: Current page number (0-based)
            items_per_page: Number of items per page

        Returns:
            Discord embed with queue information
        """
        total_items = len(queue.queue)
        total_pages = (total_items + items_per_page - 1) // items_per_page if total_items > 0 else 1

        if total_items == 0:
            return info_embed("Queue", "The queue is empty.")

        # Calculate pagination
        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        page_items = queue.queue[start_idx:end_idx]

        # Build description
        description_parts = []
        for idx, entry in enumerate(page_items, start=start_idx + 1):
            duration_str = self.format_duration(entry.duration)
            requester_name = entry.requester.display_name if entry.requester else "Unknown"
            
            # Mark current track
            marker = "▶️" if idx - 1 == queue.current_index else f"{idx}."
            description_parts.append(
                f"{marker} **{entry.title}**\n"
                f"   └ Duration: {duration_str} | Source: {entry.source} | Requested by: {requester_name}"
            )

        description = "\n\n".join(description_parts)
        
        embed = info_embed(
            "Music Queue",
            description
        )
        embed.set_footer(text=f"Page {page + 1} of {total_pages} | Total: {total_items} track(s)")

        return embed

    async def search_track(self, query: str) -> Optional[wavelink.Playable]:
        """
        Search for a track using Wavelink.

        Args:
            query: Search query or URL

        Returns:
            Wavelink Playable object or None
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Check if it's a Spotify URL
            if self.spotify_resolver.is_spotify_url(query):
                # Resolve Spotify to searchable query
                resolved = self.spotify_resolver.resolve_track(query)
                if resolved:
                    query = resolved
                # If playlist, handle differently
                if "playlist" in query.lower():
                    # For now, just use the first track
                    # Full playlist support can be added later
                    pass

            # Check if query is already a URL (YouTube, etc.)
            is_url = (
                query.startswith("http://")
                or query.startswith("https://")
                or query.startswith("ytsearch:")
                or query.startswith("scsearch:")
            )

            # If not a URL, add ytsearch: prefix for YouTube search
            if not is_url:
                query = f"ytsearch:{query}"

            # Check if any nodes are available
            if not wavelink.Pool.nodes:
                logger.error("No Lavalink nodes available for search")
                return None

            # Search using Wavelink
            tracks = await wavelink.Pool.fetch_tracks(query)
            if not tracks:
                logger.warning(f"No tracks found for query: {query}")
                return None

            # Return the first result
            if isinstance(tracks, wavelink.Playlist):
                return tracks.tracks[0] if tracks.tracks else None
            return tracks[0] if tracks else None
        except wavelink.NoNodesAvailable:
            logger.error("No Lavalink nodes available")
            return None
        except Exception as e:
            logger.error(f"Error searching for track '{query}': {e}", exc_info=True)
            return None

    async def play_track(
        self,
        interaction: discord.Interaction,
        track: wavelink.Playable,
        requester: discord.Member,
    ) -> None:
        """
        Play a track in the voice channel.

        Args:
            interaction: Discord interaction
            track: Wavelink playable track
            requester: User who requested the track
        """
        voice_client: Optional[wavelink.Player] = interaction.guild.voice_client  # type: ignore

        if not voice_client:
            return

        queue = self.get_queue(interaction.guild_id)  # type: ignore

        # Create queue entry
        source = (
            "Spotify"
            if self.spotify_resolver.is_spotify_url(str(track.uri or ""))
            else "YouTube"
        )
        entry = QueueEntry(
            title=track.title or "Unknown",
            source=source,
            duration=int(track.length / 1000),  # Convert ms to seconds
            requester=requester,
            identifier=str(track.uri) if track.uri else "",
            uri=str(track.uri) if track.uri else None,
        )

        # If not playing, start immediately
        if not queue.is_playing:
            queue.add(entry)
            await voice_client.play(track)
            queue.set_playing(True)

            embed = success_embed(
                "Now Playing",
                f"**{track.title}**\n"
                f"Duration: {self.format_duration(entry.duration)}\n"
                f"Requested by: {requester.mention}",
            )
        else:
            # Add to queue
            queue.add(entry)
            embed = success_embed(
                "Added to Queue",
                f"**{track.title}**\n"
                f"Duration: {self.format_duration(entry.duration)}\n"
                f"Position in queue: {len(queue.queue)}",
            )

        # Use followup if response is already deferred, otherwise use response
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed)
        else:
            await interaction.response.send_message(embed=embed)

    async def _play_track_search_and_play(self, interaction: discord.Interaction, query: str) -> None:
        """
        Helper method to validate voice state, connect, search, and play a track.
        Used by both /play and /queue commands.
        """
        # Validate voice context
        is_valid, error_emb, voice_channel = await validate_voice_context(
            interaction
        )
        if not is_valid:
            await interaction.response.send_message(embed=error_emb)
            return

        # Ensure bot voice state
        bot_voice_client = interaction.guild.voice_client  # type: ignore
        is_valid, error_emb = await ensure_bot_voice_state(
            interaction, voice_channel, bot_voice_client
        )
        if not is_valid:
            await interaction.response.send_message(embed=error_emb)
            return

        # Connect bot if not connected
        if bot_voice_client is None:
            try:
                await voice_channel.connect(cls=wavelink.Player)
                bot_voice_client = interaction.guild.voice_client  # type: ignore
            except Exception:
                await interaction.response.send_message(
                    embed=error_embed(
                        "Connection Failed", "Failed to connect to voice channel."
                    )
                )
                return

        # Defer response while searching
        await interaction.response.defer()

        # Search for track
        track = await self.search_track(query)
        if not track:
            await interaction.followup.send(
                embed=error_embed("Track Not Found", "Could not find the requested track.")
            )
            return

        # Play track
        await self.play_track(interaction, track, interaction.user)  # type: ignore

    @app_commands.command(name="play", description="Plays a song immediately or starts playback if idle")
    @app_commands.describe(query="Song name, YouTube URL, or Spotify URL")
    async def play_command(
        self, interaction: discord.Interaction, query: str
    ) -> None:
        """Play a song immediately or add to queue if already playing."""
        await self._play_track_search_and_play(interaction, query)

    @app_commands.command(name="queue", description="Adds a song to the queue or displays the current queue")
    @app_commands.describe(query="Song name, YouTube URL, or Spotify URL (optional - omit to view queue)")
    async def queue_command(
        self, interaction: discord.Interaction, query: Optional[str] = None
    ) -> None:
        """
        Add a song to the queue (or play if queue is empty).
        If no query is provided, display the current queue with pagination.
        """
        queue = self.get_queue(interaction.guild_id)  # type: ignore

        # If no query provided, display the queue
        if query is None:
            if queue.is_empty:
                await interaction.response.send_message(
                    embed=info_embed("Queue", "The queue is empty.")
                )
                return

            # Create pagination view
            view = QueuePaginationView(self, queue, interaction.guild_id)  # type: ignore
            embed = self.create_queue_embed(queue, 0, 10)
            view.update_buttons()
            await interaction.response.send_message(embed=embed, view=view)
            return

        # If query is provided, add song to queue (existing behavior)
        # Special case: if queue is empty, behave like /play
        if queue.is_empty:
            await self._play_track_search_and_play(interaction, query)
            return

        # Validate voice context
        is_valid, error_emb, voice_channel = await validate_voice_context(
            interaction
        )
        if not is_valid:
            await interaction.response.send_message(embed=error_emb)
            return

        # Ensure bot voice state
        bot_voice_client = interaction.guild.voice_client  # type: ignore
        is_valid, error_emb = await ensure_bot_voice_state(
            interaction, voice_channel, bot_voice_client
        )
        if not is_valid:
            await interaction.response.send_message(embed=error_emb)
            return

        # Defer response while searching
        await interaction.response.defer()

        # Search for track
        track = await self.search_track(query)
        if not track:
            await interaction.followup.send(
                embed=error_embed(
                    "Track Not Found", "Could not find the requested track."
                )
            )
            return

        # Add to queue
        source = (
            "Spotify"
            if self.spotify_resolver.is_spotify_url(str(track.uri or ""))
            else "YouTube"
        )
        entry = QueueEntry(
            title=track.title or "Unknown",
            source=source,
            duration=int(track.length / 1000),
            requester=interaction.user,  # type: ignore
            identifier=str(track.uri) if track.uri else "",
            uri=str(track.uri) if track.uri else None,
        )

        queue.add(entry)

        embed = success_embed(
            "Added to Queue",
            f"**{track.title}**\n"
            f"Duration: {self.format_duration(entry.duration)}\n"
            f"Position in queue: {len(queue.queue)}",
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="pause", description="Pauses the currently playing track")
    async def pause_command(self, interaction: discord.Interaction) -> None:
        """Pause the currently playing track."""
        voice_client: Optional[wavelink.Player] = interaction.guild.voice_client  # type: ignore

        if not voice_client or not voice_client.playing:
            await interaction.response.send_message(
                embed=error_embed("Not Playing", "No track is currently playing.")
            )
            return

        if voice_client.paused:
            await interaction.response.send_message(
                embed=error_embed("Already Paused", "Playback is already paused.")
            )
            return

        await voice_client.pause(True)
        queue = self.get_queue(interaction.guild_id)  # type: ignore
        queue.set_paused(True)

        await interaction.response.send_message(
            embed=success_embed("Paused", "Playback has been paused.")
        )

    @app_commands.command(name="unpause", description="Resumes paused playback")
    async def unpause_command(self, interaction: discord.Interaction) -> None:
        """Resume paused playback."""
        voice_client: Optional[wavelink.Player] = interaction.guild.voice_client  # type: ignore

        if not voice_client or not voice_client.paused:
            await interaction.response.send_message(
                embed=error_embed("Not Paused", "Playback is not paused.")
            )
            return

        await voice_client.pause(False)
        queue = self.get_queue(interaction.guild_id)  # type: ignore
        queue.set_paused(False)

        await interaction.response.send_message(
            embed=success_embed("Resumed", "Playback has been resumed.")
        )

    @app_commands.command(name="skip", description="Skips the currently playing track")
    async def skip_command(self, interaction: discord.Interaction) -> None:
        """Skip the currently playing track."""
        voice_client: Optional[wavelink.Player] = interaction.guild.voice_client  # type: ignore
        queue = self.get_queue(interaction.guild_id)  # type: ignore

        if not voice_client or not voice_client.playing:
            await interaction.response.send_message(
                embed=error_embed("Not Playing", "No track is currently playing.")
            )
            return

        # Skip to next track
        next_track = queue.skip()
        if next_track:
            # Find and play next track
            track = await wavelink.Pool.fetch_tracks(next_track.identifier)
            if track:
                await voice_client.play(track[0])
                embed = success_embed(
                    "Skipped",
                    f"Now playing: **{next_track.title}**",
                )
            else:
                embed = error_embed("Skip Failed", "Could not load the next track.")
        else:
            # No more tracks
            await voice_client.stop()
            queue.set_playing(False)
            embed = success_embed("Skipped", "Reached the end of the queue.")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="jump", description="Jumps to a specific position in the queue")
    @app_commands.describe(song_index="The position in the queue (1-based)")
    async def jump_command(
        self, interaction: discord.Interaction, song_index: int
    ) -> None:
        """Jump to a specific position in the queue."""
        queue = self.get_queue(interaction.guild_id)  # type: ignore
        voice_client: Optional[wavelink.Player] = interaction.guild.voice_client  # type: ignore

        if queue.is_empty:
            await interaction.response.send_message(
                embed=error_embed("Empty Queue", "The queue is empty.")
            )
            return

        # Convert to 0-based index
        index = song_index - 1
        if index < 0 or index >= len(queue.queue):
            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Index",
                    f"Please provide a number between 1 and {len(queue.queue)}.",
                )
            )
            return

        # Jump to track
        track_entry = queue.jump(index)
        if track_entry and voice_client:
            # Load and play the track
            track = await wavelink.Pool.fetch_tracks(track_entry.identifier)
            if track:
                await voice_client.play(track[0])
                queue.set_playing(True)
                embed = success_embed(
                    "Jumped",
                    f"Now playing: **{track_entry.title}** (Position {song_index})",
                )
            else:
                embed = error_embed("Jump Failed", "Could not load the requested track.")
        else:
            embed = error_embed("Jump Failed", "Could not jump to that position.")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="shuffle", description="Randomizes the order of the remaining queue")
    async def shuffle_command(self, interaction: discord.Interaction) -> None:
        """Shuffle the remaining queue."""
        queue = self.get_queue(interaction.guild_id)  # type: ignore

        if len(queue.queue) <= 1:
            await interaction.response.send_message(
                embed=warning_embed("Cannot Shuffle", "Need at least 2 tracks to shuffle.")
            )
            return

        queue.shuffle()
        await interaction.response.send_message(
            embed=success_embed("Shuffled", "The queue has been shuffled.")
        )

    @app_commands.command(name="quit", description="Stops playback, clears the queue, and disconnects")
    async def quit_command(self, interaction: discord.Interaction) -> None:
        """Stop playback, clear queue, and disconnect from voice channel."""
        voice_client: Optional[wavelink.Player] = interaction.guild.voice_client  # type: ignore
        queue = self.get_queue(interaction.guild_id)  # type: ignore

        if voice_client:
            await voice_client.disconnect()

        queue.clear()

        await interaction.response.send_message(
            embed=success_embed("Disconnected", "Left the voice channel and cleared the queue.")
        )

    @app_commands.command(name="help", description="Displays all available commands")
    async def help_command(self, interaction: discord.Interaction) -> None:
        """Display all available commands."""
        commands_list = [
            "**/play** `[query]` - Plays a song immediately or starts playback if idle",
            "**/queue** `[query]` - Adds a song to the queue (omit query to view queue)",
            "**/pause** - Pauses the currently playing track",
            "**/unpause** - Resumes paused playback",
            "**/skip** - Skips the currently playing track",
            "**/jump** `[song_index]` - Jumps to a specific position in the queue",
            "**/shuffle** - Randomizes the order of the remaining queue",
            "**/quit** - Stops playback, clears the queue, and disconnects",
            "**/help** - Displays this help message",
        ]

        description = "\n".join(commands_list)
        embed = info_embed("JazzBot Commands", description)
        embed.set_footer(text="Use /queue without parameters to view the current queue")

        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, payload: wavelink.TrackEndEventPayload
    ) -> None:
        """Handle track end event to play next track in queue."""
        if not payload.player or not payload.player.guild:
            return

        guild_id = payload.player.guild.id
        queue = self.get_queue(guild_id)

        # Skip to next track
        next_track = queue.skip()
        if next_track:
            # Find and play next track
            track = await wavelink.Pool.fetch_tracks(next_track.identifier)
            if track and payload.player:
                await payload.player.play(track[0])
                queue.set_playing(True)
        else:
            # Queue is empty
            queue.set_playing(False)


async def setup(bot: commands.Bot) -> None:
    """Setup function for the cog."""
    await bot.add_cog(MusicCommands(bot))

