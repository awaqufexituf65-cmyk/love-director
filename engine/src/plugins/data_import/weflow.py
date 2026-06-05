"""WeFlow adapter — imports WeChat chat exports from WeFlow TXT format."""

from pathlib import Path
from ..base import DataImportPlugin


class WeFlowAdapter(DataImportPlugin):
    name = "weflow"
    supported_platforms = ["wechat"]

    def detect_format(self, path: Path) -> bool:
        if not path.suffix == ".txt":
            return False
        text = path.read_text(encoding="utf-8", errors="ignore")
        # WeFlow TXT format: "YYYY-MM-DD HH:MM:SS Name: message"
        first_line = text.strip().split("\n")[0] if text.strip() else ""
        import re
        return bool(re.match(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+.+:.+', first_line))

    def import_chat(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="ignore")
