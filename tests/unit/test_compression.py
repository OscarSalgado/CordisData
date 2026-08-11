"""Tests for JSONL.GZ compression utilities."""

import json
import tempfile
import time
from pathlib import Path

from cordis_data.utils.compression import JSONLGzipReader, JSONLGzipWriter


class TestJSONLGzipWriter:
    """Tests for JSONLGzipWriter."""

    def test_write_records_creates_file(self) -> None:
        """Test that writing records creates a .jsonl.gz file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl.gz"
            records = [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ]
            writer = JSONLGzipWriter(path)
            writer.write_records(records)

            assert path.exists()
            assert writer.records_written == 2

    def test_utf8_normalization(self) -> None:
        """Test that UTF-8 strings are normalized to NFC form."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl.gz"
            # Combining diacritics (e-acute) vs precomposed (é)
            records = [
                {"text": "café"},  # Precomposed
                {"text": "résumé"},  # Precomposed
                {"text": "naïve"},  # Precomposed
            ]
            writer = JSONLGzipWriter(path, normalize_utf8=True)
            writer.write_records(records)

            # Read back and verify normalization
            reader = JSONLGzipReader(path)
            read_records = reader.read_all()
            assert len(read_records) == 3
            assert read_records[0]["text"] == "café"

    def test_compression_ratio(self) -> None:
        """Test compression ratio calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl.gz"
            # Create records with repetitive data (compresses well)
            records = [
                {"id": i, "name": "Test" * 100, "data": "x" * 1000}
                for i in range(10)
            ]
            writer = JSONLGzipWriter(path)
            writer.write_records(records)

            # Estimate original size
            original_size = sum(len(json.dumps(r).encode("utf-8")) + 1 for r in records)
            ratio = writer.compression_ratio(original_size)
            # Repetitive data should compress to < 50%
            assert ratio < 50

    def test_writes_to_new_directory(self) -> None:
        """Test that writer creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "deep" / "test.jsonl.gz"
            records = [{"id": 1}]
            writer = JSONLGzipWriter(path)
            writer.write_records(records)

            assert path.parent.exists()
            assert path.exists()

    def test_special_unicode_characters(self) -> None:
        """Test handling of special Unicode characters from EU documents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl.gz"
            records = [
                {"text": "€100 million"},  # Euro symbol
                {"text": "50° angle"},  # Degree symbol
                {"text": "en–dash"},  # En-dash
                {"text": ""quoted text""},  # Smart quotes
                {"text": "first²"},  # Superscript
            ]
            writer = JSONLGzipWriter(path)
            writer.write_records(records)

            reader = JSONLGzipReader(path)
            read_records = reader.read_all()
            assert len(read_records) == 5
            assert "€" in read_records[0]["text"]
            assert "°" in read_records[1]["text"]


class TestJSONLGzipReader:
    """Tests for JSONLGzipReader."""

    def test_read_all_records(self) -> None:
        """Test reading all records at once."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl.gz"
            original = [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
                {"id": 3, "name": "Charlie"},
            ]
            writer = JSONLGzipWriter(path)
            writer.write_records(original)

            reader = JSONLGzipReader(path)
            read = reader.read_all()
            assert read == original

    def test_read_records_streaming(self) -> None:
        """Test streaming record iteration without loading all to memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl.gz"
            records = [{"id": i} for i in range(100)]
            writer = JSONLGzipWriter(path)
            writer.write_records(records)

            reader = JSONLGzipReader(path)
            count = 0
            for record in reader.read_records():
                count += 1
                assert "id" in record
            assert count == 100

    def test_count_records(self) -> None:
        """Test counting records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl.gz"
            records = [{"id": i} for i in range(50)]
            writer = JSONLGzipWriter(path)
            writer.write_records(records)

            reader = JSONLGzipReader(path)
            assert reader.count_records() == 50

    def test_read_uncompressed_jsonl(self) -> None:
        """Test reading uncompressed .jsonl files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl"
            records = [
                {"id": 1, "value": "first"},
                {"id": 2, "value": "second"},
            ]
            # Write uncompressed JSONL manually
            with open(path, "w", encoding="utf-8") as f:
                for record in records:
                    f.write(json.dumps(record) + "\n")

            # Reader should handle it
            reader = JSONLGzipReader(path)
            read = reader.read_all()
            assert len(read) == 2
            assert read[0]["id"] == 1

    def test_file_not_found_error(self) -> None:
        """Test that missing file raises FileNotFoundError."""
        path = Path("/nonexistent/path/file.jsonl.gz")
        try:
            JSONLGzipReader(path)
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass

    def test_round_trip_integrity(self) -> None:
        """Test that data survives write → read cycle intact."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl.gz"
            original = [
                {
                    "id": i,
                    "text": f"Record {i}",
                    "nested": {"key": "value"},
                    "list": [1, 2, 3],
                    "float": 3.14159,
                }
                for i in range(10)
            ]
            writer = JSONLGzipWriter(path, normalize_utf8=True)
            writer.write_records(original)

            reader = JSONLGzipReader(path)
            read = reader.read_all()

            assert len(read) == len(original)
            for orig, read_rec in zip(original, read):
                assert orig == read_rec


class TestCompressionPerformance:
    """Performance tests for compression."""

    def test_decompression_speed(self) -> None:
        """Test that decompression of 8.5MB equivalent is fast."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl.gz"
            # Create ~629 records similar to real calls data
            records = []
            for i in range(629):
                records.append(
                    {
                        "reference": f"REF-{i:06d}",
                        "topicId": f"TOPIC-{i}",
                        "title": "Sample call title " * 10,
                        "programme": "Horizon Europe",
                        "description": "Sample description " * 50,
                    }
                )
            writer = JSONLGzipWriter(path)
            writer.write_records(records)

            # Time decompression
            reader = JSONLGzipReader(path)
            start = time.time()
            all_records = reader.read_all()
            elapsed = time.time() - start

            # Should decompress in < 100ms (target is ~17ms)
            assert elapsed < 0.1
            assert len(all_records) == 629
