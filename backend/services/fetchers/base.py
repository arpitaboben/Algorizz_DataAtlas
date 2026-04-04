"""
Abstract base class for dataset fetchers.
All platform-specific fetchers inherit from this.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from models.schemas import Dataset


class DatasetFetcher(ABC):
    """Abstract interface for fetching dataset metadata from a source."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the source identifier (e.g. 'kaggle', 'huggingface', 'github')."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check whether this fetcher is configured and usable."""
        ...

    @abstractmethod
    async def fetch(self, query: str, limit: int = 20) -> list[Dataset]:
        """
        Fetch dataset metadata matching the query.
        Returns metadata only — does NOT download actual datasets.
        Only returns datasets that have CSV files available.
        """
        ...
