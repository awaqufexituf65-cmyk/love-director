"""Love Director Engine — Main orchestrator.

Binds all modules together: PhaseManager + ChatAnalyzer + ProfileEngine +
ProbabilityEngine + DecisionTreeEngine.

Usage:
    from director import LoveDirectorEngine
    engine = LoveDirectorEngine()
    session_id = engine.start_session()
    engine.process_phase(session_id, phase, input_data)
"""

from pathlib import Path
from typing import Optional

try:
    from .phases.phase_manager import PhaseManager, Phase
    from .analysis.chat_analyzer import ChatAnalyzer
    from .analysis.profile_engine import ProfileEngine
    from .analysis.probability_engine import ProbabilityEngine
    from .phases.decision_tree import DecisionTreeEngine
    from .data.store import DataStore
except ImportError:
    from phases.phase_manager import PhaseManager, Phase
    from analysis.chat_analyzer import ChatAnalyzer
    from analysis.profile_engine import ProfileEngine
    from analysis.probability_engine import ProbabilityEngine
    from phases.decision_tree import DecisionTreeEngine
    from data.store import DataStore


class LoveDirectorEngine:
    """Platform-independent core engine. No AI platform dependency."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.store = DataStore()
        self.phase_manager = PhaseManager()
        self.chat_analyzer = ChatAnalyzer()
        self.profile_engine = ProfileEngine()

        # Load knowledge base
        kb_dir = data_dir or Path(__file__).parent.parent.parent.parent / "data"
        kb = self.store.load_knowledge_base(kb_dir)
        self.prob_engine = ProbabilityEngine(stats_baseline=kb.get("stats", {}))
        self.tree_engine = DecisionTreeEngine(prob_engine=self.prob_engine)

    # ---- Session lifecycle ----
    def start_session(self) -> str:
        return self.store.create_session()

    def get_progress(self, session_id: str) -> dict:
        return self.phase_manager.progress()

    # ---- Phase processing ----
    def process_phase(self, session_id: str, phase_str: str, input_data: dict) -> dict:
        """Process input for a specific phase and advance the state machine."""
        phase = Phase.from_str(phase_str)

        if not self.phase_manager.advance_to(phase):
            return {
                "success": False,
                "errors": [f"Cannot advance to {phase_str}. Check dependencies."],
                "next_phase": None,
            }

        handlers = {
            Phase.SAFETY: self._handle_safety,
            Phase.PROFILE_SELF: self._handle_profile_self,
            Phase.PROFILE_BEHAVIOR: self._handle_profile_behavior,
            Phase.PROFILE_GAP: self._handle_profile_gap,
            Phase.PHILOSOPHY: self._handle_philosophy,
            Phase.OBSERVATION: self._handle_observation,
            Phase.DECISION_TREE: self._handle_decision_tree,
            Phase.PERSPECTIVE: self._handle_perspective,
        }

        handler = handlers.get(phase)
        if not handler:
            return {"success": False, "errors": [f"No handler for {phase_str}"]}

        result = handler(session_id, input_data)

        # Update state data and mark phase complete
        self.phase_manager.state.data.update(input_data)
        self.phase_manager.state.data.update(result)  # handler output
        self.phase_manager.state.completed.add(phase)

        next_p = self.phase_manager.get_next_phase()
        result["next_phase"] = next_p.value if next_p else None
        result["success"] = True

        return result

    # ---- Phase handlers ----
    def _handle_safety(self, session_id: str, data: dict) -> dict:
        return {"result": "safety_accepted", "message": "用户已同意安全声明"}

    def _handle_profile_self(self, session_id: str, data: dict) -> dict:
        self.store.save_profile(session_id, data)
        return {"result": "profile_saved", "fields_collected": list(data.keys())}

    def _handle_profile_behavior(self, session_id: str, data: dict) -> dict:
        chat_texts = data.get("chat_texts", [])
        if not chat_texts:
            return {"result": "no_chat_data", "warnings": ["未提供聊天记录"]}

        analyses = [self.chat_analyzer.analyze_text(ct) for ct in chat_texts]
        cross_analysis = self.chat_analyzer.analyze_multiple_chats(chat_texts)

        profile = self.store.get_profile(session_id)
        profile["chat_analyses"] = [a.__dict__ for a in analyses]
        profile["cross_analysis"] = cross_analysis.__dict__
        self.store.save_profile(session_id, profile)

        return {
            "result": "behavior_analyzed",
            "relationship_count": len(chat_texts),
            "cross_analysis": {
                "partner_similarity": cross_analysis.partner_similarity_score,
                "avg_conflict_avoidance": cross_analysis.conflict_avoidance_score,
            },
        }

    def _handle_profile_gap(self, session_id: str, data: dict) -> dict:
        profile = self.store.get_profile(session_id)
        self_report = {k: v for k, v in profile.items() if k not in ("chat_analyses", "cross_analysis")}
        chat = profile.get("cross_analysis", {})

        result = self.profile_engine.compute_profile(self_report, chat)

        profile["gap_analysis"] = {
            "gaps": [g.__dict__ for g in result.gaps],
            "vulnerability_score": result.vulnerability_score,
            "vulnerability_factors": result.vulnerability_factors,
        }
        self.store.save_profile(session_id, profile)

        return {
            "result": "gap_computed",
            "gap_count": len(result.gaps),
            "top_gaps": [{"dimension": g.dimension, "severity": g.gap_severity} for g in result.gaps[:3]],
            "vulnerability_score": result.vulnerability_score,
        }

    def _handle_philosophy(self, session_id: str, data: dict) -> dict:
        self.store.save_philosophy(session_id, data)
        dimensions = list(data.keys())
        return {"result": "philosophy_saved", "dimensions_covered": len(dimensions), "dimensions": dimensions}

    def _handle_observation(self, session_id: str, data: dict) -> dict:
        profile = self.store.get_profile(session_id)
        gaps = profile.get("gap_analysis", {}).get("gaps", [])

        behavior = {
            "conflict_gap": 0.0, "conflict_consistency": 0.7,
            "speed_gap": 0.0, "speed_consistency": 0.65,
            "filter_gap": 0.0, "filter_consistency": 0.6,
            "giving_gap": 0.0, "giving_consistency": 0.5,
            "security_gap": 0.0, "security_consistency": 0.55,
            "social_media_gap": 0.0, "social_media_consistency": 0.5,
            "change_success_rate": 0.3,
            "past_partner_anxious": False,
            "core_pattern_description": "待提取",
        }

        dim_map = {"mate_selection_criteria": "filter_gap", "conflict_style": "conflict_gap", "emotional_speed": "speed_gap"}
        for gap in gaps:
            key = dim_map.get(gap.get("dimension", ""))
            if key:
                behavior[key] = gap.get("gap_severity", 0.0)

        self.store.save_behavior(session_id, behavior)
        return {"result": "observation_complete"}

    def _handle_decision_tree(self, session_id: str, data: dict) -> dict:
        profile = self.store.get_profile(session_id)
        philosophy = self.store.get_philosophy(session_id) or {}
        behavior = self.store.get_behavior(session_id) or {}

        variables = self.tree_engine.extract_variables(profile, philosophy, behavior)
        tree = self.tree_engine.build_tree(variables, profile, behavior)
        ok, issues = self.tree_engine.validate_tree(tree)
        tree_dict = self.tree_engine.tree_to_dict(tree)
        self.store.save_decision_tree(session_id, tree_dict)

        return {
            "result": "decision_tree_generated",
            "variable_count": len(variables),
            "variables": [v.name for v in variables],
            "validation_passed": ok,
            "validation_issues": issues,
            "tree": tree_dict,
        }

    def _handle_perspective(self, session_id: str, data: dict) -> dict:
        return {"result": "perspective_complete", "message": "导演视角闭环"}
