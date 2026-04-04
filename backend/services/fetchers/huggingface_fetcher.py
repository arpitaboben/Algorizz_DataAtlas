"""
HuggingFace Datasets Fetcher.
Uses the public HuggingFace Hub API (no token required, token = higher rate limit).
Endpoint: https://huggingface.co/api/datasets?search=...
"""
from __future__ import annotations
import logging
import hashlib
import httpx

from services.fetchers.base import DatasetFetcher
from models.schemas import Dataset
from config import settings

logger = logging.getLogger(__name__)


class HuggingFaceFetcher(DatasetFetcher):

    API_URL = "https://huggingface.co/api/datasets"

    @property
    def source_name(self) -> str:
        return "huggingface"

    async def is_available(self) -> bool:
        # HuggingFace public API always available (token is optional)
        return True

    async def fetch(self, query: str, limit: int = 20) -> list[Dataset]:
        try:
            headers = {}
            if settings.HUGGINGFACE_TOKEN:
                headers["Authorization"] = f"Bearer {settings.HUGGINGFACE_TOKEN}"

            params = {
                "search": query,
                "limit": limit,
                "sort": "downloads",
                "direction": "-1",
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(self.API_URL, params=params, headers=headers)
                resp.raise_for_status()
                items = resp.json()

            datasets: list[Dataset] = []
            for item in items[:limit]:
                try:
                    ds_name = item.get("id", "")  # e.g. "username/dataset-name"
                    ds_id = f"hf-{hashlib.md5(ds_name.encode()).hexdigest()[:12]}"

                    # Description
                    description = item.get("description", "") or ""
                    if not description and item.get("cardData"):
                        description = item["cardData"].get("description", "")

                    # Tags
                    tags = item.get("tags", []) or []
                    tags = [str(t) for t in tags[:10]]  # cap at 10

                    # Check if CSV is among formats or just include all
                    # HuggingFace doesn't always expose file format in listing
                    # We mark as csv and verify on download

                    last_modified = item.get("lastModified", "")
                    author = ds_name.split("/")[0] if "/" in ds_name else "HuggingFace"

                    # Downloads as a proxy for size display
                    downloads = item.get("downloads", 0) or 0

                    datasets.append(Dataset(
                        id=ds_id,
                        title=ds_name.split("/")[-1].replace("-", " ").replace("_", " ").title()
                            if "/" in ds_name else ds_name,
                        description=description[:500],
                        source="huggingface",
                        format="csv",
                        size=f"{downloads:,} downloads",
                        sizeBytes=0,  # HuggingFace API doesn't always expose size
                        downloadUrl=f"https://huggingface.co/datasets/{ds_name}",
                        tags=tags,
                        lastUpdated=last_modified,
                        author=author,
                        license=item.get("cardData", {}).get("license", "Unknown")
                            if isinstance(item.get("cardData"), dict) else "Unknown",
                    ))
                except Exception as e:
                    logger.warning(f"Failed to parse HuggingFace dataset: {e}")
                    continue

            logger.info(f"HuggingFace: found {len(datasets)} datasets for '{query}'")
            return datasets

        except Exception as e:
            logger.error(f"HuggingFace fetch error: {e}")
            return []
