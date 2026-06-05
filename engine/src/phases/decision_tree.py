"""Decision Tree Engine — The beating heart of Love Director.

Generates a probabilistic decision tree from user profile + philosophy + behavior data.
NOT a fixed template — the tree grows from the user's actual data patterns.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

try:
    from ..analysis.probability_engine import ProbabilityEngine, Probability
except ImportError:
    from analysis.probability_engine import ProbabilityEngine, Probability


class EndingType(Enum):
    INERTIA = "inertia"
    GROWTH = "growth"
    SURPRISE = "surprise"
    WARNING = "warning"
    CYCLE = "cycle"
    RECONSTRUCTION = "reconstruction"


ENDING_EMOJI = {
    EndingType.INERTIA: "\U0001f342",
    EndingType.GROWTH: "\U0001f331",
    EndingType.SURPRISE: "⚡",
    EndingType.WARNING: "\U0001f480",
    EndingType.CYCLE: "\U0001f504",
    EndingType.RECONSTRUCTION: "\U0001f308",
}


@dataclass
class Variable:
    name: str
    description: str
    self_report_gap: float
    cross_relationship_consistency: float
    change_difficulty: float
    data_evidence: list[str] = field(default_factory=list)

    @property
    def is_significant(self) -> bool:
        return self.self_report_gap >= 0.5 and self.cross_relationship_consistency >= 0.5

    @property
    def rank_score(self) -> float:
        return self.self_report_gap * 0.4 + self.cross_relationship_consistency * 0.4 + max(0, 1 - self.change_difficulty) * 0.2


@dataclass
class Branch:
    label: str
    direction: str
    probability: Probability
    data_evidence: str
    children: list["TreeNode"] = field(default_factory=list)


@dataclass
class StochasticEvent:
    name: str
    description: str
    base_rate: float
    match_user_pattern: bool


@dataclass
class Ending:
    title: str
    ending_type: EndingType
    probability: Probability
    timeframe: str
    story: str
    gain: str
    loss: str
    data_basis: list[str] = field(default_factory=list)


@dataclass
class TreeNode:
    label: str
    level: int
    data: Optional[Variable | StochasticEvent | Branch | Ending] = None
    children: list["TreeNode"] = field(default_factory=list)


class DecisionTreeEngine:
    MIN_ENDING_TYPES = 4

    def __init__(self, prob_engine: Optional[ProbabilityEngine] = None):
        self._prob = prob_engine or ProbabilityEngine()

    def extract_variables(self, profile: dict, philosophy: dict, behavior: dict) -> list[Variable]:
        candidates = []

        if "conflict_belief" in philosophy:
            cs = philosophy["conflict_belief"]
            candidates.append(Variable(
                name="conflict_handling", description="冲突应对方式",
                self_report_gap=behavior.get("conflict_gap", 0.0),
                cross_relationship_consistency=behavior.get("conflict_consistency", 0.0),
                change_difficulty=0.7 if cs.get("type") == "avoidance" else 0.3,
                data_evidence=behavior.get("conflict_evidence", []),
            ))

        if "time_belief" in philosophy:
            candidates.append(Variable(
                name="confirmation_speed", description="关系确认速度",
                self_report_gap=behavior.get("speed_gap", 0.0),
                cross_relationship_consistency=behavior.get("speed_consistency", 0.0),
                change_difficulty=0.4,
                data_evidence=behavior.get("speed_evidence", []),
            ))

        if "value_ranking" in philosophy:
            candidates.append(Variable(
                name="mate_selection_filter", description="择偶筛选机制",
                self_report_gap=behavior.get("filter_gap", 0.0),
                cross_relationship_consistency=behavior.get("filter_consistency", 0.0),
                change_difficulty=0.5,
                data_evidence=behavior.get("filter_evidence", []),
            ))

        if "giving_pattern" in philosophy:
            candidates.append(Variable(
                name="giving_pattern", description="付出观念",
                self_report_gap=behavior.get("giving_gap", 0.0),
                cross_relationship_consistency=behavior.get("giving_consistency", 0.0),
                change_difficulty=0.5,
                data_evidence=behavior.get("giving_evidence", []),
            ))

        if "security_source" in philosophy:
            candidates.append(Variable(
                name="security_attachment", description="安全感来源",
                self_report_gap=behavior.get("security_gap", 0.0),
                cross_relationship_consistency=behavior.get("security_consistency", 0.0),
                change_difficulty=0.6,
                data_evidence=behavior.get("security_evidence", []),
            ))

        if "social_media_influence" in philosophy:
            candidates.append(Variable(
                name="social_media", description="社交媒体渗透度",
                self_report_gap=behavior.get("social_media_gap", 0.0),
                cross_relationship_consistency=behavior.get("social_media_consistency", 0.0),
                change_difficulty=0.4,
                data_evidence=behavior.get("social_media_evidence", []),
            ))

        candidates.sort(key=lambda v: v.rank_score, reverse=True)
        selected = candidates[:4]
        if len(selected) < 2:
            selected = candidates[:2]
        return selected

    def build_tree(self, variables: list[Variable], profile: dict, behavior: dict) -> TreeNode:
        root = TreeNode(label="Core Pattern", level=0)

        for var in variables:
            var_node = TreeNode(label=var.description, level=1, data=var)

            keep_prob = self._prob.compute_branch_probability(
                var.name, "keep",
                user_consistency=var.cross_relationship_consistency,
                user_change_success=0.0,
            )
            keep_branch = TreeNode(label="Keep", level=2, data=Branch(
                label="保持", direction="keep", probability=keep_prob,
                data_evidence=var.data_evidence[0] if var.data_evidence else "",
            ))
            keep_branch.children = self._build_stochastic_layer(var, keep_branch, keep_prob, behavior)

            change_prob = self._prob.compute_branch_probability(
                var.name, "change",
                user_consistency=var.cross_relationship_consistency,
                user_change_success=behavior.get("change_success_rate", 0.3),
            )
            change_branch = TreeNode(label="Change", level=2, data=Branch(
                label="改变", direction="change", probability=change_prob,
                data_evidence="User desires change",
            ))
            change_branch.children = self._build_stochastic_layer(var, change_branch, change_prob, behavior)

            var_node.children = [keep_branch, change_branch]
            root.children.append(var_node)

        return root

    def _build_stochastic_layer(self, var: Variable, parent: TreeNode, parent_prob: Probability, behavior: dict) -> list[TreeNode]:
        events = self._get_relevant_events(var, behavior)
        nodes = []
        for event in events:
            event_prob = self._prob.compute_conditional_probability(parent_prob, event.name, event.base_rate)
            event_node = TreeNode(label=event.name, level=3, data=event)
            direction = parent.data.direction if isinstance(parent.data, Branch) else "keep"
            endings = self._generate_endings(var, direction, event)
            for ending in endings:
                ending_prob = self._prob.compute_conditional_probability(event_prob, ending.title, 0.5)
                ending.probability = ending_prob
                leaf = TreeNode(
                    label=f"{ENDING_EMOJI.get(ending.ending_type, '')} {ending.title}",
                    level=4, data=ending,
                )
                event_node.children.append(leaf)
            nodes.append(event_node)
        return nodes

    def _generate_endings(self, var: Variable, direction: str, event: StochasticEvent) -> list[Ending]:
        endings = []
        endings.append(Ending(
            title=f"Inertia: {var.description} unchanged",
            ending_type=EndingType.INERTIA,
            probability=Probability(0.25, 0.15, 0.35, 0.25, 0.25, 0.0, [], []),
            timeframe="6-12 months",
            story=f"You continue your pattern. {event.description} happens. Life goes on as usual.",
            gain="Familiarity, no need to face fear of change",
            loss="Lost opportunity for something different",
            data_basis=[f"Consistent in {var.cross_relationship_consistency*100:.0f}% of past relationships"],
        ))

        if direction == "change":
            endings.append(Ending(
                title=f"Growth: First time changing {var.description}",
                ending_type=EndingType.GROWTH,
                probability=Probability(0.12, 0.05, 0.20, 0.12, 0.10, 0.08, [], []),
                timeframe="6-18 months",
                story=f"You made a different choice. It felt strange at first, but the result surprised you.",
                gain="New experience, confirmation of self-efficacy",
                loss="Comfort zone of old patterns",
                data_basis=["User expressed desire to change"],
            ))

        if direction == "keep":
            endings.append(Ending(
                title=f"Warning: {var.description} to extreme",
                ending_type=EndingType.WARNING,
                probability=Probability(0.18, 0.10, 0.28, 0.18, 0.15, 0.12, [], []),
                timeframe="3-5 years",
                story=f"Your pattern intensifies. {event.description} accelerates it. You find yourself in a cycle.",
                gain="Short-term security",
                loss="Long-term flexibility, openness to different possibilities",
                data_basis=[f"Self-report gap: {var.self_report_gap:.2f}"],
            ))

        endings.append(Ending(
            title=f"Surprise: {event.name} brings unexpected change",
            ending_type=EndingType.SURPRISE,
            probability=Probability(0.08, 0.02, 0.15, 0.05, 0.08, 0.10, [], []),
            timeframe="1-3 years",
            story=f"{event.description}. This unexpected event gives you a new perspective.",
            gain="Unexpected perspective shift",
            loss="Sense of control over life",
            data_basis=[f"Base rate of {event.name}: {event.base_rate:.0%}"],
        ))

        return endings

    def _get_relevant_events(self, var: Variable, behavior: dict) -> list[StochasticEvent]:
        return [
            StochasticEvent("Meet secure-attachment partner", "You meet someone with a secure attachment style", 0.25, True),
            StochasticEvent("Meet anxious-attachment partner", "You meet someone with an anxious attachment style", 0.19, behavior.get("past_partner_anxious", False)),
            StochasticEvent("Major life change", "Job change, move, or family event shifts your focus", 0.15, True),
            StochasticEvent("Someone who doesn't fit your template", "You meet someone outside your usual criteria", 0.20, behavior.get("has_unexpected_connection", False)),
        ]

    def validate_tree(self, tree: TreeNode) -> tuple[bool, list[str]]:
        issues = []
        all_endings = []

        def collect(node: TreeNode):
            if isinstance(node.data, Ending):
                all_endings.append(node.data)
            for child in node.children:
                collect(child)
        collect(tree)

        ending_types = {e.ending_type for e in all_endings}
        if len(all_endings) < 6:
            issues.append(f"Only {len(all_endings)} endings (need >= 6)")
        if len(ending_types) < self.MIN_ENDING_TYPES:
            issues.append(f"Only {len(ending_types)} ending types (need >= {self.MIN_ENDING_TYPES})")

        return len(issues) == 0, issues

    def tree_to_dict(self, tree: TreeNode) -> dict:
        result = {"label": tree.label, "level": tree.level}

        if isinstance(tree.data, Variable):
            result["type"] = "variable"
            result["variable"] = {
                "name": tree.data.name, "description": tree.data.description,
                "self_report_gap": round(tree.data.self_report_gap, 2),
                "cross_relationship_consistency": round(tree.data.cross_relationship_consistency, 2),
                "change_difficulty": round(tree.data.change_difficulty, 2),
            }
        elif isinstance(tree.data, Branch):
            result["type"] = "branch"
            result["branch"] = {
                "label": tree.data.label, "direction": tree.data.direction,
                "probability": tree.data.probability.as_dict(),
            }
        elif isinstance(tree.data, StochasticEvent):
            result["type"] = "stochastic_event"
            result["event"] = {"name": tree.data.name, "description": tree.data.description, "base_rate": tree.data.base_rate}
        elif isinstance(tree.data, Ending):
            result["type"] = "ending"
            result["ending"] = {
                "title": tree.data.title, "type": tree.data.ending_type.value,
                "emoji": ENDING_EMOJI.get(tree.data.ending_type, ""),
                "probability": tree.data.probability.as_dict(),
                "timeframe": tree.data.timeframe, "story": tree.data.story,
                "gain": tree.data.gain, "loss": tree.data.loss,
                "data_basis": tree.data.data_basis,
            }

        if tree.children:
            result["children"] = [self.tree_to_dict(c) for c in tree.children]
        return result
