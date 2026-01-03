# 🎯 Library Manager - Quick Examples

## Basic Commands

### 1. List all your libraries
```bash
dabhounds --library-list
```

### 2. View library details (simple)
```bash
dabhounds --library-view abc123
```

### 3. View library details (interactive TUI)
```bash
dabhounds --library-view abc123 --interactive
```

---

## Export Commands

### 4. Export library to JSON
```bash
dabhounds --library-export abc123
```

### 5. Export library to CSV
```bash
dabhounds --library-export abc123 --format csv
```

### 6. Export to custom location
```bash
dabhounds --library-export abc123 --output ~/Downloads/my-playlist.json
```

---

## Duplicate Detection

### 7. Find duplicates (non-interactive)
```bash
dabhounds --library-duplicates abc123
```

### 8. Find duplicates (interactive - recommended)
```bash
dabhounds --library-duplicates abc123 --interactive
```

### 9. Find duplicates with lower threshold (more matches)
```bash
dabhounds --library-duplicates abc123 --dup-threshold 85
```

---

## Delete Tracks

### 10. Delete specific tracks
```bash
dabhounds --library-delete abc123 --track-ids "12345,12346,12347"
```

---

## Interactive TUI Workflows

### Workflow 1: Clean Duplicates
```bash
# 1. Open library in interactive mode
dabhounds --library-view abc123 --interactive

# 2. Inside TUI, press these keys:
#    U - Find duplicates
#    F - Switch to duplicates filter
#    Space - Select tracks to remove (navigate with arrows)
#    D - Delete selected tracks
#    y - Confirm deletion
#    Q - Quit
```

### Workflow 2: Export Searched Tracks
```bash
# 1. Open library in interactive mode
dabhounds --library-view abc123 --interactive

# 2. Inside TUI:
#    / - Enter search mode
#    Type "Beatles" - Search for Beatles tracks
#    A - Select all search results
#    E - Export to JSON
#    Q - Quit
```

### Workflow 3: Browse and Manage Library
```bash
# Open library interactively
dabhounds --library-view abc123 --interactive

# Navigation:
#   ↑/↓ - Scroll through tracks
#   Space - Select/deselect track
#   A - Select all visible
#   N - Deselect all
#   
# Filter:
#   F - Cycle through filters (all/selected/duplicates)
#   / - Search
#
# Actions:
#   E - Export selected to JSON
#   C - Export selected to CSV
#   D - Delete selected
#   U - Find duplicates
#   H - Show help
#   Q - Quit
```

---

## Advanced Use Cases

### 11. Find and remove all duplicates automatically
```bash
# Step 1: Find duplicates non-interactively and save output
dabhounds --library-duplicates abc123 > duplicates.txt

# Step 2: Review duplicates.txt manually

# Step 3: Use interactive mode to select and delete
dabhounds --library-duplicates abc123 --interactive
```

### 12. Backup library before cleanup
```bash
# Export full library first
dabhounds --library-export abc123 --output ~/backups/library-backup.json

# Then clean it up interactively
dabhounds --library-view abc123 --interactive
```

### 13. Search for specific artist and export
```bash
dabhounds --library-view abc123 --interactive
# Press '/' and type artist name
# Press 'A' to select all
# Press 'E' to export
```

---

## Tips & Tricks

💡 **Tip 1**: Always export your library before doing bulk deletions  
💡 **Tip 2**: Use `--dup-threshold 90-95` for most accurate duplicate detection  
💡 **Tip 3**: In TUI, use `F` filter to review only selected tracks before deletion  
💡 **Tip 4**: Search (`/`) is case-insensitive and searches title, artist, and album  
💡 **Tip 5**: Press `H` in TUI anytime to see full keyboard shortcuts  

---

## Combining with Playlist Conversion

```bash
# 1. Convert Spotify playlist to DAB
dabhounds https://open.spotify.com/playlist/xxxxx

# 2. Note the library ID from output

# 3. Review and clean up
dabhounds --library-view <library_id> --interactive

# 4. Find and remove duplicates
# Press 'U' in TUI

# 5. Export final clean library
# Press 'E' or 'C' in TUI
```

---

## Scripting Examples

### Bash Script: Export All Libraries
```bash
#!/bin/bash
# Save as export-all-libraries.sh

dabhounds --library-list | grep "ID:" | awk '{print $2}' | while read lib_id; do
    echo "Exporting library $lib_id..."
    dabhounds --library-export "$lib_id" --format json
done
```

### Bash Script: Find Duplicates in All Libraries
```bash
#!/bin/bash
# Save as check-all-duplicates.sh

dabhounds --library-list | grep "ID:" | awk '{print $2}' | while read lib_id; do
    echo "Checking duplicates in $lib_id..."
    dabhounds --library-duplicates "$lib_id" > "duplicates_${lib_id}.txt"
done
```

---

## Keyboard Shortcuts Reference (TUI)

| Category | Key | Action |
|----------|-----|--------|
| **Navigation** | ↑/↓ | Scroll up/down |
| | PgUp/PgDn | Scroll page |
| **Selection** | Space | Toggle selection |
| | A | Select all visible |
| | N | Deselect all |
| **Filtering** | F | Cycle filter mode |
| | / | Search |
| | Esc | Clear search |
| **Actions** | D | Delete selected |
| | E | Export JSON |
| | C | Export CSV |
| | U | Find duplicates |
| **Help** | H or ? | Show help |
| **Exit** | Q or Esc | Quit |

---

## Common Patterns

### Pattern 1: Weekly Library Cleanup
```bash
# Check for new duplicates
dabhounds --library-duplicates <lib_id> --interactive

# Inside TUI: U → F → Select → D
```

### Pattern 2: Migrate Library Data
```bash
# Export from DAB
dabhounds --library-export <lib_id> --format json

# Now you have a backup/portable format
```

### Pattern 3: Selective Track Removal
```bash
# Search and remove specific tracks
dabhounds --library-view <lib_id> --interactive

# Inside TUI: / → "unwanted" → A → D
```

---

## Need More Help?

- Read full documentation: `LIBRARY_MANAGER.md`
- Check main README: `README.md`
- Run `dabhounds --help`
- In TUI, press `H` for help
