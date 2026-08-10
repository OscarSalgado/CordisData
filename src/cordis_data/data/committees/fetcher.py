"""Fetch and track committee documents with change detection."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from cordis_data.data.changelog import ChangeEvent
from cordis_data.data.committees.client import CommitteeDocumentsClient
from cordis_data.data.metadata import update_timestamp


class CommitteeDocumentsFetcher:
    """Fetch committee documents and detect changes."""

    def __init__(self, client: Optional[CommitteeDocumentsClient] = None) -> None:
        """Initialize fetcher.

        Args:
            client: CommitteeDocumentsClient instance
        """
        self.client = client or CommitteeDocumentsClient()

    def main(
        self,
        committee_codes: list[str],
        output_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
        window_days: int = 90,
    ) -> list[dict]:
        """Fetch documents with rolling 3-month window.

        Args:
            committee_codes: Committees to monitor
            output_path: Path to write documents.json
            metadata_path: Path to metadata
            window_days: Days to look back (default: 90)
        """
        if output_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            output_path = project_root / "data" / "committees" / "documents.json"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing documents
        existing = self._load_documents(output_path)

        # Calculate window
        start_date = (datetime.now(timezone.utc) - timedelta(days=window_days)).strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )

        # Fetch all documents from API
        print(f"Fetching documents from {len(committee_codes)} committees...")
        fetched = self._fetch_all_pages(committee_codes, start_date)
        print(f"Fetched {len(fetched)} documents")

        # Purge documents older than window
        fetched = self._purge_old_documents(fetched, window_days)

        # Detect changes
        existing_by_ref = {doc["documentReference"]: doc for doc in existing}
        new_docs = [doc for doc in fetched if doc["documentReference"] not in existing_by_ref]

        print(f"New documents: {len(new_docs)}")

        # Merge
        merged = {doc["documentReference"]: doc for doc in existing}
        for doc in fetched:
            merged[doc["documentReference"]] = doc

        merged_list = list(merged.values())

        # Save
        output_path.write_text(json.dumps(merged_list, indent=2, ensure_ascii=False))
        print(f"Saved {len(merged_list)} documents to {output_path}")

        # Update metadata
        if metadata_path:
            metadata_path = Path(metadata_path)
            metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
            update_timestamp(metadata, "committees_fetched_at")
            metadata_path.write_text(json.dumps(metadata, indent=2))

        return new_docs

    def _load_documents(self, path: Path) -> list[dict[str, Any]]:
        """Load existing documents from disk."""
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return []

    def _fetch_all_pages(self, committee_codes: list[str], start_date: str) -> list[dict]:
        """Fetch all pages with pagination."""
        all_docs = []
        page = 0

        while True:
            resp = self.client.fetch_documents(committee_codes, start_date, page=page, size=100)
            all_docs.extend(resp.get("content", []))

            total_pages = resp.get("totalPages", 1)
            if page >= total_pages - 1:
                break

            page += 1

        return all_docs

    def _purge_old_documents(
        self, documents: list[dict], window_days: int
    ) -> list[dict]:
        """Remove documents older than window."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

        filtered = []
        for doc in documents:
            try:
                creation = datetime.fromisoformat(
                    doc["creationDate"].replace("Z", "+00:00")
                )
                if creation >= cutoff:
                    filtered.append(doc)
            except (ValueError, KeyError):
                filtered.append(doc)

        return filtered

    def detect_changes(
        self,
        existing: list[dict[str, Any]],
        fetched: list[dict[str, Any]],
    ) -> tuple[list[dict], list[ChangeEvent]]:
        """Detect NEW and UPDATED documents.

        Args:
            existing: Previous documents snapshot
            fetched: Newly fetched documents

        Returns:
            Tuple of (new_documents, change_events)
        """
        existing_refs = {doc["documentReference"] for doc in existing}
        existing_by_ref = {doc["documentReference"]: doc for doc in existing}

        new_docs = []
        events = []

        for doc in fetched:
            ref = doc["documentReference"]

            if ref not in existing_refs:
                # NEW document - triggers alert
                new_docs.append(doc)
                events.append(
                    ChangeEvent(
                        reference=doc.get("reference", ref),
                        topicId=ref,
                        event_type="NEW",
                        detected_at=datetime.now(timezone.utc).isoformat() + "Z",
                        snapshot=doc,
                    )
                )
            else:
                # Check if UPDATED
                old_doc = existing_by_ref[ref]
                if doc.get("updateDate") != old_doc.get("updateDate"):
                    events.append(
                        ChangeEvent(
                            reference=doc.get("reference", ref),
                            topicId=ref,
                            event_type="UPDATED",
                            detected_at=datetime.now(timezone.utc).isoformat() + "Z",
                            field="updateDate",
                            old_value=old_doc.get("updateDate"),
                            new_value=doc.get("updateDate"),
                            snapshot_after=doc,
                        )
                    )

        return new_docs, events

    def save_changelog(self, events: list[ChangeEvent], changelog_dir: Path) -> None:
        """Save changelog with all events."""
        changelog_dir.mkdir(parents=True, exist_ok=True)

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        changelog_file = changelog_dir / f"{today}.json"

        new_count = sum(1 for e in events if e.event_type == "NEW")
        changed_count = sum(1 for e in events if e.event_type in ["NEW", "UPDATED"])

        changelog = {
            "fetch_date": today,
            "fetch_timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "summary": {
                "new": new_count,
                "updated": changed_count - new_count,
                "total_events": len(events),
            },
            "events": [e.to_dict() for e in events],
        }

        changelog_file.write_text(json.dumps(changelog, indent=2, ensure_ascii=False))
