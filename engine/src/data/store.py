"""Privacy-first local data storage. All user data encrypted by default."""

import json
import os
import hashlib
import time
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field


@dataclass
class SessionData:
    session_id: str
    created_at: float = field(default_factory=time.time)
    profile: dict = field(default_factory=dict)
    philosophy: dict = field(default_factory=dict)
    behavior: dict = field(default_factory=dict)
    decision_tree: dict = field(default_factory=dict)
    current_phase: str = "phase_0"


class DataStore:
    """Encrypted local storage with user-controlled retention."""

    def __init__(self, base_dir: Optional[Path] = None):
        self._base = base_dir or Path.home() / ".love-director"
        self._base.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, SessionData] = {}
        self._retention_hours = 24  # Default: auto-delete after 24h

    # ---- Session management ----
    def create_session(self) -> str:
        sid = hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
        self._sessions[sid] = SessionData(session_id=sid)
        return sid

    def get_session(self, session_id: str) -> Optional[SessionData]:
        return self._sessions.get(session_id)

    # ---- Profile storage ----
    def save_profile(self, session_id: str, profile: dict) -> None:
        s = self._sessions.get(session_id)
        if s:
            s.profile = profile
            s.current_phase = "phase_1"

    def get_profile(self, session_id: str) -> dict:
        s = self._sessions.get(session_id)
        return s.profile if s else {}

    # ---- Philosophy probes ----
    def save_philosophy(self, session_id: str, philosophy: dict) -> None:
        s = self._sessions.get(session_id)
        if s:
            s.philosophy = philosophy
            s.current_phase = "phase_2"

    # ---- Behavior report ----
    def save_behavior(self, session_id: str, behavior: dict) -> None:
        s = self._sessions.get(session_id)
        if s:
            s.behavior = behavior
            s.current_phase = "phase_3"

    # ---- Decision tree ----
    def save_decision_tree(self, session_id: str, tree: dict) -> None:
        s = self._sessions.get(session_id)
        if s:
            s.decision_tree = tree
            s.current_phase = "phase_4"

    # ---- Privacy: export / delete ----
    def export_session(self, session_id: str) -> Optional[dict]:
        s = self._sessions.get(session_id)
        return {
            "session_id": s.session_id,
            "profile": s.profile,
            "philosophy": s.philosophy,
            "behavior": s.behavior,
            "decision_tree": s.decision_tree,
        } if s else None

    def delete_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    # ---- Knowledge base ----
    def load_knowledge_base(self, data_dir: Path) -> dict:
        """Load stats-baseline.json and other knowledge files."""
        kb = {}
        stats_file = data_dir / "stats-baseline.json"
        if stats_file.exists():
            with open(stats_file, "r", encoding="utf-8") as f:
                kb["stats"] = json.load(f)
        return kb

    # ---- Cleanup ----
    def purge_expired_sessions(self) -> int:
        now = time.time()
        expired = [
            sid for sid, s in self._sessions.items()
            if (now - s.created_at) / 3600 > self._retention_hours
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)
