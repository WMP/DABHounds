# Library Management Feature

## Overview
This PR adds comprehensive library management functionality to DABHounds, allowing users to view, manage, export, and clean up their DAB libraries through both interactive (TUI) and non-interactive (CLI) modes.

## Features

### 🎯 Core Functionality
- **View Library Contents**: Browse all tracks in a library with detailed metadata
- **Interactive TUI Mode**: Full-screen curses-based interface for browsing and managing tracks
- **Non-Interactive CLI**: Command-line options for scripting and automation
- **Smart Caching**: 1-hour TTL cache system for fast repeated operations
- **Pagination Support**: Handles large libraries (tested with 300+ tracks)

### 🔍 Track Information Display
Each track shows:
- Artist and Title
- Album name
- Release year
- Audio quality (bit depth/sample rate)
- Hi-Res indicator (*)
- Single-line Excel-style format for efficient space usage

### 🎨 Interactive Features
- **Arrow Key Navigation**: Move cursor through track list
- **Auto-Scrolling**: Keeps cursor visible, handles duplicate group headers
- **Track Selection**: Space to toggle, A to select all, N to deselect all
- **Filtering**: Cycle through all/selected/duplicates views
- **Search**: Real-time search by artist/title/album
- **Duplicate Detection**: ISRC + fuzzy matching (RapidFuzz)
- **Bulk Operations**: Delete, export selected or all tracks

### 🔧 Duplicate Management
- ISRC-based exact matching
- Fuzzy matching with configurable threshold (default 95%)
- Visual grouping with headers
- Color-coded display (magenta)
- Automatic group cleanup after deletion

### 📦 Export Options
- **JSON**: Full metadata or minimal format
- **CSV**: Spreadsheet-compatible format
- Exports to `~/.dabhound/exports/`

### 🚀 Library Discovery
- List all user libraries
- Search by library name (exact or partial match)
- Interactive library picker

## Usage Examples

### Interactive Mode

```bash
# Pick library interactively
python -m dabhounds.cli --interactive

# Open specific library by name
python -m dabhounds.cli --interactive --library-name "My Playlist"

# Find duplicates interactively
python -m dabhounds.cli --library-duplicates LIBRARY_ID --interactive
```

### Non-Interactive Mode

```bash
# List all libraries
python -m dabhounds.cli --library-list

# View library details
python -m dabhounds.cli --library-view LIBRARY_ID

# Export to JSON
python -m dabhounds.cli --library-export LIBRARY_ID --format json --output tracks.json

# Find duplicates (threshold 90%)
python -m dabhounds.cli --library-duplicates LIBRARY_ID --dup-threshold 90

# Delete specific tracks
python -m dabhounds.cli --library-delete LIBRARY_ID --track-ids "123,456,789"
```

## Interactive TUI Controls

| Key | Action |
|-----|--------|
| `↑`/`↓` | Navigate tracks |
| `PgUp`/`PgDn` | Page up/down |
| `Space` | Toggle selection |
| `A` | Select all visible |
| `N` | Deselect all |
| `F` | Cycle filter (all/selected/duplicates) |
| `/` | Search mode |
| `Esc` | Clear search |
| `U` | Find/show duplicates |
| `D` | Delete selected (with confirmation) |
| `E` | Export to JSON |
| `C` | Export to CSV |
| `H` or `?` | Toggle help |
| `Q` or `Esc` | Quit |

## Technical Details

### New Files
- `dabhounds/core/library_manager.py` - Core API operations, caching, duplicate detection
- `dabhounds/core/library_tui.py` - Interactive TUI using curses
- `dabhounds/core/library_cli.py` - Non-interactive CLI commands
- `LIBRARY_MANAGER.md` - Complete documentation
- `LIBRARY_MANAGER_EXAMPLES.md` - Usage examples
- `LIBRARY_MANAGER_CHANGELOG.md` - Technical changelog

### Modified Files
- `dabhounds/cli.py` - Integrated library management arguments
- `dabhounds/core/auth.py` - Added session getter for library operations
- `dabhounds/core/library.py` - Minor refactoring

### Dependencies
- `rapidfuzz` - Fuzzy string matching for duplicate detection

### Cache System
- Location: `~/.dabhound/cache/`
- Format: `library_{id}.json`
- TTL: 1 hour
- Auto-invalidation on delete operations

### API Pagination
Handles DAB API pagination correctly:
- Fetches 20 tracks per page
- Continues until `pagination.hasMore = false`
- Progress indication during fetch
- Tested with libraries of 300+ tracks

## Performance

**Without cache** (322 tracks):
- ~17 API calls
- ~15 seconds initial load

**With cache**:
- 0 API calls
- <1 second load time

## Testing

Tested scenarios:
- ✅ Large libraries (322 tracks)
- ✅ Pagination handling
- ✅ Duplicate detection (19 groups, 40 tracks)
- ✅ Track deletion and cache invalidation
- ✅ Group header display and scrolling
- ✅ Arrow key navigation with auto-scroll
- ✅ Duplicate group cleanup after deletion
- ✅ Search and filtering
- ✅ JSON/CSV export

## Merge Strategy

This PR is designed to be merge-friendly:
- No breaking changes to existing code
- All functionality is additive
- Works with both accepted and non-accepted feature branches
- Separate modules for easy code review

## Documentation

Comprehensive documentation included:
- User guide (`LIBRARY_MANAGER.md`)
- Usage examples (`LIBRARY_MANAGER_EXAMPLES.md`)
- Technical changelog (`LIBRARY_MANAGER_CHANGELOG.md`)

## Future Enhancements

Potential improvements:
- [ ] Batch export multiple libraries
- [ ] Advanced filtering (by quality, date range)
- [ ] Track statistics and analytics
- [ ] Playlist creation from selection
- [ ] Integration with sync operations

## Commits

12 commits implementing the feature incrementally:
1. Initial comprehensive library management functionality
2. Pagination support for large libraries
3. Caching system with 1-hour TTL
4. Duplicate detection with visual grouping
5. Library search by name
6. Interactive library picker
7. Duplicate group display improvements
8. Detailed track metadata display
9. Single-line Excel-style format
10. Arrow key navigation implementation
11. Improved scrolling for duplicate headers
12. Duplicate group cleanup after deletion

## Breaking Changes

None. All changes are backward compatible.

## Screenshots

See attached screenshots showing:
- Interactive library browser
- Duplicate detection with grouping
- Track selection and metadata display
- Color-coded interface
