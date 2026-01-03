# dabhounds/core/download.py

"""
File download module for DABHounds.
Handles downloading tracks from DAB in various quality formats.
"""

import os
import time
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

import requests
from mutagen.flac import FLAC
from mutagen.id3 import APIC, ID3, TALB, TDRC, TIT2, TPE1
from mutagen.mp3 import MP3
from tqdm import tqdm

from dabhounds.core.auth import get_authenticated_session, load_config

CONFIG = load_config()
API_BASE = CONFIG["DAB_API_BASE"]

# Quality format mapping (Qobuz-based)
QUALITY_FORMATS = {
    "mp3": 5,  # MP3 320kbps
    "cd": 6,  # CD Quality (16-bit/44.1kHz FLAC)
    "hires": 7,  # Hi-Res 24-bit up to 96kHz
    "hires_max": 27,  # Hi-Res 24-bit up to 192kHz
}

# Reverse mapping for display
QUALITY_NAMES = {
    5: "MP3 320kbps",
    6: "CD Quality (16-bit/44.1kHz FLAC)",
    7: "Hi-Res 24-bit (up to 96kHz)",
    27: "Hi-Res 24-bit (up to 192kHz)",
}


def get_stream_url(track_id: str, quality: int = 27) -> Optional[str]:
    """
    Get streaming URL for a track from DAB API.

    Args:
        track_id: DAB track ID
        quality: Quality format code (5, 6, 7, 27)

    Returns:
        Streaming URL or None if failed
    """
    session = get_authenticated_session()
    if not session:
        print("[DABHound] Error: Not authenticated. Please login first.")
        return None

    try:
        response = session.get(
            f"{API_BASE}/stream",
            params={"trackId": track_id, "quality": quality},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        if "url" in data:
            return data["url"]
        else:
            print(f"[DABHound] Error: No URL in response for track {track_id}")
            return None

    except requests.RequestException as e:
        print(f"[DABHound] Error getting stream URL: {e}")
        return None


def add_metadata_to_file(file_path: Path, track: Dict) -> bool:
    """
    Add metadata (tags) to downloaded audio file.

    Args:
        file_path: Path to audio file
        track: Track dictionary with metadata

    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract metadata from track
        title = track.get("title", "")
        artist = track.get("artist", "")
        album = track.get("albumTitle", "")
        release_date = track.get("releaseDate", "")
        year = (
            release_date.split("-")[0]
            if release_date and "-" in release_date
            else release_date
        )

        # Get album cover URL
        album_cover_url = None
        image = track.get("image")
        if image:
            if isinstance(image, dict):
                # Try different size keys
                album_cover_url = (
                    image.get("large") or image.get("medium") or image.get("small")
                )
            elif isinstance(image, str):
                album_cover_url = image

        # Download album cover if available
        album_cover_data = None
        if album_cover_url:
            try:
                cover_response = requests.get(album_cover_url, timeout=10)
                if cover_response.status_code == 200:
                    album_cover_data = cover_response.content
            except:
                pass  # Continue without cover

        # Add metadata based on file type
        if file_path.suffix.lower() == ".mp3":
            # MP3 metadata using ID3
            try:
                audio = MP3(file_path, ID3=ID3)
            except:
                # Create ID3 tag if doesn't exist
                audio = MP3(file_path)
                audio.add_tags()

            if title:
                audio.tags.add(TIT2(encoding=3, text=title))
            if artist:
                audio.tags.add(TPE1(encoding=3, text=artist))
            if album:
                audio.tags.add(TALB(encoding=3, text=album))
            if year:
                audio.tags.add(TDRC(encoding=3, text=year))

            # Add album cover
            if album_cover_data:
                audio.tags.add(
                    APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,  # Cover (front)
                        desc="Cover",
                        data=album_cover_data,
                    )
                )

            audio.save()

        elif file_path.suffix.lower() == ".flac":
            # FLAC metadata
            audio = FLAC(file_path)

            if title:
                audio["title"] = title
            if artist:
                audio["artist"] = artist
            if album:
                audio["album"] = album
            if year:
                audio["date"] = year

            # Add album cover
            if album_cover_data:
                from mutagen.flac import Picture

                picture = Picture()
                picture.type = 3  # Cover (front)
                picture.mime = "image/jpeg"
                picture.desc = "Cover"
                picture.data = album_cover_data
                audio.add_picture(picture)

            audio.save()

        return True

    except Exception as e:
        print(f"[DABHound] Warning: Could not add metadata: {e}")
        return False


def download_file(url: str, output_path: Path, show_progress: bool = True) -> bool:
    """
    Download a file from URL with progress bar.

    Args:
        url: Download URL
        output_path: Path where file will be saved
        show_progress: Show progress bar

    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))

        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Download with progress bar
        with open(output_path, "wb") as f:
            if show_progress and total_size > 0:
                with tqdm(
                    total=total_size, unit="iB", unit_scale=True, desc=output_path.name
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            else:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        return True

    except requests.RequestException as e:
        print(f"[DABHound] Error downloading file: {e}")
        return False


def download_track(
    track: Dict,
    output_dir: Path = None,
    quality: str = "hires_max",
    filename_template: str = "{artist} - {title}",
    show_progress: bool = True,
) -> Optional[Path]:
    """
    Download a single track from DAB.

    Args:
        track: Track dictionary with id, title, artist, etc.
        output_dir: Directory where file will be saved (default: ./downloads)
        quality: Quality format name (mp3, cd, hires, hires_max)
        filename_template: Template for filename (supports: {artist}, {title}, {album}, {id})
        show_progress: Show progress bar

    Returns:
        Path to downloaded file or None if failed
    """
    track_id = str(track.get("id"))
    if not track_id:
        print("[DABHound] Error: Track has no ID")
        return None

    # Get quality code
    quality_code = QUALITY_FORMATS.get(quality.lower())
    if quality_code is None:
        print(
            f"[DABHound] Error: Unknown quality '{quality}'. Valid: {', '.join(QUALITY_FORMATS.keys())}"
        )
        return None

    # Get stream URL
    print(
        f"[DABHound] Getting stream URL for track {track_id} ({QUALITY_NAMES[quality_code]})..."
    )
    stream_url = get_stream_url(track_id, quality_code)
    if not stream_url:
        return None

    # Determine file extension from URL or quality
    if quality_code == 5:
        extension = ".mp3"
    else:
        extension = ".flac"

    # Build filename from template
    filename_vars = {
        "artist": track.get("artist", "Unknown Artist"),
        "title": track.get("title", "Unknown Title"),
        "album": track.get("albumTitle", ""),
        "id": track_id,
    }

    # Sanitize filename
    filename = filename_template.format(**filename_vars)
    # Remove invalid characters
    filename = "".join(c for c in filename if c not in r'\/:*?"<>|')
    filename = filename.strip()

    # Set output directory
    if output_dir is None:
        output_dir = Path("./downloads")

    output_path = output_dir / f"{filename}{extension}"

    # Check if file already exists
    if output_path.exists():
        print(f"[DABHound] File already exists: {output_path}")
        response = input("Overwrite? (y/N): ").strip().lower()
        if response != "y":
            print("[DABHound] Skipping download.")
            return output_path

    # Download
    print(f"[DABHound] Downloading to: {output_path}")
    if download_file(stream_url, output_path, show_progress):
        # Add metadata to the file
        print(f"[DABHound] Adding metadata...")
        add_metadata_to_file(output_path, track)
        print(f"[DABHound] ✓ Downloaded: {output_path}")
        return output_path
    else:
        # Clean up partial download
        if output_path.exists():
            output_path.unlink()
        return None


def download_tracks(
    tracks: List[Dict],
    output_dir: Path = None,
    quality: str = "hires_max",
    filename_template: str = "{artist} - {title}",
    show_progress: bool = True,
    delay: float = 1.0,
) -> List[Path]:
    """
    Download multiple tracks.

    Args:
        tracks: List of track dictionaries
        output_dir: Directory where files will be saved
        quality: Quality format name
        filename_template: Template for filenames
        show_progress: Show progress bars
        delay: Delay between downloads (seconds) to avoid rate limiting

    Returns:
        List of successfully downloaded file paths
    """
    downloaded = []

    print(f"\n[DABHound] Starting download of {len(tracks)} track(s)...")

    for i, track in enumerate(tracks, 1):
        print(f"\n[DABHound] === Track {i}/{len(tracks)} ===")

        result = download_track(
            track,
            output_dir=output_dir,
            quality=quality,
            filename_template=filename_template,
            show_progress=show_progress,
        )

        if result:
            downloaded.append(result)

        # Delay between downloads (except after last track)
        if i < len(tracks) and delay > 0:
            time.sleep(delay)

    print(f"\n[DABHound] Downloaded {len(downloaded)}/{len(tracks)} track(s)")
    return downloaded


def get_available_qualities(track_id: str) -> List[Dict[str, any]]:
    """
    Get list of available quality formats for a track.

    Args:
        track_id: DAB track ID

    Returns:
        List of dicts with 'code', 'name', 'available' keys
    """
    # Try to get stream URL for each quality
    available = []

    for name, code in QUALITY_FORMATS.items():
        url = get_stream_url(track_id, code)
        available.append(
            {
                "format": name,
                "code": code,
                "name": QUALITY_NAMES[code],
                "available": url is not None,
            }
        )

    return available
