# dabhounds/core/library_manager.py

"""
Library Manager - API for managing DAB libraries.
Provides functions to:
- Fetch library details and tracks
- Delete tracks from libraries
- Find duplicates
- Export to JSON/CSV
"""

import csv
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rapidfuzz import fuzz

from dabhounds.core.auth import get_authenticated_session, load_config

CONFIG = load_config()
API_BASE = CONFIG["DAB_API_BASE"]

# Cache directory
CACHE_DIR = Path.home() / ".dabhound" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Cache expiry time (in seconds) - 1 hour
CACHE_EXPIRY = 3600


def _get_cache_path(library_id: str) -> Path:
    """Get cache file path for a library."""
    return CACHE_DIR / f"library_{library_id}.json"


def _load_cache(library_id: str) -> Optional[Dict]:
    """Load cached library data if valid."""
    cache_path = _get_cache_path(library_id)

    if not cache_path.exists():
        return None

    try:
        # Check if cache is expired
        cache_age = time.time() - cache_path.stat().st_mtime
        if cache_age > CACHE_EXPIRY:
            print(f"[DABHound] Cache expired for library {library_id}")
            return None

        with cache_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"[DABHound] Loaded {len(data.get('tracks', []))} tracks from cache")
            return data
    except Exception as e:
        print(f"[DABHound] Error loading cache: {e}")
        return None


def _save_cache(library_id: str, data: Dict):
    """Save library data to cache."""
    cache_path = _get_cache_path(library_id)

    try:
        with cache_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[DABHound] Error saving cache: {e}")


def _invalidate_cache(library_id: str):
    """Delete cache for a library."""
    cache_path = _get_cache_path(library_id)
    if cache_path.exists():
        cache_path.unlink()


def get_library_details(library_id: str) -> Optional[Dict]:
    """
    Fetch library metadata from DAB API.

    Returns:
        Dictionary with library info: {id, name, description, isPublic, tracks, etc.}
        The response includes full library object with embedded tracks.
        Returns None if library doesn't exist or request fails.
    """
    session = get_authenticated_session()
    try:
        response = session.get(f"{API_BASE}/libraries/{library_id}")
        if response.status_code == 200:
            data = response.json()
            # API returns {"library": {...}} format
            if isinstance(data, dict) and "library" in data:
                return data["library"]
            return data
        elif response.status_code == 404:
            print(f"[DABHound] Library {library_id} not found.")
            return None
        else:
            print(f"[DABHound] Error fetching library: {response.status_code}")
            return None
    except Exception as e:
        print(f"[DABHound] Exception while fetching library: {e}")
        return None


def get_library_tracks(library_id: str, use_cache: bool = True) -> List[Dict]:
    """
    Fetch all tracks from a DAB library.

    Note: DAB API returns tracks as part of the library object with pagination.
    This function handles pagination automatically to fetch all tracks.
    Results are cached to speed up subsequent requests.

    Args:
        library_id: DAB library ID
        use_cache: If True, use cached data if available (default: True)

    Returns:
        List of track dictionaries with full metadata.
    """
    # Try cache first
    if use_cache:
        cached = _load_cache(library_id)
        if cached:
            return cached.get("tracks", [])

    print(f"[DABHound] Fetching all tracks from API...")
    session = get_authenticated_session()
    all_tracks = []
    page = 1
    total_pages = None

    while True:
        try:
            # Fetch page
            response = session.get(
                f"{API_BASE}/libraries/{library_id}", params={"page": page}
            )
            if response.status_code != 200:
                print(
                    f"[DABHound] Error fetching tracks page {page}: {response.status_code}"
                )
                break

            data = response.json()
            if isinstance(data, dict) and "library" in data:
                library = data["library"]
            else:
                library = data

            # Get tracks from this page
            tracks = library.get("tracks", [])
            if tracks:
                all_tracks.extend(tracks)

            # Check pagination
            pagination = library.get("pagination", {})
            has_more = pagination.get("hasMore", False)

            if total_pages is None and pagination.get("total"):
                total_pages = (
                    pagination["total"] + pagination.get("limit", 20) - 1
                ) // pagination.get("limit", 20)

            if total_pages:
                print(
                    f"[DABHound] Fetched page {page}/{total_pages} ({len(all_tracks)} tracks so far)"
                )

            if not has_more:
                break

            page += 1

        except Exception as e:
            print(f"[DABHound] Exception while fetching tracks page {page}: {e}")
            break

    # Cache the result
    if all_tracks:
        _save_cache(
            library_id,
            {"id": library_id, "tracks": all_tracks, "cached_at": time.time()},
        )
        print(f"[DABHound] Cached {len(all_tracks)} tracks")

    return all_tracks


def delete_track_from_library(library_id: str, track_id: str) -> bool:
    """
    Delete a track from a DAB library.

    Returns:
        True if successful, False otherwise.
    """
    session = get_authenticated_session()
    try:
        response = session.delete(
            f"{API_BASE}/libraries/{library_id}/tracks/{track_id}"
        )
        if response.status_code in [200, 204]:
            return True
        else:
            print(f"[DABHound] Error deleting track {track_id}: {response.status_code}")
            return False
    except Exception as e:
        print(f"[DABHound] Exception while deleting track: {e}")
        return False


def delete_tracks_bulk(library_id: str, track_ids: List[str]) -> Tuple[int, int]:
    """
    Delete multiple tracks from a library.

    Returns:
        (success_count, failure_count)
    """
    success = 0
    failed = 0

    for track_id in track_ids:
        if delete_track_from_library(library_id, track_id):
            success += 1
        else:
            failed += 1

    # Invalidate cache after deletions
    if success > 0:
        _invalidate_cache(library_id)

    return success, failed


def find_duplicates(
    tracks: List[Dict], similarity_threshold: int = 95
) -> List[List[Dict]]:
    """
    Find duplicate tracks based on title, artist, and ISRC.

    Args:
        tracks: List of track dictionaries
        similarity_threshold: Fuzzy matching threshold (0-100)

    Returns:
        List of duplicate groups. Each group is a list of tracks that are duplicates.
    """
    duplicates = []
    processed = set()

    for i, track1 in enumerate(tracks):
        if i in processed:
            continue

        group = [track1]
        track1_key = f"{track1.get('artist', '')} {track1.get('title', '')}"
        track1_isrc = track1.get("isrc", "")

        for j, track2 in enumerate(tracks[i + 1 :], start=i + 1):
            if j in processed:
                continue

            # Check ISRC first (exact match)
            track2_isrc = track2.get("isrc", "")
            if track1_isrc and track2_isrc and track1_isrc == track2_isrc:
                group.append(track2)
                processed.add(j)
                continue

            # Fuzzy match on artist + title
            track2_key = f"{track2.get('artist', '')} {track2.get('title', '')}"
            score = fuzz.token_set_ratio(track1_key, track2_key)

            if score >= similarity_threshold:
                group.append(track2)
                processed.add(j)

        if len(group) > 1:
            duplicates.append(group)
            processed.add(i)

    return duplicates


def export_to_json(
    tracks: List[Dict], output_path: Path, minimal: bool = False
) -> bool:
    """
    Export tracks to JSON format.

    Args:
        tracks: List of track dictionaries
        output_path: Path to save JSON file
        minimal: If True, export only essential fields (artist, title, id, isrc)

    Returns:
        True if successful
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if minimal:
            simplified = []
            for track in tracks:
                simplified.append(
                    {
                        "id": track.get("id"),
                        "title": track.get("title"),
                        "artist": track.get("artist"),
                        "isrc": track.get("isrc"),
                        "albumTitle": track.get("albumTitle"),
                        "duration": track.get("duration"),
                    }
                )
            data = simplified
        else:
            data = tracks

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        print(f"[DABHound] Error exporting to JSON: {e}")
        return False


def export_to_csv(tracks: List[Dict], output_path: Path) -> bool:
    """
    Export tracks to CSV format.

    Args:
        tracks: List of track dictionaries
        output_path: Path to save CSV file

    Returns:
        True if successful
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "id",
            "title",
            "artist",
            "albumTitle",
            "isrc",
            "duration",
            "releaseDate",
        ]

        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(tracks)

        return True
    except Exception as e:
        print(f"[DABHound] Error exporting to CSV: {e}")
        return False


def list_user_libraries() -> List[Dict]:
    """
    Fetch all libraries for the authenticated user.

    Returns:
        List of library dictionaries with basic info.
    """
    session = get_authenticated_session()
    try:
        response = session.get(f"{API_BASE}/libraries")
        if response.status_code == 200:
            data = response.json()
            # Handle different API response formats
            if isinstance(data, dict) and "libraries" in data:
                return data["libraries"]
            return data if isinstance(data, list) else []
        else:
            print(f"[DABHound] Error fetching libraries: {response.status_code}")
            return []
    except Exception as e:
        print(f"[DABHound] Exception while fetching libraries: {e}")
        return []


def find_library_by_name(name: str) -> Optional[str]:
    """
    Find library ID by name (case-insensitive partial match).

    Args:
        name: Library name to search for

    Returns:
        Library ID if found, None otherwise
    """
    libraries = list_user_libraries()
    name_lower = name.lower()

    # Try exact match first
    for lib in libraries:
        if lib.get("name", "").lower() == name_lower:
            return lib.get("id")

    # Try partial match
    for lib in libraries:
        if name_lower in lib.get("name", "").lower():
            return lib.get("id")

    return None


def print_library_summary(library: Dict, tracks: List[Dict]):
    """
    Print a formatted summary of library details.

    Args:
        library: Library metadata dictionary
        tracks: List of tracks in the library
    """
    print("\n" + "=" * 70)
    print(f"Library: {library.get('name', 'Unknown')}")
    print("=" * 70)
    print(f"ID: {library.get('id', 'N/A')}")
    print(f"Description: {library.get('description', 'N/A')}")
    print(f"Public: {'Yes' if library.get('isPublic') else 'No'}")
    print(f"Total Tracks: {len(tracks)}")
    print("=" * 70)

    if tracks:
        print("\nTracks:")
        print("-" * 70)
        for i, track in enumerate(tracks, 1):
            print(
                f"{i}. {track.get('artist', 'Unknown')} - {track.get('title', 'Unknown')}"
            )
            print(f"   ID: {track.get('id')} | Album: {track.get('albumTitle', 'N/A')}")

        print("-" * 70)
    else:
        print("\n(No tracks in library)")

    print()
