"""Spotify metadata resolution utilities."""

import re
from typing import List, Optional, Tuple

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials

    SPOTIFY_AVAILABLE = True
except ImportError:
    SPOTIFY_AVAILABLE = False


class SpotifyResolver:
    """Resolves Spotify links to searchable track information."""

    def __init__(
        self, client_id: Optional[str] = None, client_secret: Optional[str] = None
    ) -> None:
        """
        Initialize Spotify resolver.

        Args:
            client_id: Spotify API client ID
            client_secret: Spotify API client secret
        """
        self.client = None
        if SPOTIFY_AVAILABLE and client_id and client_secret:
            try:
                auth_manager = SpotifyClientCredentials(
                    client_id=client_id, client_secret=client_secret
                )
                self.client = spotipy.Spotify(auth_manager=auth_manager)
            except Exception:
                # If Spotify auth fails, continue without it
                pass

    def is_spotify_url(self, query: str) -> bool:
        """Check if the query is a Spotify URL."""
        spotify_pattern = r"https?://(open\.)?spotify\.com/(track|playlist|album)/[\w]+"
        return bool(re.match(spotify_pattern, query))

    def extract_spotify_id(self, url: str) -> Optional[Tuple[str, str]]:
        """
        Extract Spotify ID and type from URL.

        Returns:
            Tuple of (type, id) or None if invalid
        """
        pattern = r"https?://(open\.)?spotify\.com/(track|playlist|album)/([\w]+)"
        match = re.match(pattern, url)
        if match:
            return (match.group(2), match.group(3))
        return None

    def resolve_track(self, url: str) -> Optional[str]:
        """
        Resolve a Spotify track URL to a searchable query.

        Args:
            url: Spotify track URL

        Returns:
            Searchable query string (artist + track name) or None
        """
        if not self.client:
            return None

        try:
            track_id = self.extract_spotify_id(url)
            if not track_id or track_id[0] != "track":
                return None

            track = self.client.track(track_id[1])
            artists = ", ".join([artist["name"] for artist in track["artists"]])
            track_name = track["name"]
            return f"{artists} {track_name}"
        except Exception:
            return None

    def resolve_playlist(self, url: str) -> List[str]:
        """
        Resolve a Spotify playlist URL to a list of searchable queries.

        Args:
            url: Spotify playlist URL

        Returns:
            List of searchable query strings
        """
        if not self.client:
            return []

        try:
            playlist_id = self.extract_spotify_id(url)
            if not playlist_id or playlist_id[0] != "playlist":
                return []

            playlist = self.client.playlist(playlist_id[1])
            tracks = []

            for item in playlist["tracks"]["items"]:
                if item["track"]:
                    artists = ", ".join(
                        [artist["name"] for artist in item["track"]["artists"]]
                    )
                    track_name = item["track"]["name"]
                    tracks.append(f"{artists} {track_name}")

            return tracks
        except Exception:
            return []

