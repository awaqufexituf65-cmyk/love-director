"""Profile engine — computes the 3-layer user profile and gap analysis."""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class GapFinding:
    dimension: str
    self_report: str        # what user says
    behavior_data: str      # what data shows
    gap_severity: float     # 0-1
    evidence: list[str] = field(default_factory=list)


@dataclass
class ProfileResult:
    self_report: dict       # Phase 1A questionnaire
    behavior: dict          # Phase 1B extracted from chat data
    gaps: list[GapFinding]  # Phase 1C gap analysis
    vulnerability_score: float  # 0-1
    vulnerability_factors: list[str]


class ProfileEngine:
    """Analyzes self-report vs behavioral data to find gaps."""

    # Dimensions to check for gaps
    GAP_DIMENSIONS = [
        "mate_selection_criteria",  # what user says they value vs what they actually filter on
        "conflict_style",           # claimed vs actual conflict response
        "initiative_balance",       # who initiates conversations
        "emotional_speed",          # how fast they get attached
        "social_disclosure",        # how much they share vs what they claim
    ]

    def compute_profile(self, self_report: dict, chat_analysis: dict) -> ProfileResult:
        """Fuse self-report questionnaire with chat analysis into a 3-layer profile."""
        behavior = self._extract_behavior(chat_analysis)
        gaps = self._find_gaps(self_report, behavior, chat_analysis)
        vuln = self._assess_vulnerability(self_report, gaps)

        return ProfileResult(
            self_report=self_report,
            behavior=behavior,
            gaps=gaps,
            vulnerability_score=vuln[0],
            vulnerability_factors=vuln[1],
        )

    def _extract_behavior(self, chat_analysis: dict) -> dict:
        """Extract behavioral metrics from chat analysis output."""
        return {
            "initiative_ratio": chat_analysis.get("user_initiate_ratio", 0.5),
            "avg_response_time_minutes": chat_analysis.get("avg_response_time", 30),
            "conflict_avoidance_index": chat_analysis.get("conflict_avoidance_score", 0.5),
            "emotional_velocity_days": chat_analysis.get("avg_time_to_intimacy", 7),
            "partner_type_consistency": chat_analysis.get("partner_similarity_score", 0.5),
            "giving_imbalance": chat_analysis.get("message_length_ratio", 1.0),
        }

    def _find_gaps(self, self_report: dict, behavior: dict, chat_analysis: dict) -> list[GapFinding]:
        """Find gaps between what user claims and what data shows."""
        gaps = []

        # Gap 1: Mate selection criteria
        if "value_ranking" in self_report:
            claimed_top = self_report["value_ranking"].get("claimed", {}).get("1st", "")
            actual_top = self_report["value_ranking"].get("actual", {}).get("1st", "")
            if claimed_top and actual_top and claimed_top != actual_top:
                gaps.append(GapFinding(
                    dimension="mate_selection_criteria",
                    self_report=f"声称最看重: {claimed_top}",
                    behavior_data=f"实际因: {actual_top} 而拒绝/分手",
                    gap_severity=0.8,
                    evidence=[f"过去{self_report.get('relationship_count', 0)}段关系中，分手原因排第一的是{actual_top}"],
                ))

        # Gap 2: Conflict style
        if "conflict_belief" in self_report and "conflict_avoidance_index" in behavior:
            claimed_conflict = self_report["conflict_belief"].get("self_description", "")
            avoidance = behavior["conflict_avoidance_index"]
            if avoidance > 0.6 and "不喜欢回避" in str(claimed_conflict):
                gaps.append(GapFinding(
                    dimension="conflict_style",
                    self_report=f"自述: {claimed_conflict}",
                    behavior_data=f"冲突回避指数: {avoidance:.2f} (>0.6=显著回避模式)",
                    gap_severity=min(0.9, avoidance),
                    evidence=[f"在{chat_analysis.get('relationship_count', 0)}段关系中均检测到回避模式"],
                ))

        # Gap 3: Initiative balance
        ratio = behavior.get("initiative_ratio", 0.5)
        if ratio < 0.3:
            gaps.append(GapFinding(
                dimension="initiative_balance",
                self_report="用户可能认为自己'挺主动的'",
                behavior_data=f"实际主动发起对话比例: {ratio:.0%}",
                gap_severity=0.7,
                evidence=[f"在分析的关系中，用户平均主动发起对话比例为{ratio:.0%}"],
            ))
        elif ratio > 0.8:
            gaps.append(GapFinding(
                dimension="initiative_balance",
                self_report="用户可能认为自己'随缘'",
                behavior_data=f"实际主动发起对话比例: {ratio:.0%}（过高，可能为讨好模式）",
                gap_severity=0.6,
                evidence=[],
            ))

        # Gap 4: Emotional speed
        velocity = behavior.get("emotional_velocity_days", 30)
        if velocity < 7:
            gaps.append(GapFinding(
                dimension="emotional_speed",
                self_report="用户自述的确认关系速度",
                behavior_data=f"实际平均{velocity}天确认关系（<7天=闪电型）",
                gap_severity=0.6,
                evidence=[f"数据: 最快{chat_analysis.get('fastest_confirm_days', 0)}天"],
            ))

        # Gap 5: Social media influence
        if "social_media_influence" in self_report:
            claimed = self_report["social_media_influence"].get("self_awareness", "")
            influencer_count = self_report["social_media_influence"].get("followed_influencers", 0)
            if influencer_count > 10 and "没什么影响" in str(claimed):
                gaps.append(GapFinding(
                    dimension="social_disclosure",
                    self_report=f"自述'社交媒体对我没什么影响'",
                    behavior_data=f"实际关注了{influencer_count}个恋爱/婚恋博主",
                    gap_severity=0.7,
                    evidence=[f"根据北师大(2025)研究，关注>10个博主与择偶标准被人为抬高相关"],
                ))

        return gaps

    def _assess_vulnerability(self, self_report: dict, gaps: list[GapFinding]) -> tuple[float, list[str]]:
        """Assess user vulnerability based on profile data."""
        score = 0.0
        factors = []

        age = self_report.get("age", 25)
        if age >= 28 and self_report.get("purpose") == "marriage_oriented":
            score += 0.2
            factors.append("年龄焦虑 + 婚姻导向 → 时间压力")

        if self_report.get("parent_marriage") in ["divorced", "high_conflict"]:
            score += 0.15
            factors.append("原生家庭婚姻不稳定 → 可能缺乏健康关系模板")

        if self_report.get("social_support") == "none":
            score += 0.2
            factors.append("缺乏社交支持系统 → 孤立无援时更依赖伴侣")

        if self_report.get("recent_breakup_months", 99) < 3:
            score += 0.25
            factors.append("刚结束关系 (<3个月) → 处于反弹期")

        gap_count = len([g for g in gaps if g.gap_severity > 0.6])
        if gap_count >= 3:
            score += 0.15
            factors.append(f"显著自述-行为差距 ({gap_count}项) → 对自身模式缺乏自觉")

        large_gaps = [g for g in gaps if g.gap_severity > 0.7]
        if large_gaps:
            score += 0.1
            factors.append(f"严重盲区: {', '.join(g.dimension for g in large_gaps)}")

        score = min(1.0, score)
        return score, factors
