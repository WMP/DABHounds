## Summary

Adds comprehensive library management to DABHounds with both interactive TUI and CLI modes.

**Stats**: +2,584 lines across 9 files | 12 commits | 0 breaking changes

## Key Features

✨ **Interactive TUI Mode** - Full curses-based interface with arrow key navigation
📋 **Library Browser** - View all tracks with metadata (album, year, quality)
🔍 **Duplicate Detection** - ISRC + fuzzy matching with visual grouping
📦 **Export** - JSON/CSV export functionality
💾 **Smart Caching** - 1-hour TTL cache (15s → <1s for 300+ tracks)
🎯 **Bulk Operations** - Select, delete, export multiple tracks
🔎 **Search & Filter** - Real-time search, filter by selected/duplicates

## Quick Start

```bash
# Interactive library picker
python -m dabhounds.cli --interactive

# Find duplicates in library
python -m dabhounds.cli --library-duplicates LIBRARY_ID --interactive

# Export library to JSON
python -m dabhounds.cli --library-export LIBRARY_ID --format json
```

## What's New

- 3 new modules: `library_manager.py`, `library_tui.py`, `library_cli.py`
- 3 documentation files with complete guides and examples
- Full pagination support for large libraries
- Auto-scrolling with smart cursor positioning
- Duplicate group cleanup after deletion
- Single-line Excel-style track display

## Testing

Extensively tested with:
- Libraries with 300+ tracks
- Pagination (20 tracks/page)
- 19 duplicate groups (40 tracks)
- All interactive operations
- Cache invalidation

See `LIBRARY_MANAGER.md` for complete documentation.
