"""Phase state machine — enforces the 5-phase workflow order and data completion."""

from enum import Enum
from typing import Optional, Any
from dataclasses import dataclass


class Phase(Enum):
    SAFETY = "phase_0"
    PROFILE_SELF = "phase_1a"
    PROFILE_BEHAVIOR = "phase_1b"
    PROFILE_GAP = "phase_1c"
    PHILOSOPHY = "phase_2"
    OBSERVATION = "phase_3"
    DECISION_TREE = "phase_4"
    PERSPECTIVE = "phase_5"

    @classmethod
    def from_str(cls, s: str) -> "Phase":
        for p in cls:
            if p.value == s:
                return p
        raise ValueError(f"Unknown phase: {s}")


# Phase dependencies: which phase needs which data before it can start
PHASE_REQUIREMENTS = {
    Phase.SAFETY: [],
    Phase.PROFILE_SELF: [Phase.SAFETY],
    Phase.PROFILE_BEHAVIOR: [Phase.PROFILE_SELF],
    Phase.PROFILE_GAP: [Phase.PROFILE_SELF, Phase.PROFILE_BEHAVIOR],
    Phase.PHILOSOPHY: [Phase.PROFILE_GAP],
    Phase.OBSERVATION: [Phase.PHILOSOPHY, Phase.PROFILE_BEHAVIOR],
    Phase.DECISION_TREE: [Phase.OBSERVATION],
    Phase.PERSPECTIVE: [Phase.DECISION_TREE],
}

# Minimum data required for each phase to be considered "complete"
PHASE_DATA_CHECKS = {
    Phase.PROFILE_SELF: ["age", "gender", "city_tier", "parent_marriage"],
    Phase.PROFILE_BEHAVIOR: ["chat_sources"],  # at least 1 chat source provided
    Phase.PROFILE_GAP: ["gap_analysis"],
    Phase.PHILOSOPHY: ["time_belief", "purpose", "value_ranking", "conflict_belief"],
    Phase.OBSERVATION: ["core_pattern", "contradictions", "key_variables"],
    Phase.DECISION_TREE: ["variables", "branches", "endings"],
    Phase.PERSPECTIVE: [],  # no data needed, just user reflection
}


@dataclass
class PhaseState:
    current: Phase = Phase.SAFETY
    completed: set[Phase] = None
    data: dict = None

    def __post_init__(self):
        if self.completed is None:
            self.completed = set()
        if self.data is None:
            self.data = {}


class PhaseManager:
    """Enforces phase ordering and data completeness."""

    def __init__(self):
        self.state = PhaseState()

    # ---- Navigation ----
    def can_proceed_to(self, target: Phase) -> bool:
        """Check if all dependencies of `target` are completed."""
        deps = PHASE_REQUIREMENTS.get(target, [])
        return all(d in self.state.completed for d in deps)

    def advance_to(self, target: Phase) -> bool:
        if not self.can_proceed_to(target):
            return False
        self.state.current = target
        return True

    def get_next_phase(self) -> Optional[Phase]:
        """Auto-detect which phase should come next."""
        phase_order = list(Phase)
        idx = phase_order.index(self.state.current)
        if idx + 1 < len(phase_order):
            next_p = phase_order[idx + 1]
            if self.can_proceed_to(next_p):
                return next_p
        return None

    # ---- Data validation ----
    def is_phase_data_complete(self, phase: Phase) -> tuple[bool, list[str]]:
        """Returns (is_complete, missing_keys)."""
        required = PHASE_DATA_CHECKS.get(phase, [])
        missing = [k for k in required if k not in self.state.data or not self.state.data[k]]
        return len(missing) == 0, missing

    def complete_phase(self, phase: Phase, data: Optional[dict] = None) -> bool:
        complete, missing = self.is_phase_data_complete(phase)
        if not complete:
            return False
        self.state.completed.add(phase)
        if data:
            self.state.data.update(data)
        return True

    # ---- Status ----
    def progress(self) -> dict:
        total = len(Phase)
        done = len(self.state.completed)
        return {
            "current": self.state.current.value,
            "completed": [p.value for p in self.state.completed],
            "remaining": [p.value for p in Phase if p not in self.state.completed],
            "percentage": round(done / total * 100),
            "can_advance": bool(self.get_next_phase()),
        }

    def reset(self) -> None:
        self.state = PhaseState()
