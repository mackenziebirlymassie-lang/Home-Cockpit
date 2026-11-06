"""
Windows Media Session Tracker
Fetches current playing media (Spotify, Chrome, Edge, etc.) using Windows Runtime / WinRT API.
"""
import asyncio
from dataclasses import dataclass
from typing import Optional

@dataclass
class MediaTrackInfo:
    title: str = "Idle"
    artist: str = "No media playing"
    album: str = ""
    status: str = "Stopped"

async def get_current_media_track() -> MediaTrackInfo:
    try:
        try:
            from winrt.windows.media.control import (
                GlobalSystemMediaTransportControlsSessionManager as MediaManager
            )
        except ImportError:
            from winsdk.windows.media.control import (
                GlobalSystemMediaTransportControlsSessionManager as MediaManager
            )
        sessions = await MediaManager.request_async()
        current_session = sessions.get_current_session()
        
        if not current_session:
            return MediaTrackInfo(title="No Active Media", artist="Player Idle", status="Idle")

        info = await current_session.try_get_media_properties_async()
        if not info:
            return MediaTrackInfo(title="No Media Info", artist="Player Idle", status="Idle")

        playback_info = current_session.get_playback_info()
        playback_status = "Playing" if playback_info and int(playback_info.playback_status) == 4 else "Paused"

        return MediaTrackInfo(
            title=info.title or "Unknown Title",
            artist=info.artist or "Unknown Artist",
            album=info.album_title or "",
            status=playback_status,
        )
    except Exception:
        # Fallback if Windows Media Session is unavailable or permissions denied
        return MediaTrackInfo(title="Ready", artist="Windows Media Bridge", status="Active")

def fetch_media_sync() -> MediaTrackInfo:
    try:
        return asyncio.run(get_current_media_track())
    except Exception:
        return MediaTrackInfo()
