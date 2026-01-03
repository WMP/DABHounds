# 📚 DABHounds Library Manager

The Library Manager is a powerful feature for managing your DAB libraries directly from the command line. It supports both **interactive** (TUI-based) and **non-interactive** modes.

---

## 🚀 Features

- **List Libraries**: View all your DAB libraries
- **View Library Details**: Browse tracks with full metadata
- **Interactive TUI**: Manage libraries with keyboard-driven interface
- **Export**: Save library tracks to JSON or CSV
- **Find Duplicates**: Detect duplicate tracks using ISRC or fuzzy matching
- **Delete Tracks**: Remove tracks from libraries (bulk or selective)
- **Filter & Search**: Find tracks by artist, title, or album
- **Select/Deselect**: Mark tracks for batch operations

---

## 📖 Usage

### List All Libraries

```bash
dabhounds --library-list
```

Shows all your DAB libraries with IDs, track counts, and visibility status.

---

### View Library (Non-Interactive)

```bash
dabhounds --library-view <library_id>
```

Displays library details and the first 10 tracks. Perfect for quick checks.

**Example:**
```bash
dabhounds --library-view 12345
```

---

### View Library (Interactive TUI)

```bash
dabhounds --library-view <library_id> --interactive
```

Launches a full-screen interactive interface where you can:
- Browse all tracks with arrow keys
- Select/deselect tracks with `Space`
- Filter by status (all/selected/duplicates)
- Search tracks with `/`
- Export selected tracks
- Delete selected tracks
- Find and manage duplicates

**TUI Keyboard Shortcuts:**
| Key | Action |
|-----|--------|
| `↑`/`↓` | Scroll track list |
| `PgUp`/`PgDn` | Scroll by page |
| `Space` | Toggle track selection |
| `A` | Select all visible tracks |
| `N` | Deselect all tracks |
| `F` | Cycle filter (all/selected/duplicates) |
| `/` | Enter search mode |
| `Esc` | Clear search |
| `D` | Delete selected tracks (with confirmation) |
| `E` | Export selected to JSON |
| `C` | Export selected to CSV |
| `U` | Find/show duplicates |
| `H` or `?` | Show help |
| `Q` or `Esc` | Quit |

---

### Export Library

```bash
# Export to JSON (default)
dabhounds --library-export <library_id>

# Export to CSV
dabhounds --library-export <library_id> --format csv

# Custom output path
dabhounds --library-export <library_id> --output ~/my-library.json
```

**Default export location:** `~/.dabhound/exports/`

**JSON format includes:**
- Full track metadata
- Audio quality information
- Album details
- ISRC codes

**CSV format includes:**
- Track ID, title, artist
- Album title
- ISRC, duration, release date

---

### Find Duplicates

```bash
# Non-interactive (prints duplicate groups)
dabhounds --library-duplicates <library_id>

# Interactive (opens TUI with duplicates filter)
dabhounds --library-duplicates <library_id> --interactive

# Adjust similarity threshold (default: 95%)
dabhounds --library-duplicates <library_id> --dup-threshold 85
```

**How duplicates are detected:**
1. **Exact ISRC match** (highest priority)
2. **Fuzzy matching** on artist + title (using RapidFuzz)

The threshold controls fuzzy matching sensitivity (0-100). Higher = stricter.

---

### Delete Tracks

```bash
dabhounds --library-delete <library_id> --track-ids "id1,id2,id3"
```

**Example:**
```bash
dabhounds --library-delete 12345 --track-ids "789,790,791"
```

⚠️ **Note:** Deletion requires confirmation and is **irreversible**.

**Tip:** Use the interactive TUI to select tracks visually, then delete them with the `D` key.

---

## 🎯 Workflow Examples

### Example 1: Clean up duplicates interactively

```bash
# Open library in interactive mode
dabhounds --library-view 12345 --interactive

# Inside TUI:
# 1. Press 'U' to find duplicates
# 2. Press 'F' to switch to duplicates filter
# 3. Review duplicates and press Space to select tracks to remove
# 4. Press 'D' to delete selected tracks
# 5. Confirm deletion
```

### Example 2: Export selected tracks

```bash
# Open library in interactive mode
dabhounds --library-view 12345 --interactive

# Inside TUI:
# 1. Press '/' to search for tracks (e.g., "Taylor Swift")
# 2. Press 'A' to select all matching tracks
# 3. Press 'E' to export to JSON (or 'C' for CSV)
```

### Example 3: Batch delete by track IDs

```bash
# List library to find track IDs
dabhounds --library-view 12345

# Delete specific tracks
dabhounds --library-delete 12345 --track-ids "100,101,102"
```

### Example 4: Export entire library to CSV

```bash
dabhounds --library-export 12345 --format csv --output ~/music/my-library.csv
```

---

## 🔧 Advanced Features

### Search Functionality (Interactive Mode)

Press `/` in the TUI to enter search mode. The search is **case-insensitive** and matches:
- Track title
- Artist name
- Album title

**Example:** Searching for `"remix"` will find all remixes in your library.

### Filter Modes (Interactive Mode)

Press `F` to cycle through filter modes:
- **All**: Show all tracks
- **Selected**: Show only selected tracks
- **Duplicates**: Show only duplicate tracks (requires running duplicate detection first)

### Bulk Operations

1. Use filters and search to narrow down tracks
2. Press `A` to select all visible tracks
3. Perform batch export or deletion

---

## 📁 File Locations

- **Config:** `~/.dabhound/config.json`
- **Exports:** `~/.dabhound/exports/`
- **Reports:** `~/.dabhound/reports/`

---

## 🛠️ Technical Details

### Architecture

The Library Manager consists of three modules:

1. **`library_manager.py`**: Core API for DAB library operations
   - `get_library_details()`: Fetch library metadata
   - `get_library_tracks()`: Fetch all tracks
   - `delete_track_from_library()`: Delete single track
   - `find_duplicates()`: Detect duplicates
   - `export_to_json()`, `export_to_csv()`: Export functions

2. **`library_tui.py`**: Interactive TUI (curses-based)
   - Full-screen interface with selection, filtering, search
   - Real-time track management
   - Keyboard-driven workflow

3. **`library_cli.py`**: Non-interactive CLI commands
   - Simple command-line operations
   - Scriptable and automation-friendly

### API Endpoints Used

- `GET /api/libraries` - List user libraries
- `GET /api/libraries/{id}` - Get library details
- `GET /api/libraries/{id}/tracks` - Get library tracks
- `DELETE /api/libraries/{id}/tracks/{track_id}` - Delete track

### Dependencies

All dependencies are already included in DABHounds:
- `requests` - API calls
- `rapidfuzz` - Fuzzy matching for duplicates
- `curses` - Interactive TUI (optional, fallback available)

---

## ⚠️ Important Notes

- **Authentication required**: You must be logged in with `dabhounds --login`
- **Deletion is irreversible**: Always double-check before confirming
- **Rate limits**: The API respects DAB's rate limits automatically
- **Platform compatibility**: TUI requires terminal with curses support (works on Linux, macOS, WSL)

---

## 🐛 Troubleshooting

### TUI not working?

If you see "TUI not available on this platform":
- Use non-interactive mode instead
- Check if your terminal supports curses
- On Windows, use WSL or Windows Terminal

### Library not found?

- Verify the library ID with `--library-list`
- Ensure you're logged in with the correct account
- Check that the library still exists on DABMusic

### Export failed?

- Ensure the output directory exists or is writable
- Check available disk space
- Verify you have tracks in the library

---

## 📝 License

Same as DABHounds: **GNU Affero General Public License v3.0**

---

## 🙏 Credits

Library Manager developed as an extension to DABHounds.

Original DABHounds by: **sherlockholmesat221b**  
Special thanks to: **superadmin0, uimaxbai, joehacks, Squid.WTF**
