"""Decision Tree Engine — The beating heart of Love Director.

Generates a probabilistic decision tree from user profile + philosophy + behavior data.
NOT a fixed template — the tree grows from the user's actual data patterns.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from ..analysis.probability_engine import ProbabilityEngine, Probability


class EndingType(Enum):
    INERTIA = "inertia"         # 🍂 nothing changes
    GROWTH = "growth"           # 🌱 key change → positive chain reaction
    SURPRISE = "surprise"       # ⚡ external random event changes trajectory
    WARNING = "warning"         # 💀 current pattern taken to extreme
    CYCLE = "cycle"             # 🔄 surface change, same essence
    RECONSTRUCTION = "reconstruction"  # 🌈 fundamental shift in core beliefs


ENDING_EMOJI = {
    EndingType.INERTIA: "🍂",
    EndingType.GROWTH: "🌱",
    EndingType.SURPRISE: "⚡",
    EndingType.WARNING: "💀",
    EndingType.CYCLE: "🔄",
    EndingType.RECONSTRUCTION: "🌈",
}


@dataclass
class Variable:
    """A key variable extracted from user data that can branch."""
    name: str
    description: str
    self_report_gap: float      # 0-1: discrepancy between what user says vs does
    cross_relationship_consistency: float  # 0-1: how stable across past relationships
    change_difficulty: float     # 0-1: how hard to change (based on past attempts)
    data_evidence: list[str] = field(default_factory=list)

    @property
    def is_significant(self) -> bool:
        """A variable is significant if gap + consistency are high."""
        return self.self_report_gap >= 0.5 and self.cross_relationship_consistency >= 0.5

    @property
    def rank_score(self) -> float:
        """Composite score for ranking variables."""
        return self.self_report_gap * 0.4 + self.cross_relationship_consistency * 0.4 + max(0, 1 - self.change_difficulty) * 0.2


@dataclass
class Branch:
    """A single branch from a variable."""
    label: str
    direction: str  # "keep" or "change"
    probability: Probability
    data_evidence: str
    children: list["TreeNode"] = field(default_factory=list)


@dataclass
class StochasticEvent:
    """An external random event that can occur at a branch point."""
    name: str
    description: str
    base_rate: float  # 0-1: how often this event occurs in similar population
    match_user_pattern: bool  # whether user's past behavior makes this more likely


@dataclass
class Ending:
    """A leaf node — a specific future outcome with a story."""
    title: str
    ending_type: EndingType
    probability: Probability
    timeframe: str        # e.g. "6-12 months"
    story: str            # 3-5 sentence narrative
    gain: str             # what user gains from this path
    loss: str             # what user loses
    data_basis: list[str]  # specific user data that leads to this ending


@dataclass
class TreeNode:
    """A node in the decision tree."""
    label: str
    level: int            # 0=root, 1=variable, 2=stochastic, 3=leaf
    data: Optional[Variable | StochasticEvent | Ending] = None
    children: list["TreeNode"] = field(default_factory=list)


class DecisionTreeEngine:
    """Extracts variables, builds branches, generates probabilistic endings."""

    MIN_ENDING_TYPES = 4  # Each tree must have at least 4 different ending types

    def __init__(self, prob_engine: Optional[ProbabilityEngine] = None):
        self._prob = prob_engine or ProbabilityEngine()

    # ---- Step 1: Variable Extraction ----
    def extract_variables(self, profile: dict, philosophy: dict, behavior: dict) -> list[Variable]:
        """
        Extract 2-4 key variables from user data.
        These are the variables that have the most "fork potential" in the user's life.
        """
        candidates = []

        # Conflict avoidance
        if "conflict_style" in philosophy:
            cs = philosophy["conflict_style"]
            candidates.append(Variable(
                name="conflict_handling",
                description="冲突应对方式",
                self_report_gap=behavior.get("conflict_gap", 0.0),
                cross_relationship_consistency=behavior.get("conflict_consistency", 0.0),
                change_difficulty=0.7 if cs.get("type") == "avoidance" else 0.3,
                data_evidence=behavior.get("conflict_evidence", []),
            ))

        # Confirmation speed
        if "time_belief" in philosophy:
            tb = philosophy["time_belief"]
            candidates.append(Variable(
                name="confirmation_speed",
                description="关系确认速度",
                self_report_gap=behavior.get("speed_gap", 0.0),
                cross_relationship_consistency=behavior.get("speed_consistency", 0.0),
                change_difficulty=0.4,
                data_evidence=behavior.get("speed_evidence", []),
            ))

        # Mate selection filter
        if "value_ranking" in philosophy:
            vr = philosophy["value_ranking"]
            candidates.append(Variable(
                name="mate_selection_filter",
                description="择偶筛选机制",
                self_report_gap=behavior.get("filter_gap", 0.0),
                cross_relationship_consistency=behavior.get("filter_consistency", 0.0),
                change_difficulty=0.5,
                data_evidence=behavior.get("filter_evidence", []),
            ))

        # Giving pattern
        if "giving_pattern" in philosophy:
            gp = philosophy["giving_pattern"]
            candidates.append(Variable(
                name="giving_pattern",
                description="付出观念",
                self_report_gap=behavior.get("giving_gap", 0.0),
                cross_relationship_consistency=behavior.get("giving_consistency", 0.0),
                change_difficulty=0.5,
                data_evidence=behavior.get("giving_evidence", []),
            ))

        # Security attachment
        if "security_source" in philosophy:
            candidates.append(Variable(
                name="security_attachment",
                description="安全感来源",
                self_report_gap=behavior.get("security_gap", 0.0),
                cross_relationship_consistency=behavior.get("security_consistency", 0.0),
                change_difficulty=0.6,
                data_evidence=behavior.get("security_evidence", []),
            ))

        # Social media influence
        if "social_media_influence" in philosophy:
            candidates.append(Variable(
                name="social_media",
                description="社交媒体渗透度",
                self_report_gap=behavior.get("social_media_gap", 0.0),
                cross_relationship_consistency=behavior.get("social_media_consistency", 0.0),
                change_difficulty=0.4,
                data_evidence=behavior.get("social_media_evidence", []),
            ))

        # Sort by rank score, take top 2-4
        candidates.sort(key=lambda v: v.rank_score, reverse=True)
        selected = candidates[:4]

        # Ensure at least 2 variables
        if len(selected) < 2 and len(candidates) >= 2:
            selected = candidates[:2]

        return selected

    # ---- Step 2: Branch Building ----
    def build_tree(self, variables: list[Variable], profile: dict, behavior: dict) -> TreeNode:
        """Build the full decision tree from extracted variables."""
        # Root node — user's core pattern
        root = TreeNode(
            label=f"📍 核心模式: {profile.get('core_pattern_description', '基于数据的恋爱模式')}",
            level=0,
        )

        for var in variables:
            var_node = TreeNode(label=f"🔀 {var.description}", level=1, data=var)

            # Branch: keep current behavior
            keep_prob = self._prob.compute_branch_probability(
                var.name, "keep",
                user_consistency=var.cross_relationship_consistency,
                user_change_success=0.0,
            )
            keep_branch = TreeNode(
                label=f"保持当前模式 ({var.description})",
                level=2,
                data=Branch(
                    label="保持",
                    direction="keep",
                    probability=keep_prob,
                    data_evidence=var.data_evidence[0] if var.data_evidence else "",
                ),
            )

            # Add stochastic events under "keep"
            keep_branch.children = self._build_stochastic_layer(var, var_node, keep_prob, behavior)

            # Branch: try to change
            change_prob = self._prob.compute_branch_probability(
                var.name, "change",
                user_consistency=var.cross_relationship_consistency,
                user_change_success=behavior.get("change_success_rate", 0.3),
            )
            change_branch = TreeNode(
                label=f"尝试改变 ({var.description})",
                level=2,
                data=Branch(
                    label="改变",
                    direction="change",
                    probability=change_prob,
                    data_evidence="用户自述'想要改变'",
                ),
            )

            change_branch.children = self._build_stochastic_layer(var, change_branch, change_prob, behavior)

            var_node.children = [keep_branch, change_branch]
            root.children.append(var_node)

        return root

    def _build_stochastic_layer(
        self, var: Variable, parent: TreeNode, parent_prob: Probability, behavior: dict
    ) -> list[TreeNode]:
        """Generate stochastic event nodes and endings under a branch."""
        events = self._get_relevant_events(var, behavior)
        nodes = []

        for event in events:
            event_prob = self._prob.compute_conditional_probability(parent_prob, event.name, event.base_rate)
            event_node = TreeNode(
                label=f"🎲 {event.name}",
                level=3,
                data=event,
            )

            # Generate endings for this event
            endings = self._generate_endings(var, parent.data.direction if parent.data else "keep", event)
            for ending in endings:
                ending_prob = self._prob.compute_conditional_probability(event_prob, ending.title, 0.5)
                ending.probability = ending_prob
                leaf = TreeNode(label=f"{ENDING_EMOJI[ending.ending_type]} {ending.title}", level=4, data=ending)
                event_node.children.append(leaf)

            nodes.append(event_node)

        return nodes

    # ---- Step 3: Ending Generation ----
    def _generate_endings(self, var: Variable, direction: str, event: StochasticEvent) -> list[Ending]:
        """Generate ending scenarios based on variable + direction + stochastic event."""
        endings = []

        # Always generate inertia ending as baseline
        endings.append(Ending(
            title=f"惯性延续: {var.description}不变",
            ending_type=EndingType.INERTIA,
            probability=Probability(0.25, 0.15, 0.35, 0.25, 0.25, 0.0, [], []),
            timeframe="6-12个月",
            story=f"你继续{var.description}的方式。{event.description}发生了。一切如常。",
            gain="熟悉、安全、不需要面对改变的恐惧",
            loss="失去了不同的可能性",
            data_basis=[f"用户过去{var.cross_relationship_consistency*100:.0f}%的关系中保持此模式"],
        ))

        # Growth: if direction is "change"
        if direction == "change":
            endings.append(Ending(
                title=f"成长: 第一次改变{var.description}",
                ending_type=EndingType.GROWTH,
                probability=Probability(0.12, 0.05, 0.20, 0.12, 0.10, 0.08, [], []),
                timeframe="6-18个月",
                story=f"你第一次在{var.description}上做出了不同的选择。一开始很别扭，但结果出乎意料。",
                gain="新的体验、对自我能力的确认",
                loss="旧模式的舒适区",
                data_basis=["用户自述'想要改变'", f"类似人群有{30}%成功改变了类似模式"],
            ))

        # Warning: if direction is "keep"
        if direction == "keep":
            endings.append(Ending(
                title=f"警示: {var.description}极端化",
                ending_type=EndingType.WARNING,
                probability=Probability(0.18, 0.10, 0.28, 0.18, 0.15, 0.12, [], []),
                timeframe="3-5年",
                story=f"{var.description}的模式不断强化。{event.description}加速了这一过程。你发现自己陷入了一个越来越难以打破的循环。",
                gain="短期内的安全感",
                loss="长期的灵活性、对不同可能的开放性",
                data_basis=[f"用户{var.name}的self-report gap为{var.self_report_gap:.2f}，说明用户对自己的模式缺乏自觉"],
            ))

        # Surprise: external event changes things
        endings.append(Ending(
            title=f"意外: {event.name}带来了意想不到的转变",
            ending_type=EndingType.SURPRISE,
            probability=Probability(0.08, 0.02, 0.15, 0.05, 0.08, 0.10, [], []),
            timeframe="1-3年",
            story=f"{event.description}。这个你完全没预料到的事件，反而给了你重新审视{var.description}的机会。",
            gain="意外的视角转换",
            loss="对生活的控制感",
            data_basis=[f"基于{event.name}的概率分布"],
        ))

        return endings

    def _get_relevant_events(self, var: Variable, behavior: dict) -> list[StochasticEvent]:
        """Determine which stochastic events are relevant for this variable."""
        events = []

        # Universal events
        events.append(StochasticEvent(
            name="遇到安全型伴侣",
            description="你遇到了一个依恋风格为安全型的人",
            base_rate=0.25,  # ~25% of population is securely attached
            match_user_pattern=True,
        ))

        events.append(StochasticEvent(
            name="遇到焦虑型伴侣",
            description="你遇到了一个依恋风格为焦虑型的人",
            base_rate=0.19,
            match_user_pattern=behavior.get("past_partner_anxious", False),
        ))

        events.append(StochasticEvent(
            name="生活重大变故",
            description="工作变动/搬家/家庭事件改变了你的生活重心",
            base_rate=0.15,
            match_user_pattern=True,
        ))

        events.append(StochasticEvent(
            name="不符合标准但让你感到不同的人",
            description="你遇到了一个不符合你常规筛选条件但让你感觉不一样的人",
            base_rate=0.20,
            match_user_pattern=behavior.get("has_unexpected_connection", False),
        ))

        return events

    # ---- Step 4: Validation ----
    def validate_tree(self, tree: TreeNode) -> tuple[bool, list[str]]:
        """Validate tree completeness and diversity."""
        issues = []

        # Count ending types
        def collect_endings(node: TreeNode) -> list[Ending]:
            if isinstance(node.data, Ending):
                return [node.data]
            result = []
            for child in node.children:
                result.extend(collect_endings(child))
            return result

        endings = collect_endings(tree)
        ending_types = {e.ending_type for e in endings}

        if len(endings) < 6:
            issues.append(f"Ending count ({len(endings)}) below minimum (6)")

        if len(ending_types) < self.MIN_ENDING_TYPES:
            issues.append(
                f"Ending type diversity ({len(ending_types)}) below minimum ({self.MIN_ENDING_TYPES}). "
                f"Found: {[t.value for t in ending_types]}"
            )

        # Check probabilities sum sensibly
        leaf_probs = [e.probability.value for e in endings]
        total = sum(leaf_probs)
        if total < 0.5 or total > 3.0:
            issues.append(f"Leaf probability sum ({total:.2f}) outside expected range (0.5-3.0)")

        return len(issues) == 0, issues

    # ---- Step 5: Serialization ----
    def tree_to_dict(self, tree: TreeNode) -> dict:
        """Serialize the tree for JSON output / API response."""
        result = {"label": tree.label, "level": tree.level}

        if isinstance(tree.data, Variable):
            result["type"] = "variable"
            result["variable"] = {
                "name": tree.data.name,
                "description": tree.data.description,
                "self_report_gap": round(tree.data.self_report_gap, 2),
                "cross_relationship_consistency": round(tree.data.cross_relationship_consistency, 2),
                "change_difficulty": round(tree.data.change_difficulty, 2),
                "data_evidence": tree.data.data_evidence,
            }
        elif isinstance(tree.data, Branch):
            result["type"] = "branch"
            result["branch"] = {
                "label": tree.data.label,
                "direction": tree.data.direction,
                "probability": tree.data.probability.as_dict(),
            }
        elif isinstance(tree.data, StochasticEvent):
            result["type"] = "stochastic_event"
            result["event"] = {
                "name": tree.data.name,
                "description": tree.data.description,
                "base_rate": tree.data.base_rate,
            }
        elif isinstance(tree.data, Ending):
            result["type"] = "ending"
            result["ending"] = {
                "title": tree.data.title,
                "type": tree.data.ending_type.value,
                "emoji": ENDING_EMOJI[tree.data.ending_type],
                "probability": tree.data.probability.as_dict(),
                "timeframe": tree.data.timeframe,
                "story": tree.data.story,
                "gain": tree.data.gain,
                "loss": tree.data.loss,
                "data_basis": tree.data.data_basis,
            }

        if tree.children:
            result["children"] = [self.tree_to_dict(c) for c in tree.children]

        return result
