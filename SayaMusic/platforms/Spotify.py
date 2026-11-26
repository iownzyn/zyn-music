# Saya Music
import asyncio
import difflib
import re
import time

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from youtubesearchpython.aio import VideosSearch

import config


class SpotifyAPI:
    def __init__(self):
        self.regex = r"^https?://open\\.spotify\\.com/.+"
        self.client_id = config.SPOTIFY_CLIENT_ID
        self.client_secret = config.SPOTIFY_CLIENT_SECRET
        self._track_cache = {}
        self._search_cache = {}
        self._cache_ttl = 600
        if self.client_id and self.client_secret:
            self.client_credentials_manager = SpotifyClientCredentials(
                self.client_id, self.client_secret
            )
            self.spotify = spotipy.Spotify(
                client_credentials_manager=self.client_credentials_manager,
                requests_timeout=12,
                retries=2,
                status_retries=2,
                backoff_factor=0.3,
            )
        else:
            self.spotify = None

    async def valid(self, link: str) -> bool:
        return bool(re.search(self.regex, link or ""))

    @staticmethod
    def _track_details(track):
        artists = [
            artist.get("name", "")
            for artist in track.get("artists", [])
            if artist.get("name") and "Various Artists" not in artist.get("name", "")
        ]
        images = ((track.get("album") or {}).get("images") or [])
        return {
            "title": track.get("name", ""),
            "artist": ", ".join(artists),
            "album": (track.get("album") or {}).get("name", ""),
            "thumb": images[0].get("url", "") if images else "",
            "spotify_url": (track.get("external_urls") or {}).get("spotify", ""),
            "duration_ms": track.get("duration_ms", 0),
        }

    async def metadata(self, link: str):
        """Fetch canonical Spotify track metadata; Spotify API does not expose audio streams."""
        if not self.spotify:
            raise RuntimeError("Spotify credentials not configured")
        track_id = link.rstrip("/").split("/")[-1].split("?")[0]
        now = time.monotonic()
        cache_key = f"url:{track_id}"
        cached = self._track_cache.get(cache_key)
        if cached and now - cached[0] < self._cache_ttl:
            return dict(cached[1])

        track = await asyncio.to_thread(self.spotify.track, track_id)
        details = self._track_details(track)
        if not details["title"]:
            raise RuntimeError("Spotify returned an empty track title")
        self._track_cache[cache_key] = (now, dict(details))
        return details

    async def search(self, query: str):
        """Search Spotify first for canonical metadata, not a protected audio stream."""
        if not self.spotify:
            return None
        normalized = " ".join((query or "").split()).lower()
        if not normalized:
            return None
        now = time.monotonic()
        cached = self._search_cache.get(normalized)
        if cached and now - cached[0] < self._cache_ttl:
            return dict(cached[1])

        def _search():
            return self.spotify.search(q=query, type="track", limit=5)

        try:
            payload = await asyncio.to_thread(_search)
            items = (payload.get("tracks") or {}).get("items") or []
            if not items:
                return None

            # Spotify relevance order is retained, but prefer a result whose
            # title/artist text most closely matches the user's full query.
            def score(item):
                candidate = self._track_details(item)
                haystack = f"{candidate['title']} {candidate['artist']}".lower()
                return difflib.SequenceMatcher(None, normalized, haystack).ratio()

            best = max(items, key=score)
            details = self._track_details(best)
            self._search_cache[normalized] = (now, dict(details))
            if len(self._search_cache) > 512:
                oldest = min(self._search_cache, key=lambda key: self._search_cache[key][0])
                self._search_cache.pop(oldest, None)
            return details
        except Exception:
            return None

    @staticmethod
    def _duration_seconds(value):
        if not value:
            return 0
        try:
            parts = [int(part) for part in str(value).split(":")]
            total = 0
            for part in parts:
                total = total * 60 + part
            return total
        except (TypeError, ValueError):
            return 0

    async def _find_youtube_match(self, title: str, artist: str, duration_ms: int = 0):
        """Try multiple query variants and choose the closest title/duration match."""
        queries = []
        full = " ".join(part for part in (title, artist) if part).strip()
        if full:
            queries.append(full)
        if title and artist:
            queries.append(f'"{title}" "{artist}" official audio')
            queries.append(f"{title} {artist} audio")
        if title:
            queries.append(title)

        seen = set()
        candidates = []
        for query in queries:
            if query.lower() in seen:
                continue
            seen.add(query.lower())
            try:
                response = await VideosSearch(query, limit=8).next()
                candidates.extend(response.get("result") or [])
            except Exception:
                continue
            if candidates:
                # A good result from the exact title+artist query is enough;
                # avoid slow, unnecessary extra provider requests.
                break

        if not candidates:
            raise RuntimeError("Spotify track found, but no playable audio match was found")

        target_seconds = int(duration_ms / 1000) if duration_ms else 0

        def score(item):
            candidate_title = item.get("title", "")
            title_score = difflib.SequenceMatcher(
                None, f"{title} {artist}".lower(), candidate_title.lower()
            ).ratio()
            candidate_seconds = self._duration_seconds(item.get("duration"))
            duration_score = 0
            if target_seconds and candidate_seconds:
                difference = abs(target_seconds - candidate_seconds)
                duration_score = max(0, 1 - difference / max(target_seconds, 1))
            return (title_score * 0.8) + (duration_score * 0.2)

        candidates.sort(key=score, reverse=True)
        return candidates[0]

    async def track(self, link: str):
        if not self.spotify:
            raise RuntimeError("Spotify credentials not configured")

        track_id = link.rstrip("/").split("/")[-1].split("?")[0]
        now = time.monotonic()
        cache_key = f"resolved:{track_id}"
        cached = self._track_cache.get(cache_key)
        if cached and now - cached[0] < self._cache_ttl:
            details = dict(cached[1])
            return details, details["vidid"]

        # Spotify's synchronous API call runs in a worker thread so the
        # event loop remains available for assistant joins and player controls.
        spotify_details = await self.metadata(link)
        result = await self._find_youtube_match(
            spotify_details["title"],
            spotify_details["artist"],
            spotify_details["duration_ms"],
        )

        track_details = {
            "title": (
                f"{spotify_details['title']} - {spotify_details['artist']}"
                if spotify_details["artist"] else spotify_details["title"]
            ),
            "link": result.get("link"),
            "vidid": result.get("id"),
            "duration_min": result.get("duration"),
            "thumb": spotify_details["thumb"] or (
                (result.get("thumbnails") or [{}])[0].get("url", "").split("?")[0]
            ),
            "spotify_url": spotify_details["spotify_url"],
            "spotify_duration_ms": spotify_details["duration_ms"],
        }
        if not track_details["vidid"] or not track_details["link"]:
            raise RuntimeError("No usable playback result was returned")
        self._track_cache[cache_key] = (now, dict(track_details))
        if len(self._track_cache) > 512:
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
            if not music_track:
                continue
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
