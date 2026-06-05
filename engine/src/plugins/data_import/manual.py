"""Manual text paste adapter — accepts raw chat text in various formats."""

from pathlib import Path
from ..base import DataImportPlugin


class ManualAdapter(DataImportPlugin):
    name = "manual"
    supported_platforms = ["any"]

    def detect_format(self, path: Path) -> bool:
        return True  # accepts any text

    def import_chat(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="ignore")
