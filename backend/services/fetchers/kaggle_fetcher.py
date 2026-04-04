"""
Kaggle Dataset Fetcher.
Uses the official Kaggle Python SDK to search and return dataset metadata.
Gracefully disabled when KAGGLE_USERNAME / KAGGLE_KEY are not set.

This is the primary (and only) data source for Data Atlas.
"""
from __future__ import annotations
import logging
import hashlib
from typing import Optional

from services.fetchers.base import DatasetFetcher
from models.schemas import Dataset
from config import settings

logger = logging.getLogger(__name__)


def _format_bytes(size_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"


class KaggleFetcher(DatasetFetcher):

    @property
    def source_name(self) -> str:
        return "kaggle"

    async def is_available(self) -> bool:
        return settings.kaggle_available

    async def fetch(self, query: str, limit: int = 20) -> list[Dataset]:
        if not await self.is_available():
            logger.info("Kaggle API not configured — skipping")
            return []

        try:
            from kaggle.api.kaggle_api_extended import KaggleApi

            api = KaggleApi()
            api.authenticate()

            # Search for CSV datasets
            results = api.dataset_list(
                search=query,
                file_type="csv",
                sort_by="votes",
            )

            datasets: list[Dataset] = []
            for item in results[:limit]:
                try:
                    ref = str(item.ref)  # e.g. "username/dataset-slug"
                    size_bytes = int(item.totalBytes) if hasattr(item, "totalBytes") and item.totalBytes else 0

                    # Skip datasets larger than configured max
                    if size_bytes > settings.max_dataset_bytes:
                        continue

                    # Build a stable ID from the ref
                    ds_id = f"kaggle-{hashlib.md5(ref.encode()).hexdigest()[:12]}"

                    last_updated = ""
                    if hasattr(item, "lastUpdated") and item.lastUpdated:
                        try:
                            last_updated = item.lastUpdated.isoformat()
                        except Exception:
                            last_updated = str(item.lastUpdated)

                    description = ""
                    if hasattr(item, "subtitle") and item.subtitle:
                        description = str(item.subtitle)
                    elif hasattr(item, "description") and item.description:
                        description = str(item.description)

                    tags = []
                    if hasattr(item, "tags") and item.tags:
                        tags = [str(t) for t in item.tags]

                    author = ref.split("/")[0] if "/" in ref else "Unknown"

                    license_name = "Unknown"
                    if hasattr(item, "licenseName") and item.licenseName:
                        license_name = str(item.licenseName)

                    datasets.append(Dataset(
                        id=ds_id,
                        title=str(item.title) if hasattr(item, "title") else ref,
                        description=description,
                        source="kaggle",
                        format="csv",
                        size=_format_bytes(size_bytes),
                        sizeBytes=size_bytes,
                        # Store the Kaggle ref so the backend can download via SDK
                        downloadUrl=ref,
                        tags=tags,
                        lastUpdated=last_updated,
                        author=author,
                        license=license_name,
                    ))
                except Exception as e:
                    logger.warning(f"Failed to parse Kaggle dataset {item}: {e}")
                    continue

            logger.info(f"Kaggle: found {len(datasets)} datasets for '{query}'")
            return datasets

        except Exception as e:
            logger.error(f"Kaggle fetch error: {e}", exc_info=True)
            return []
