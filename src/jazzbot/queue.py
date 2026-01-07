"""Queue management system for JazzBot."""

import random
from dataclasses import dataclass
from typing import List, Optional

import discord


@dataclass
class QueueEntry:
    """Represents a single track in the queue."""

    title: str
    source: str  # "YouTube" or "Spotify"
    duration: int  # Duration in seconds
    requester: discord.Member
    identifier: str  # Track identifier for playback
    uri: Optional[str] = None  # Original URI if applicable


class MusicQueue:
    """Manages the music queue for a single guild."""

    def __init__(self) -> None:
        """Initialize an empty queue."""
        self._queue: List[QueueEntry] = []
        self._current_index: int = 0
        self._is_playing: bool = False
        self._is_paused: bool = False

    @property
    def queue(self) -> List[QueueEntry]:
        """Get the current queue."""
        return self._queue

    @property
    def current_index(self) -> int:
        """Get the current track index."""
        return self._current_index

    @property
    def is_playing(self) -> bool:
        """Check if music is currently playing."""
        return self._is_playing

    @property
    def is_paused(self) -> bool:
        """Check if playback is paused."""
        return self._is_paused

    @property
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return len(self._queue) == 0

    @property
    def current_track(self) -> Optional[QueueEntry]:
        """Get the currently playing track."""
        if self._current_index < len(self._queue):
            return self._queue[self._current_index]
        return None

    def add(self, entry: QueueEntry) -> None:
        """Add a track to the queue."""
        self._queue.append(entry)

    def clear(self) -> None:
        """Clear the entire queue."""
        self._queue.clear()
        self._current_index = 0
        self._is_playing = False
        self._is_paused = False

    def skip(self) -> Optional[QueueEntry]:
        """
        Skip to the next track.

        Returns:
            The next track entry, or None if queue is empty
        """
        if self._current_index + 1 < len(self._queue):
            self._current_index += 1
            return self._queue[self._current_index]
        return None

    def jump(self, index: int) -> Optional[QueueEntry]:
        """
        Jump to a specific position in the queue.

        Args:
            index: Zero-based index to jump to

        Returns:
            The track at the specified index, or None if invalid
        """
        if 0 <= index < len(self._queue):
            self._current_index = index
            return self._queue[self._current_index]
        return None

    def shuffle(self) -> None:
        """Shuffle the remaining queue (preserves current track)."""
        if len(self._queue) <= 1:
            return

        # Save current track
        current = self._queue[self._current_index]

        # Shuffle remaining tracks
        remaining = self._queue[self._current_index + 1 :]
        random.shuffle(remaining)

        # Reconstruct queue
        self._queue = (
            self._queue[: self._current_index] + [current] + remaining
        )

    def set_playing(self, playing: bool) -> None:
        """Set the playing state."""
        self._is_playing = playing
        if not playing:
            self._is_paused = False

    def set_paused(self, paused: bool) -> None:
        """Set the paused state."""
        self._is_paused = paused

    def get_queue_list(self, max_items: int = 10) -> List[QueueEntry]:
        """
        Get a list of upcoming tracks.

        Args:
            max_items: Maximum number of items to return

        Returns:
            List of queue entries starting from current position
        """
        start = self._current_index
        end = min(start + max_items, len(self._queue))
        return self._queue[start:end]

