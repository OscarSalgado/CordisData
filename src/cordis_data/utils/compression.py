"""JSONL.GZ compression utilities for efficient data storage."""

import gzip
import json
import unicodedata
from pathlib import Path
from typing import Any, Generator, Iterator, Optional


class JSONLGzipWriter:
    """Write JSON records to JSONL.GZ format (one record per line, gzip compressed)."""

    def __init__(self, path: Path | str, normalize_utf8: bool = True) -> None:
        """Initialize writer.

        Args:
            path: Output file path (should end with .jsonl.gz)
            normalize_utf8: If True, normalize all strings to NFC form
        """
        self.path = Path(path)
        self.normalize_utf8 = normalize_utf8
        self.bytes_written = 0
        self.records_written = 0

    def write_records(self, records: list[dict[str, Any]]) -> None:
        """Write multiple records to JSONL.GZ file.

        Args:
            records: List of dict records to write
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with gzip.open(self.path, "wt", encoding="utf-8") as f:
            for record in records:
                normalized = self._normalize_record(record) if self.normalize_utf8 else record
                line = json.dumps(normalized, separators=(",", ":"), ensure_ascii=False)
                f.write(line + "\n")
                self.bytes_written += len(line.encode("utf-8")) + 1
                self.records_written += 1

    def _normalize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Recursively normalize all string values to NFC form.

        Args:
            record: Dict record to normalize

        Returns:
            Record with all strings normalized to NFC
        """
        normalized = {}
        for key, val in record.items():
            if isinstance(val, str):
                normalized[key] = unicodedata.normalize("NFC", val)
            elif isinstance(val, dict):
                normalized[key] = self._normalize_record(val)
            elif isinstance(val, list):
                normalized[key] = [
                    unicodedata.normalize("NFC", item) if isinstance(item, str) else item
                    for item in val
                ]
            else:
                normalized[key] = val
        return normalized

    def compression_ratio(self, original_size: int) -> float:
        """Calculate compression ratio.

        Args:
            original_size: Original size in bytes before compression

        Returns:
            Compression ratio as percentage (0-100)
        """
        if original_size == 0:
            return 0.0
        return (self.bytes_written / original_size) * 100


class JSONLGzipReader:
    """Read JSON records from JSONL.GZ format (one record per line)."""

    def __init__(self, path: Path | str) -> None:
        """Initialize reader.

        Args:
            path: Input file path (.jsonl.gz or .jsonl)
        """
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {self.path}")

    def read_all(self) -> list[dict[str, Any]]:
        """Read all records into memory.

        Returns:
            List of dict records
        """
        return list(self.read_records())

    def read_records(self) -> Generator[dict[str, Any], None, None]:
        """Iterate over records line-by-line.

        Yields:
            Dict record from each line
        """
        # Determine if file is gzipped based on extension
        is_gzipped = str(self.path).endswith(".gz")

        if is_gzipped:
            with gzip.open(self.path, "rt", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if line:
                        yield json.loads(line)
        else:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if line:
                        yield json.loads(line)

    def count_records(self) -> int:
        """Count total records in file without loading all to memory.

        Returns:
            Number of records
        """
        count = 0
        for _ in self.read_records():
            count += 1
        return count
