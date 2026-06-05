"""Plugin system for Love Director. Extensible architecture for data import, AI backends, and psychology models."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class DataImportPlugin(ABC):
    """Plugin for importing chat data from various sources."""
    name: str = "base"
    supported_platforms: list[str] = []

    @abstractmethod
    def detect_format(self, path: Path) -> bool: ...

    @abstractmethod
    def import_chat(self, path: Path) -> str: ...


class AIBackendPlugin(ABC):
    """Plugin for AI model backends."""
    name: str = "base"
    supported_models: list[str] = []

    @abstractmethod
    def generate(self, prompt: str, context: dict) -> str: ...


class PsychologyPlugin(ABC):
    """Plugin for psychological assessment models."""
    name: str = "base"

    @abstractmethod
    def assess(self, data: dict) -> dict: ...
