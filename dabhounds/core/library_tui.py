# dabhounds/core/library_tui.py

"""
Interactive TUI for library management.
Features:
- Browse library tracks
- Select/deselect tracks
- Filter tracks
- Delete selected tracks
- Export selected tracks to JSON/CSV
- Find and manage duplicates
"""

import sys
from pathlib import Path
from typing import Dict, List, Set

try:
    import curses

    HAS_CURSES = True
except ImportError:
    HAS_CURSES = False

from dabhounds.core.library_manager import (
    delete_tracks_bulk,
    export_to_csv,
    export_to_json,
    find_duplicates,
)


class LibraryTUI:
    """Interactive TUI for managing DAB libraries."""

    def __init__(self, library_id: str, library_name: str, tracks: List[Dict]):
        self.library_id = library_id
        self.library_name = library_name
        self.tracks = tracks
        self.selected_ids: Set[str] = set()
        self.scroll_pos = 0
        self.cursor_pos = 0  # Current highlighted track in filtered list
        self.current_filter = "all"  # all, selected, duplicates
        self.search_query = ""
        self.duplicate_groups = []
        self.show_help = False
        self.track_to_group = {}  # Map track ID to group number

    def get_filtered_tracks(self) -> List[Dict]:
        """Get tracks based on current filter and search query."""
        filtered = self.tracks

        # Apply filter
        if self.current_filter == "selected":
            filtered = [t for t in filtered if str(t.get("id")) in self.selected_ids]
        elif self.current_filter == "duplicates":
            # Return tracks grouped by duplicate groups
            filtered = []
            for group in self.duplicate_groups:
                filtered.extend(group)

        # Apply search
        if self.search_query:
            query_lower = self.search_query.lower()
            filtered = [
                t
                for t in filtered
                if query_lower in t.get("title", "").lower()
                or query_lower in t.get("artist", "").lower()
                or query_lower in t.get("albumTitle", "").lower()
            ]

        return filtered

    def toggle_selection(self, track_id: str):
        """Toggle selection state of a track."""
        if track_id in self.selected_ids:
            self.selected_ids.remove(track_id)
        else:
            self.selected_ids.add(track_id)

    def select_all_visible(self):
        """Select all currently visible (filtered) tracks."""
        filtered = self.get_filtered_tracks()
        for track in filtered:
            self.selected_ids.add(str(track.get("id")))

    def deselect_all(self):
        """Deselect all tracks."""
        self.selected_ids.clear()

    def find_and_cache_duplicates(self):
        """Find duplicates and cache them."""
        print("[DABHound] Searching for duplicates...")
        self.duplicate_groups = find_duplicates(self.tracks)

        # Build track-to-group mapping
        self.track_to_group = {}
        for group_idx, group in enumerate(self.duplicate_groups, 1):
            for track in group:
                track_id = str(track.get("id"))
                self.track_to_group[track_id] = group_idx

        return len(self.duplicate_groups)

    def run(self, stdscr):
        """Main TUI loop."""
        curses.curs_set(0)
        stdscr.keypad(True)
        stdscr.timeout(100)

        # Initialize colors
        try:
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_GREEN, -1)  # Selected
            curses.init_pair(2, curses.COLOR_CYAN, -1)  # Header
            curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Warning
            curses.init_pair(4, curses.COLOR_RED, -1)  # Error/Delete
            curses.init_pair(5, curses.COLOR_MAGENTA, -1)  # Duplicate
        except:
            pass

        while True:
            try:
                stdscr.clear()
                height, width = stdscr.getmaxyx()

                # Minimum size check
                if height < 15 or width < 60:
                    stdscr.addstr(0, 0, "Terminal too small! Resize to at least 60x15")
                    stdscr.refresh()
                    key = stdscr.getch()
                    if key in [ord("q"), ord("Q"), 27]:
                        break
                    continue

                if self.show_help:
                    self._render_help(stdscr, height, width)
                else:
                    self._render_main(stdscr, height, width)

                stdscr.refresh()
                key = stdscr.getch()

                if key == -1:  # Timeout
                    continue

                # Handle input
                if not self._handle_input(stdscr, key, height, width):
                    break  # User quit

            except KeyboardInterrupt:
                break
            except Exception as e:
                try:
                    stdscr.addstr(0, 0, f"Error: {str(e)[: width - 1]}")
                    stdscr.addstr(1, 0, "Press Q to quit")
                    stdscr.refresh()
                    stdscr.timeout(-1)
                    key = stdscr.getch()
                    if key in [ord("q"), ord("Q")]:
                        break
                except:
                    break

    def _render_main(self, stdscr, height, width):
        """Render main track list view."""
        filtered = self.get_filtered_tracks()

        # Header
        title = f"Library Manager - {self.library_name}"
        if len(title) > width - 1:
            title = title[: width - 4] + "..."
        stdscr.addstr(0, 0, title, curses.A_BOLD | curses.color_pair(2))

        lib_id = f"ID: {self.library_id}"
        if len(lib_id) > width - 1:
            lib_id = lib_id[: width - 4] + "..."
        stdscr.addstr(1, 0, lib_id)

        # Stats
        stats = f"Total: {len(self.tracks)} | Filtered: {len(filtered)} | Selected: {len(self.selected_ids)}"
        if self.duplicate_groups:
            stats += f" | Duplicates: {sum(len(g) for g in self.duplicate_groups)}"
        if len(stats) > width - 1:
            stats = stats[: width - 4] + "..."
        stdscr.addstr(2, 0, stats, curses.color_pair(3))

        # Filter/Search info
        filter_line = f"Filter: [{self.current_filter.upper()}]"
        if self.search_query:
            filter_line += f" | Search: '{self.search_query}'"
        if len(filter_line) > width - 1:
            filter_line = filter_line[: width - 4] + "..."
        stdscr.addstr(3, 0, filter_line)

        stdscr.addstr(4, 0, "-" * min(width - 1, 80))

        # Track list
        list_start = 5
        list_height = max(1, height - list_start - 6)

        max_scroll = max(0, len(filtered) - list_height)
        self.scroll_pos = max(0, min(self.scroll_pos, max_scroll))

        # Track current group in duplicates view
        current_group = None
        display_line = 0

        for track_idx in range(
            self.scroll_pos, min(self.scroll_pos + list_height, len(filtered))
        ):
            if display_line >= list_height:
                break

            track = filtered[track_idx]
            track_id = str(track.get("id"))
            is_selected = track_id in self.selected_ids

            # Check if we need to show group header (duplicates view only)
            if self.current_filter == "duplicates":
                group_num = self.track_to_group.get(track_id)
                if group_num and group_num != current_group:
                    # Show group header
                    y_pos = list_start + display_line
                    if y_pos < height - 5:
                        group_size = len(
                            [t for t in self.duplicate_groups[group_num - 1]]
                        )
                        header = f"--- Group {group_num} ({group_size} tracks) ---"
                        try:
                            stdscr.addstr(
                                y_pos,
                                0,
                                header[: width - 1],
                                curses.color_pair(3) | curses.A_BOLD,
                            )
                        except curses.error:
                            pass
                    display_line += 1
                    current_group = group_num

                    if display_line >= list_height:
                        break

            # Check if duplicate
            is_dup = track_id in self.track_to_group

            artist = track.get("artist", "Unknown")
            title = track.get("title", "Unknown")
            album = track.get("albumTitle", "")
            release_date = track.get("releaseDate", "")

            # Get audio quality info
            audio_quality = track.get("audioQuality", {})
            bit_depth = audio_quality.get("maximumBitDepth", 0)
            sample_rate = audio_quality.get("maximumSamplingRate", 0)
            is_hires = audio_quality.get("isHiRes", False)

            # Build single line with all info (Excel style)
            marker = "[X]" if is_selected else "[ ]"
            line = f"{marker} {artist} - {title}"

            # Add metadata inline with separators
            metadata = []

            if album:
                # Truncate album if too long
                album_short = album if len(album) <= 30 else album[:27] + "..."
                metadata.append(album_short)

            if release_date:
                # Extract year from date (format: YYYY-MM-DD)
                year = (
                    release_date.split("-")[0] if "-" in release_date else release_date
                )
                metadata.append(year)

            if bit_depth and sample_rate:
                quality_str = f"{bit_depth}bit/{sample_rate}kHz"
                if is_hires:
                    quality_str += "*"
                metadata.append(quality_str)

            # Append metadata to line with separator
            if metadata:
                line += " | " + " | ".join(metadata)

            # Truncate if needed
            max_len = width - 3
            if len(line) > max_len:
                line = line[: max_len - 3] + "..."

            y_pos = list_start + display_line

            # Determine color and attributes
            is_cursor = track_idx == self.cursor_pos

            if is_cursor:
                # Highlighted cursor position
                color = curses.A_REVERSE
            elif is_selected:
                # Selected track
                color = curses.color_pair(1)
            elif is_dup:
                # Duplicate track
                color = curses.color_pair(5)
            else:
                # Normal track
                color = 0

            # Draw line
            if y_pos < height - 5:
                try:
                    stdscr.addstr(y_pos, 0, line[: width - 1], color)
                except curses.error:
                    pass

            display_line += 1

        # Footer
        footer_y = height - 5
        if footer_y > list_start:
            stdscr.addstr(footer_y, 0, "-" * min(width - 1, 80))

            commands = [
                "[Space] Select | [A]ll [N]one | [F]ilter [/]Search",
                "[D]elete Sel | [E]xport JSON [C]SV | [U]Duplicates",
                "[H]elp | [Q]uit",
            ]

            for idx, cmd in enumerate(commands):
                y = footer_y + 1 + idx
                if y < height - 1:
                    if len(cmd) > width - 1:
                        cmd = cmd[: width - 4] + "..."
                    try:
                        stdscr.addstr(y, 0, cmd[: width - 1], curses.A_BOLD)
                    except curses.error:
                        pass

    def _render_help(self, stdscr, height, width):
        """Render help screen."""
        help_text = [
            "=== DABHounds Library Manager - Help ===",
            "",
            "Navigation:",
            "  Arrow Up/Down    - Scroll track list",
            "  Page Up/Down     - Scroll by page",
            "  Space            - Toggle selection of current track",
            "",
            "Selection:",
            "  A                - Select all visible tracks",
            "  N                - Deselect all tracks",
            "",
            "Filtering:",
            "  F                - Cycle filter (all/selected/duplicates)",
            "  /                - Enter search mode",
            "  Esc              - Clear search",
            "",
            "Actions:",
            "  D                - Delete selected tracks (with confirmation)",
            "  E                - Export selected to JSON",
            "  C                - Export selected to CSV",
            "  U                - Find/show duplicates",
            "",
            "Other:",
            "  H or ?           - Toggle this help",
            "  Q or Esc         - Quit library manager",
            "",
            "Press any key to return...",
        ]

        for i, line in enumerate(help_text):
            if i >= height - 1:
                break
            if len(line) > width - 1:
                line = line[: width - 4] + "..."
            try:
                stdscr.addstr(i, 0, line[: width - 1])
            except curses.error:
                pass

    def _handle_input(self, stdscr, key, height, width) -> bool:
        """
        Handle keyboard input.
        Returns False if user wants to quit, True otherwise.
        """
        if self.show_help:
            self.show_help = False
            return True

        # Quit
        if key in [ord("q"), ord("Q"), 27]:  # Q or Esc
            return False

        # Help
        elif key in [ord("h"), ord("H"), ord("?")]:
            self.show_help = True

        # Navigation
        elif key == curses.KEY_UP:
            filtered = self.get_filtered_tracks()
            if filtered:
                self.cursor_pos = max(0, self.cursor_pos - 1)
                # Auto-scroll up if cursor moves above visible area
                if self.cursor_pos < self.scroll_pos:
                    self.scroll_pos = self.cursor_pos
        elif key == curses.KEY_DOWN:
            filtered = self.get_filtered_tracks()
            if filtered:
                self.cursor_pos = min(len(filtered) - 1, self.cursor_pos + 1)
                # Ensure cursor is visible - more aggressive scrolling
                # In duplicates mode, we need extra room for group headers
                list_height = max(1, height - 5 - 6)
                # Keep cursor in middle third when scrolling down
                if self.cursor_pos >= self.scroll_pos + (list_height // 2):
                    self.scroll_pos = max(0, self.cursor_pos - (list_height // 2))
        elif key == curses.KEY_PPAGE:  # Page Up
            filtered = self.get_filtered_tracks()
            if filtered:
                self.cursor_pos = max(0, self.cursor_pos - 10)
                self.scroll_pos = max(0, self.scroll_pos - 10)
                # Ensure cursor stays in view
                if self.cursor_pos < self.scroll_pos:
                    self.scroll_pos = self.cursor_pos
        elif key == curses.KEY_NPAGE:  # Page Down
            filtered = self.get_filtered_tracks()
            if filtered:
                list_height = max(1, height - 5 - 6)
                self.cursor_pos = min(len(filtered) - 1, self.cursor_pos + 10)
                max_scroll = max(0, len(filtered) - list_height)
                self.scroll_pos = min(max_scroll, self.scroll_pos + 10)
                # Ensure cursor stays in view
                if self.cursor_pos >= self.scroll_pos + list_height:
                    self.scroll_pos = self.cursor_pos - list_height + 1

        # Selection
        elif key == ord(" "):  # Space - toggle current track
            filtered = self.get_filtered_tracks()
            if filtered and self.cursor_pos < len(filtered):
                track = filtered[self.cursor_pos]
                self.toggle_selection(str(track.get("id")))
        elif key in [ord("a"), ord("A")]:  # Select all visible
            self.select_all_visible()
        elif key in [ord("n"), ord("N")]:  # Deselect all
            self.deselect_all()

        # Filtering
        elif key in [ord("f"), ord("F")]:
            if self.current_filter == "all":
                self.current_filter = "selected"
            elif self.current_filter == "selected":
                self.current_filter = "duplicates" if self.duplicate_groups else "all"
            else:
                self.current_filter = "all"
            self.scroll_pos = 0
            self.cursor_pos = 0

        # Search
        elif key == ord("/"):
            self._enter_search_mode(stdscr, height, width)

        # Duplicates
        elif key in [ord("u"), ord("U")]:
            self._find_duplicates_action(stdscr, height, width)

        # Delete
        elif key in [ord("d"), ord("D")]:
            self._delete_selected_action(stdscr, height, width)

        # Export
        elif key in [ord("e"), ord("E")]:
            self._export_json_action(stdscr, height, width)
        elif key in [ord("c"), ord("C")]:
            self._export_csv_action(stdscr, height, width)

        return True

    def _enter_search_mode(self, stdscr, height, width):
        """Enter interactive search mode."""
        curses.echo()
        curses.curs_set(1)
        stdscr.timeout(-1)

        try:
            stdscr.addstr(height - 1, 0, "Search: " + " " * (width - 10))
            stdscr.addstr(height - 1, 0, "Search: ")
            stdscr.refresh()

            query = stdscr.getstr(height - 1, 8, width - 10).decode("utf-8")
            self.search_query = query.strip()
            self.scroll_pos = 0
            self.cursor_pos = 0
        except:
            pass
        finally:
            curses.noecho()
            curses.curs_set(0)
            stdscr.timeout(100)

    def _find_duplicates_action(self, stdscr, height, width):
        """Find duplicates and switch to duplicates filter."""
        stdscr.timeout(-1)
        try:
            stdscr.addstr(height - 1, 0, " " * (width - 1))
            stdscr.addstr(height - 1, 0, "Finding duplicates...", curses.color_pair(3))
            stdscr.refresh()

            count = self.find_and_cache_duplicates()

            if self.duplicate_groups:
                self.current_filter = "duplicates"
                self.scroll_pos = 0
                self.cursor_pos = 0
                # Show brief message without blocking
                msg = f"Found {len(self.duplicate_groups)} groups ({count} tracks)"
                stdscr.addstr(height - 1, 0, " " * (width - 1))
                stdscr.addstr(height - 1, 0, msg[: width - 1], curses.color_pair(1))
                stdscr.refresh()
            else:
                msg = "No duplicates found"
                stdscr.addstr(height - 1, 0, " " * (width - 1))
                stdscr.addstr(height - 1, 0, msg[: width - 1], curses.color_pair(3))
                stdscr.refresh()
        finally:
            stdscr.timeout(100)

    def _delete_selected_action(self, stdscr, height, width):
        """Delete selected tracks with confirmation."""
        if not self.selected_ids:
            self._show_message(
                stdscr, height, width, "No tracks selected!", curses.color_pair(3)
            )
            return

        stdscr.timeout(-1)
        try:
            # Confirmation
            msg = f"Delete {len(self.selected_ids)} tracks? (y/N): "
            stdscr.addstr(height - 1, 0, " " * (width - 1))
            stdscr.addstr(height - 1, 0, msg[: width - 1], curses.color_pair(4))
            stdscr.refresh()

            curses.echo()
            confirm = stdscr.getch()
            curses.noecho()

            if confirm not in [ord("y"), ord("Y")]:
                self._show_message(
                    stdscr, height, width, "Delete cancelled.", curses.color_pair(3)
                )
                return

            # Delete
            stdscr.addstr(height - 1, 0, " " * (width - 1))
            stdscr.addstr(height - 1, 0, "Deleting tracks...", curses.color_pair(3))
            stdscr.refresh()

            success, failed = delete_tracks_bulk(
                self.library_id, list(self.selected_ids)
            )

            # Remove deleted tracks from local list
            deleted_ids = self.selected_ids.copy()
            self.tracks = [
                t for t in self.tracks if str(t.get("id")) not in deleted_ids
            ]
            self.selected_ids.clear()

            # Rebuild duplicate groups if we were viewing them
            if self.duplicate_groups:
                # Remove deleted tracks from duplicate groups
                new_groups = []
                for group in self.duplicate_groups:
                    new_group = [
                        t for t in group if str(t.get("id")) not in deleted_ids
                    ]
                    # Only keep groups with 2+ tracks (still duplicates)
                    if len(new_group) >= 2:
                        new_groups.append(new_group)

                self.duplicate_groups = new_groups

                # Rebuild track-to-group mapping
                self.track_to_group = {}
                for group_idx, group in enumerate(self.duplicate_groups, 1):
                    for track in group:
                        track_id = str(track.get("id"))
                        self.track_to_group[track_id] = group_idx

            msg = f"Deleted {success} tracks. Failed: {failed}. Press any key..."
            self._show_message(stdscr, height, width, msg, curses.color_pair(1))
        finally:
            stdscr.timeout(100)

    def _export_json_action(self, stdscr, height, width):
        """Export selected tracks to JSON."""
        tracks_to_export = (
            [t for t in self.tracks if str(t.get("id")) in self.selected_ids]
            if self.selected_ids
            else self.tracks
        )

        if not tracks_to_export:
            self._show_message(
                stdscr, height, width, "No tracks to export!", curses.color_pair(3)
            )
            return

        stdscr.timeout(-1)
        try:
            output_path = (
                Path.home() / ".dabhound" / "exports" / f"{self.library_id}_export.json"
            )

            stdscr.addstr(height - 1, 0, " " * (width - 1))
            stdscr.addstr(height - 1, 0, "Exporting to JSON...", curses.color_pair(3))
            stdscr.refresh()

            if export_to_json(tracks_to_export, output_path, minimal=False):
                msg = f"Exported {len(tracks_to_export)} tracks to {output_path}. Press any key..."
                self._show_message(stdscr, height, width, msg, curses.color_pair(1))
            else:
                self._show_message(
                    stdscr, height, width, "Export failed!", curses.color_pair(4)
                )
        finally:
            stdscr.timeout(100)

    def _export_csv_action(self, stdscr, height, width):
        """Export selected tracks to CSV."""
        tracks_to_export = (
            [t for t in self.tracks if str(t.get("id")) in self.selected_ids]
            if self.selected_ids
            else self.tracks
        )

        if not tracks_to_export:
            self._show_message(
                stdscr, height, width, "No tracks to export!", curses.color_pair(3)
            )
            return

        stdscr.timeout(-1)
        try:
            output_path = (
                Path.home() / ".dabhound" / "exports" / f"{self.library_id}_export.csv"
            )

            stdscr.addstr(height - 1, 0, " " * (width - 1))
            stdscr.addstr(height - 1, 0, "Exporting to CSV...", curses.color_pair(3))
            stdscr.refresh()

            if export_to_csv(tracks_to_export, output_path):
                msg = f"Exported {len(tracks_to_export)} tracks to {output_path}. Press any key..."
                self._show_message(stdscr, height, width, msg, curses.color_pair(1))
            else:
                self._show_message(
                    stdscr, height, width, "Export failed!", curses.color_pair(4)
                )
        finally:
            stdscr.timeout(100)

    def _show_message(self, stdscr, height, width, message, color=0):
        """Show a message and wait for keypress."""
        stdscr.addstr(height - 1, 0, " " * (width - 1))
        stdscr.addstr(height - 1, 0, message[: width - 1], color)
        stdscr.addstr(height - 1, 0, message[: width - 1], color)
        stdscr.refresh()
        stdscr.getch()


def show_library_manager_tui(library_id: str, library_name: str, tracks: List[Dict]):
    """
    Launch interactive TUI for library management.

    Args:
        library_id: DAB library ID
        library_name: Library name
        tracks: List of track dictionaries
    """
    if not HAS_CURSES:
        print("[DABHound] Interactive TUI not available on this platform.")
        print("[DABHound] Use non-interactive mode instead.")
        return

    try:
        tui = LibraryTUI(library_id, library_name, tracks)
        curses.wrapper(tui.run)
    except Exception as e:
        print(f"[DABHound] TUI error: {e}")
