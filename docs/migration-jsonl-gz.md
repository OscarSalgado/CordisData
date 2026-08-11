# Migration Guide: JSON to JSONL.GZ Format

## Overview

CordisData has migrated from large monolithic JSON files to compressed JSONL.GZ format for improved performance and reduced storage.

**Benefits:**
- 85% reduction in file size (55MB → ~8MB for closed calls)
- Faster decompression (~17ms)
- UTF-8 normalization for better compatibility
- Organized directory structure by dataset

## Automatic Migration

**The migration happens automatically** on the next fetch with the new version:

```bash
cordis-data fetch-calls
cordis-data monitor fetch
```

When you run these commands:
1. The system detects old `data/calls.*.json` files
2. Converts them to the new `data/calls/*/jsonl.gz` format
3. Archives old files as `*.json.bak` for safety
4. Writes everything in the new format going forward

## Old vs. New Paths

| Data | Old Path | New Path |
|------|----------|----------|
| Open calls | `data/calls.open.json` | `data/calls/open.jsonl.gz` |
| Closed calls | `data/calls.closed.json` | `data/calls/closed.jsonl.gz` |
| Committee docs | `data/committees/documents.json` | `data/committees/documents.jsonl.gz` |
| Changelog (open) | `data/changelog/open/` | `data/calls/changelog/open/` |
| Changelog (closed) | `data/changelog/closed/` | `data/calls/changelog/closed/` |
| Changelog (committees) | `data/committees/changelog/` | `data/committees/changelog/` |

## Reading the New Format

### Python

```python
from cordis_data.utils.compression import JSONLGzipReader

# Load all records
reader = JSONLGzipReader("data/calls/open.jsonl.gz")
calls = reader.read_all()

# Or stream line-by-line (memory efficient for large files)
for call in reader.read_records():
    print(call['title'])
```

### Command Line

```bash
# Decompress and view
gunzip -c data/calls/open.jsonl.gz | head -1 | jq .

# Count records
gunzip -c data/calls/open.jsonl.gz | wc -l

# Search for specific calls
gunzip -c data/calls/open.jsonl.gz | jq 'select(.title | contains("Horizon"))'
```

### Other Languages

Any tool that can decompress gzip and parse JSON will work:

```bash
# Node.js
gunzip -c data/calls/open.jsonl.gz | while IFS= read -r line; do echo "$line" | jq . ; done

# PHP
$lines = file("compress.zlib://data/calls/open.jsonl.gz");
foreach ($lines as $line) {
    $call = json_decode($line);
    // use $call
}
```

## Cleanup (After Verification)

After running the new version for 1-2 fetch cycles and confirming everything works:

```bash
# Safe to delete backup files
rm data/calls.*.json.bak
```

**Do NOT delete `.bak` files immediately** — keep them for at least one successful fetch cycle to ensure no data loss.

## Rollback (If Needed)

If you encounter issues:

```bash
# Restore from backup
cp data/calls.open.json.bak data/calls.open.json
cp data/calls.closed.json.bak data/calls.closed.json

# Then run with previous version
```

## Troubleshooting

### "File not found: data/calls/closed.jsonl.gz"

This means the old format hasn't been migrated yet. Run:
```bash
cordis-data fetch-calls --force
```

Or manually migrate old files:
```python
from cordis_data.utils.compression import JSONLGzipWriter
import json

with open('data/calls.closed.json') as f:
    data = json.load(f)

writer = JSONLGzipWriter('data/calls/closed.jsonl.gz')
writer.write_records(data)
```

### Garbled characters in decompressed file

This shouldn't happen with the new version — UTF-8 is normalized to NFC form.

If you see characters like "M-bM-^@M-^Y", it's likely the old JSON files being read with incorrect encoding. Ensure you're using the new format.

### File size not reduced

JSONL.GZ achieves maximum compression with repetitive data. File sizes may vary:
- **Closed calls**: 55MB → ~8-12MB (85%+)
- **Open calls**: 8.5MB → ~1.5MB (80%+)
- **Committee docs**: Size depends on volume

## FAQ

**Q: Why JSONL.GZ instead of Parquet or SQLite?**
A: JSONL preserves JSON compatibility and tooling. Gzip compression is excellent for repetitive structured data. Simple and no additional dependencies needed.

**Q: Can I use this with my existing code?**
A: Update your file paths:
- `data/calls.open.json` → `data/calls/open.jsonl.gz`
- `data/calls.closed.json` → `data/calls/closed.jsonl.gz`

Use `JSONLGzipReader` instead of `json.load()`.

**Q: Is this a breaking change?**
A: Yes, the file paths changed. Update your code to use the new paths. The CLI and library functions handle the change transparently.

**Q: Do changelogs change format too?**
A: No, changelogs remain JSON (not compressed) for easier inspection and version control.

## Support

For issues or questions about the migration, see the GitHub issues or CLAUDE.md.
