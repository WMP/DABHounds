# Library Manager Feature - Changelog

## Added Files

### Core Modules
- `dabhounds/core/library_manager.py` - Core API for library operations
  - Functions for fetching library details and tracks
  - Delete operations (single and bulk)
  - Duplicate detection with ISRC and fuzzy matching
  - Export to JSON and CSV
  - List user libraries

- `dabhounds/core/library_tui.py` - Interactive TUI interface
  - Full-screen curses-based interface
  - Track selection and filtering
  - Search functionality
  - Real-time duplicate detection
  - Interactive delete with confirmation
  - Export selected tracks

- `dabhounds/core/library_cli.py` - Non-interactive CLI commands
  - `cmd_list_libraries()` - List all user libraries
  - `cmd_view_library()` - View library details
  - `cmd_export_library()` - Export library to file
  - `cmd_find_duplicates()` - Find and display duplicates
  - `cmd_delete_tracks()` - Delete tracks by ID

### Documentation
- `LIBRARY_MANAGER.md` - Complete documentation for the Library Manager
- `LIBRARY_MANAGER_EXAMPLES.md` - Quick examples and use cases
- `LIBRARY_MANAGER_CHANGELOG.md` - This file

## Modified Files

### `dabhounds/cli.py`
**Added imports:**
```python
from dabhounds.core.library_cli import (
    cmd_list_libraries,
    cmd_view_library,
    cmd_export_library,
    cmd_find_duplicates,
    cmd_delete_tracks
)
```

**Added CLI arguments:**
- `--library-list` - List all libraries
- `--library-view <id>` - View library details
- `--library-export <id>` - Export library
- `--library-duplicates <id>` - Find duplicates
- `--library-delete <id>` - Delete tracks
- `--interactive` - Enable interactive TUI mode
- `--format {json,csv}` - Export format selection
- `--output <path>` - Custom export path
- `--track-ids <ids>` - Comma-separated track IDs for deletion
- `--dup-threshold <0-100>` - Duplicate detection threshold

**Added command handlers in main():**
- Library list handler
- Library view handler (interactive and non-interactive)
- Library export handler
- Duplicate finder handler
- Track deletion handler

**Updated help menu:**
- Added "LIBRARY MANAGEMENT" section with all new commands
- Reorganized menu into logical sections:
  - PLAYLIST CONVERSION
  - LIBRARY MANAGEMENT
  - AUTHENTICATION
  - OTHER

## Features Summary

### Non-Interactive Mode
1. **List Libraries** - View all your DAB libraries with metadata
2. **View Library** - Display library details and first 10 tracks
3. **Export Library** - Save to JSON (full metadata) or CSV (basic fields)
4. **Find Duplicates** - Detect and display duplicate tracks
5. **Delete Tracks** - Remove specific tracks by ID

### Interactive Mode (TUI)
1. **Full Library Browser** - Navigate all tracks with arrow keys
2. **Track Selection** - Select/deselect individual or all tracks
3. **Filtering** - View all/selected/duplicate tracks
4. **Search** - Find tracks by title, artist, or album
5. **Export Selected** - Export only selected tracks
6. **Delete Selected** - Remove selected tracks with confirmation
7. **Duplicate Management** - Find, review, and remove duplicates
8. **Keyboard Shortcuts** - Full keyboard-driven interface

### Duplicate Detection
- **ISRC Matching** - Exact matches via ISRC codes
- **Fuzzy Matching** - RapidFuzz-based similarity on artist + title
- **Configurable Threshold** - Adjust sensitivity (default: 95%)
- **Grouped Results** - Duplicates displayed in groups

### Export Formats
**JSON:**
- Full track metadata
- Audio quality information
- Album details, ISRC, duration, release date
- All available fields from DAB API

**CSV:**
- Track ID, title, artist
- Album title
- ISRC, duration, release date
- Suitable for spreadsheet analysis

## API Endpoints Used

- `GET /api/libraries` - List user libraries
- `GET /api/libraries/{id}` - Get library metadata
- `GET /api/libraries/{id}/tracks` - Get all tracks in library
- `DELETE /api/libraries/{id}/tracks/{track_id}` - Delete a track

## Technical Details

### Dependencies
No new dependencies required. Uses existing DABHounds dependencies:
- `requests` - API communication
- `rapidfuzz` - Fuzzy matching
- `curses` - Interactive TUI (optional, with fallback)

### Code Structure
- **Modular Design** - Separate modules for API, TUI, and CLI
- **Backward Compatible** - No changes to existing functionality
- **Error Handling** - Graceful degradation (TUI → terminal fallback)
- **Rate Limiting** - Respects DAB API rate limits
- **Authentication** - Uses existing auth system

### Merge-Friendly Design
- All new code in separate files (no inline modifications)
- Minimal changes to `cli.py` (only imports and argument parsing)
- No modifications to existing core modules
- Independent feature that can be easily merged or removed

## Testing

All modules tested for:
- ✅ Python compilation
- ✅ Import resolution
- ✅ CLI argument parsing
- ✅ Help menu display
- ✅ Module independence

## Usage Examples

### List libraries
```bash
dabhounds --library-list
```

### View library interactively
```bash
dabhounds --library-view abc123 --interactive
```

### Find and export duplicates
```bash
dabhounds --library-duplicates abc123 --interactive
```

### Export to CSV
```bash
dabhounds --library-export abc123 --format csv
```

### Delete specific tracks
```bash
dabhounds --library-delete abc123 --track-ids "id1,id2,id3"
```

## Future Enhancements (Ideas)

- [ ] Batch operations on multiple libraries
- [ ] Smart duplicate resolution (keep highest quality)
- [ ] Library merge functionality
- [ ] Track metadata editing
- [ ] Playlist reordering in TUI
- [ ] Export to M3U/other playlist formats
- [ ] Library statistics and analytics
- [ ] Backup/restore functionality

## Notes

- Interactive TUI requires terminal with curses support (Linux, macOS, WSL)
- All operations require DAB authentication (`--login`)
- Deletion operations are irreversible (confirmation required)
- Export locations default to `~/.dabhound/exports/`
- Compatible with existing DABHounds workflow

## License

Same as DABHounds: GNU Affero General Public License v3.0
