# Saya Music
import asyncio
import re
import time

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from youtubesearchpython.aio import VideosSearch

import config


class SpotifyAPI:
    def __init__(self):
        self.regex = r"^https:\/\/open\.spotify\.com\/.+"
        self.client_id = config.SPOTIFY_CLIENT_ID
        self.client_secret = config.SPOTIFY_CLIENT_SECRET
        self._track_cache = {}
        if self.client_id and self.client_secret:
            self.client_credentials_manager = SpotifyClientCredentials(
                self.client_id, self.client_secret
            )
            self.spotify = spotipy.Spotify(
                client_credentials_manager=self.client_credentials_manager
            )
        else:
            self.spotify = None

    async def valid(self, link: str) -> bool:
        return bool(re.search(self.regex, link or ""))

    async def search(self, query: str):
        """Search Spotify metadata only; never returns an audio stream."""
        if not self.spotify:
            return None

        def _search():
            return self.spotify.search(q=query, type="track", limit=1)

        try:
            payload = await asyncio.to_thread(_search)
            items = (payload.get("tracks") or {}).get("items") or []
            if not items:
                return None
            track = items[0]
            artists = ", ".join(a.get("name", "") for a in track.get("artists", []) if a.get("name"))
            images = ((track.get("album") or {}).get("images") or [])
            return {
                "title": track.get("name", ""),
                "artist": artists,
                "album": (track.get("album") or {}).get("name", ""),
                "thumb": images[0].get("url", "") if images else "",
                "spotify_url": ((track.get("external_urls") or {}).get("spotify", "")),
                "duration_ms": track.get("duration_ms", 0),
            }
        except Exception:
            return None

    async def track(self, link: str):
        if not self.spotify:
            raise RuntimeError("Spotify credentials not configured")

        now = time.monotonic()
        cached = self._track_cache.get(link)
        if cached and now - cached[0] < 600:
            details = dict(cached[1])
            return details, details["vidid"]

        # Spotipy is synchronous. Keep its network request off the event loop
        # so assistant joins, callbacks and other groups stay responsive.
        track = await asyncio.to_thread(self.spotify.track, link)
        info = track["name"]
        artists = []
        for artist in track["artists"]:
            fetched = artist["name"]
            if fetched and "Various Artists" not in fetched:
                artists.append(fetched)
                info += f" {fetched}"

        results = VideosSearch(info, limit=1)
        data = await results.next()
        found = data.get("result") or []
        if not found:
            raise RuntimeError("No matching playable track was found")
        result = found[0]
        album_images = (track.get("album") or {}).get("images") or []
        spotify_artwork = album_images[0].get("url", "") if album_images else ""
        track_details = {
            "title": f"{track['name']} - {', '.join(artists)}" if artists else track["name"],
            "link": result["link"],
            "vidid": result["id"],
            "duration_min": result["duration"],
            "thumb": spotify_artwork or result["thumbnails"][0]["url"].split("?")[0],
            "spotify_url": (track.get("external_urls") or {}).get("spotify", ""),
        }
        self._track_cache[link] = (now, dict(track_details))
        # Bound memory use; the cache is deliberately short-lived.
        if len(self._track_cache) > 256:
            oldest = min(self._track_cache, key=lambda key: self._track_cache[key][0])
            self._track_cache.pop(oldest, None)
        return track_details, track_details["vidid"]

    async def playlist(self, url):
        if not self.spotify:
            raise RuntimeError("Spotify credentials not configured")
        playlist = await asyncio.to_thread(self.spotify.playlist, url)
        playlist_id = playlist["id"]
        results = []
        for item in playlist["tracks"]["items"]:
            music_track = item["track"]
            info = music_track["name"]
            for artist in music_track["artists"]:
                fetched = f' {artist["name"]}'
                if "Various Artists" not in fetched:
                    info += fetched
            results.append(info)
        return results, playlist_id

    async def album(self, url):
        if not self.spotify:
            raise RuntimeError("Spotify credentials not configured")
        album = await asyncio.to_thread(self.spotify.album, url)
        album_id = album["id"]
        results = []
        for item in album["tracks"]["items"]:
            info = item["name"]
            for artist in item["artists"]:
                fetched = f' {artist["name"]}'
                if "Various Artists" not in fetched:
                    info += fetched
            results.append(info)
        return results, album_id

    async def artist(self, url):
        if not self.spotify:
            raise RuntimeError("Spotify credentials not configured")
        artistinfo, artisttoptracks = await asyncio.gather(
            asyncio.to_thread(self.spotify.artist, url),
            asyncio.to_thread(self.spotify.artist_top_tracks, url),
        )
        artist_id = artistinfo["id"]
        results = []
        for item in artisttoptracks["tracks"]:
            info = item["name"]
            for artist in item["artists"]:
                fetched = f' {artist["name"]}'
                if "Various Artists" not in fetched:
                    info += fetched
            results.append(info)
        return results, artist_id
