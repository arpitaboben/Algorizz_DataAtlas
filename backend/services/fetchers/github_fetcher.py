"""
GitHub Datasets Fetcher.
Uses the public GitHub Search API to find repositories containing datasets.
No auth required (60 requests/hour). With a token, 30 requests/min.
"""
from __future__ import annotations
import logging
import hashlib
import httpx

from services.fetchers.base import DatasetFetcher
from models.schemas import Dataset
from config import settings

logger = logging.getLogger(__name__)


class GitHubFetcher(DatasetFetcher):

    SEARCH_URL = "https://api.github.com/search/repositories"

    @property
    def source_name(self) -> str:
        return "github"

    async def is_available(self) -> bool:
        # GitHub public API always available (token is optional)
        return True

    async def fetch(self, query: str, limit: int = 20) -> list[Dataset]:
        try:
            headers = {
                "Accept": "application/vnd.github.v3+json",
            }
            if settings.GITHUB_TOKEN:
                headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

            # Search for repos with dataset-related keywords + CSV mention
            search_query = f"{query} dataset csv in:name,description,readme"
            params = {
                "q": search_query,
                "sort": "stars",
                "order": "desc",
                "per_page": min(limit, 30),
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(self.SEARCH_URL, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            items = data.get("items", [])
            datasets: list[Dataset] = []

            for item in items[:limit]:
                try:
                    full_name = item.get("full_name", "")
                    ds_id = f"gh-{hashlib.md5(full_name.encode()).hexdigest()[:12]}"

                    description = item.get("description", "") or ""
                    size_kb = item.get("size", 0) or 0  # GitHub reports size in KB
                    size_bytes = size_kb * 1024

                    # Skip repos larger than configured max
                    if size_bytes > settings.max_dataset_bytes:
                        continue

                    # Format size for display
                    if size_bytes < 1024 ** 2:
                        size_str = f"{size_bytes / 1024:.1f} KB"
                    elif size_bytes < 1024 ** 3:
                        size_str = f"{size_bytes / (1024 ** 2):.1f} MB"
                    else:
                        size_str = f"{size_bytes / (1024 ** 3):.1f} GB"

                    # Extract tags from topics
                    tags = item.get("topics", []) or []
                    tags = [str(t) for t in tags[:10]]

                    updated_at = item.get("updated_at", "")
                    owner = item.get("owner", {}).get("login", "Unknown")
                    license_info = item.get("license") or {}
                    license_name = license_info.get("spdx_id", "Unknown") if isinstance(license_info, dict) else "Unknown"

                    stars = item.get("stargazers_count", 0)

                    datasets.append(Dataset(
                        id=ds_id,
                        title=item.get("name", full_name).replace("-", " ").replace("_", " ").title(),
                        description=description[:500],
                        source="github",
                        format="csv",
                        size=size_str,
                        sizeBytes=size_bytes,
                        downloadUrl=item.get("html_url", f"https://github.com/{full_name}"),
                        tags=tags,
                        lastUpdated=updated_at,
                        author=owner,
                        license=license_name,
                    ))
                except Exception as e:
                    logger.warning(f"Failed to parse GitHub repo {item.get('full_name', '?')}: {e}")
                    continue

            logger.info(f"GitHub: found {len(datasets)} datasets for '{query}'")
            return datasets

        except Exception as e:
            logger.error(f"GitHub fetch error: {e}")
            return []
