"""Probability engine for Love Director's decision tree.

Probability formula:
    P(branch) = w_user * P_user + w_pop * P_pop + w_research * P_research
    w_user + w_pop + w_research = 1.0 (default: 0.4 / 0.4 / 0.2)
"""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Probability:
    """A probability value with full provenance."""
    value: float          # 0.0 to 1.0
    confidence_low: float  # lower bound of confidence interval
    confidence_high: float # upper bound
    user_factor: float     # P_user contribution
    pop_factor: float      # P_pop contribution
    research_factor: float # P_research contribution
    data_sources: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "value": round(self.value * 100),
            "display": f"~{round(self.value * 100)}%",
            "confidence_interval": f"{round(self.confidence_low*100)}%-{round(self.confidence_high*100)}%",
            "breakdown": {
                "user_behavior": round(self.user_factor * 100),
                "population_stats": round(self.pop_factor * 100),
                "research_evidence": round(self.research_factor * 100),
            },
            "data_sources": self.data_sources,
            "uncertainties": self.uncertainties,
        }

    def __repr__(self):
        return f"Probability({self.as_dict()['display']}, CI: {self.as_dict()['confidence_interval']})"


class ProbabilityEngine:
    """Computes branch probabilities from user data + population stats + research."""

    def __init__(self, stats_baseline: Optional[dict] = None):
        """
        Args:
            stats_baseline: Loaded stats-baseline.json or equivalent dict.
        """
        self._stats = stats_baseline or {}
        self._w_user = 0.4
        self._w_pop = 0.4
        self._w_research = 0.2

    # ---- Public API ----
    def compute_branch_probability(
        self,
        variable_name: str,
        direction: str,  # "keep" or "change"
        user_consistency: float,   # 0-1: how consistently user has done this in past
        user_change_success: float, # 0-1: if "change", how often user has succeeded
    ) -> Probability:
        """
        Compute probability for a single branch of a variable.

        Args:
            variable_name: e.g. "conflict_avoidance"
            direction: "keep" (maintain current behavior) or "change" (try new behavior)
            user_consistency: how often user has done this behavior across past relationships
            user_change_success: only used for "change" direction
        """
        # P_user: based on user's own history
        if direction == "keep":
            p_user = user_consistency
        else:
            p_user = 1.0 - user_consistency
            p_user *= max(0.1, user_change_success)  # dampen by change track record

        # P_pop: population-level probability
        p_pop = self._get_population_probability(variable_name, direction)

        # P_research: research-based adjustment
        p_research = self._get_research_factor(variable_name, direction)

        # Weighted combination
        raw_value = (
            self._w_user * p_user +
            self._w_pop * p_pop +
            self._w_research * p_research
        )

        # Clamp to [0.01, 0.99] — nothing is 0% or 100%
        value = max(0.01, min(0.99, raw_value))

        # 95% confidence interval (±15%)
        margin = 0.15
        ci_low = max(0.01, value - margin)
        ci_high = min(0.99, value + margin)

        return Probability(
            value=value,
            confidence_low=ci_low,
            confidence_high=ci_high,
            user_factor=p_user,
            pop_factor=p_pop,
            research_factor=p_research,
            data_sources=self._get_sources(variable_name),
            uncertainties=self._get_uncertainties(variable_name, direction),
        )

    def compute_conditional_probability(
        self,
        parent_prob: Probability,
        event_name: str,
        base_rate: float,
    ) -> Probability:
        """Compute conditional probability for a stochastic event node."""
        value = parent_prob.value * base_rate
        value = max(0.01, min(0.99, value))

        return Probability(
            value=value,
            confidence_low=max(0.01, value - 0.10),
            confidence_high=min(0.99, value + 0.10),
            user_factor=base_rate * 0.5,
            pop_factor=base_rate * 0.3,
            research_factor=base_rate * 0.2,
            data_sources=[f"conditional on {event_name}"],
            uncertainties=["Conditional probability — actual rate depends on unmodeled factors"],
        )

    # ---- Internal ----
    def _get_population_probability(self, variable: str, direction: str) -> float:
        """Pull population-level probability from stats baseline."""
        stats = self._stats

        # Default population baselines based on research
        baselines = {
            "conflict_avoidance": {"keep": 0.41, "change": 0.59},   # 41% use avoidance (Yan 2024)
            "lightning_confirmation": {"keep": 0.35, "change": 0.65},
            "material_priority": {"keep": 0.68, "change": 0.32},     # 68% calculate gains/losses
            "social_media_influence": {"keep": 0.72, "change": 0.28}, # 72% influenced
            "external_security": {"keep": 0.61, "change": 0.39},     # 61% cite bride price
        }

        return baselines.get(variable, {"keep": 0.50, "change": 0.50}).get(direction, 0.50)

    def _get_research_factor(self, variable: str, direction: str) -> float:
        """Research-based adjustment factor."""
        factors = {
            "conflict_avoidance": 0.35 if direction == "keep" else 0.65,  # Gottman: repair matters
            "lightning_confirmation": 0.30 if direction == "keep" else 0.70,
            "material_priority": 0.40 if direction == "keep" else 0.60,
        }
        return factors.get(variable, 0.50)

    def _get_sources(self, variable: str) -> list[str]:
        mapping = {
            "conflict_avoidance": ["Yan et al. (2024)", "Gottman (1994)"],
            "lightning_confirmation": ["Altman & Taylor (1973) — 社会渗透理论"],
            "material_priority": ["中科院心理所 (2024)", "Hatfield公平理论 (1993)"],
            "social_media_influence": ["北师大×小红书 (2026)", "刘彦&崔英豪 (2025)"],
            "external_security": ["Bowlby依恋理论", "Hazan & Shaver (1987)"],
        }
        return mapping.get(variable, ["全国统计数据"])

    def _get_uncertainties(self, variable: str, direction: str) -> list[str]:
        base = [
            "概率基于群体统计，个体结果可能不同",
            "无法量化的因素: 个人意志力、外部环境突变",
        ]
        if direction == "change":
            base.append("用户的改变意愿强度无法客观测量")
        return base

    # ---- Configuration ----
    def set_weights(self, w_user: float, w_pop: float, w_research: float) -> None:
        total = w_user + w_pop + w_research
        self._w_user = w_user / total
        self._w_pop = w_pop / total
        self._w_research = w_research / total
