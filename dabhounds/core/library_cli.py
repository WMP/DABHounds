# dabhounds/core/library_cli.py

"""
Non-interactive CLI commands for library management.
"""

from pathlib import Path
from typing import Optional

from dabhounds.core.library_manager import (
    delete_tracks_bulk,
    export_to_csv,
    export_to_json,
    find_duplicates,
    get_library_details,
    get_library_tracks,
    list_user_libraries,
    print_library_summary,
)
from dabhounds.core.library_tui import show_library_manager_tui


def cmd_list_libraries():
    """List all user libraries."""
    print("[DABHound] Fetching your libraries...")
    libraries = list_user_libraries()

    if not libraries:
        print("[DABHound] No libraries found or error fetching libraries.")
        return

    print("\n" + "=" * 70)
    print(f"Your DAB Libraries ({len(libraries)} total)")
    print("=" * 70)

    for i, lib in enumerate(libraries, 1):
        lib_id = lib.get("id", "N/A")
        name = lib.get("name", "Unnamed")
        track_count = lib.get("trackCount", 0)
        is_public = lib.get("isPublic", False)

        print(f"{i}. {name}")
        print(
            f"   ID: {lib_id} | Tracks: {track_count} | Public: {'Yes' if is_public else 'No'}"
        )
        print()

    print("=" * 70)
    print("\nUse --library-view <library_id> to view details")
    print()


def cmd_view_library(library_id: str, interactive: bool = False):
    """
    View library details and tracks.

    Args:
        library_id: DAB library ID
        interactive: If True, launch interactive TUI
    """
    print(f"[DABHound] Fetching library {library_id}...")

    library = get_library_details(library_id)
    if not library:
        print(f"[DABHound] Could not fetch library {library_id}")
        return

    tracks = get_library_tracks(library_id)

    library_name = library.get("name", "Unknown")

    if interactive:
        print(f"[DABHound] Launching interactive manager for '{library_name}'...")
        show_library_manager_tui(library_id, library_name, tracks)
    else:
        print_library_summary(library, tracks)


def cmd_export_library(
    library_id: str, format: str = "json", output: Optional[str] = None
):
    """
    Export library to JSON or CSV.

    Args:
        library_id: DAB library ID
        format: 'json' or 'csv'
        output: Optional output path (defaults to ~/.dabhound/exports/)
    """
    print(f"[DABHound] Fetching library {library_id}...")

    library = get_library_details(library_id)
    if not library:
        print(f"[DABHound] Could not fetch library {library_id}")
        return

    tracks = get_library_tracks(library_id)

    if not tracks:
        print("[DABHound] No tracks to export.")
        return

    # Determine output path
    if output:
        output_path = Path(output).expanduser().resolve()
    else:
        export_dir = Path.home() / ".dabhound" / "exports"
        library_name = (
            library.get("name", "library").replace(" ", "_").replace("/", "_")
        )

        if format == "json":
            output_path = export_dir / f"{library_name}_{library_id}.json"
        else:  # csv
            output_path = export_dir / f"{library_name}_{library_id}.csv"

    print(f"[DABHound] Exporting {len(tracks)} tracks to {output_path}...")

    success = False
    if format == "json":
        success = export_to_json(tracks, output_path, minimal=False)
    elif format == "csv":
        success = export_to_csv(tracks, output_path)
    else:
        print(f"[DABHound] Unknown format: {format}")
        return

    if success:
        print(f"[DABHound] Successfully exported to {output_path}")
    else:
        print("[DABHound] Export failed.")


def cmd_find_duplicates(
    library_id: str, threshold: int = 95, interactive: bool = False
):
    """
    Find duplicate tracks in library.

    Args:
        library_id: DAB library ID
        threshold: Similarity threshold (0-100)
        interactive: If True, show in TUI with duplicates filter
    """
    print(f"[DABHound] Fetching library {library_id}...")

    library = get_library_details(library_id)
    if not library:
        print(f"[DABHound] Could not fetch library {library_id}")
        return

    tracks = get_library_tracks(library_id)

    print(f"[DABHound] Searching for duplicates (threshold: {threshold}%)...")
    duplicate_groups = find_duplicates(tracks, threshold)

    if not duplicate_groups:
        print("[DABHound] No duplicates found!")
        return

    total_dups = sum(len(group) for group in duplicate_groups)
    print(
        f"\n[DABHound] Found {len(duplicate_groups)} duplicate groups ({total_dups} total tracks)"
    )

    if interactive:
        library_name = library.get("name", "Unknown")
        print("[DABHound] Launching interactive manager with duplicates filter...")
        show_library_manager_tui(library_id, library_name, tracks)
    else:
        print("\n" + "=" * 70)
        print("Duplicate Groups:")
        print("=" * 70)

        for i, group in enumerate(duplicate_groups, 1):
            print(f"\nGroup {i} ({len(group)} tracks):")
            for track in group:
                print(
                    f"  - {track.get('artist', 'Unknown')} - {track.get('title', 'Unknown')}"
                )
                print(f"    ID: {track.get('id')} | ISRC: {track.get('isrc', 'N/A')}")

        print("\n" + "=" * 70)
        print("\nTip: Use --interactive to manage duplicates interactively")
        print()


def cmd_delete_tracks(library_id: str, track_ids: list):
    """
    Delete specific tracks from library (non-interactive).

    Args:
        library_id: DAB library ID
        track_ids: List of track IDs to delete
    """
    if not track_ids:
        print("[DABHound] No track IDs provided.")
        return

    print(f"[DABHound] Deleting {len(track_ids)} tracks from library {library_id}...")

    # Confirmation
    confirm = (
        input(f"Are you sure you want to delete {len(track_ids)} tracks? (y/N): ")
        .strip()
        .lower()
    )
    if confirm != "y":
        print("[DABHound] Delete cancelled.")
        return

    success, failed = delete_tracks_bulk(library_id, track_ids)

    print(f"[DABHound] Deleted {success} tracks successfully.")
    if failed > 0:
        print(f"[DABHound] Failed to delete {failed} tracks.")
