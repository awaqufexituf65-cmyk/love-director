"""Chat analysis engine — NLP pipeline for WeChat chat records.

Requires: pip install snownlp jieba
Optional: 大连理工大学中文情感词典 (download from https://github.com/dongrixinyu/chinese_emotion_lexicon)
"""

import re
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class ChatAnalysisResult:
    """Output of chat record analysis."""
    message_count: int
    user_message_count: int
    other_message_count: int
    user_initiate_ratio: float           # how often user starts conversations
    avg_response_time_minutes: float     # avg time to reply
    conflict_avoidance_score: float      # 0-1: higher = more avoidance
    avg_time_to_intimacy_days: float     # days until intimate language appears
    sentiment_curve: list[tuple[str, float]]  # (date, sentiment_score)
    emotion_distribution: dict[str, float]    # joy/anger/sadness/fear/surprise/disgust
    topic_distribution: dict[str, float]      # work/relationship/money/daily/conflict
    partner_similarity_score: float       # how similar past partners are
    message_length_ratio: float           # user msg length / other msg length
    keywords: list[str]                   # top emotional keywords
    conflict_episodes: list[dict]         # detected conflict episodes


class ChatAnalyzer:
    """Analyzes chat text to extract behavioral patterns."""

    # Chinese emotional keywords (simplified — extend with full lexicon)
    POSITIVE_KEYWORDS = ["爱", "喜欢", "想你", "宝贝", "亲爱的", "甜蜜", "幸福", "开心", "哈哈哈"]
    NEGATIVE_KEYWORDS = ["烦", "累", "压力", "不想", "算了", "随便", "无语", "生气", "难过"]
    CONFLICT_KEYWORDS = ["你怎么", "为什么不", "你又", "我错了", "对不起", "算了不说了", "随便你"]
    MONEY_KEYWORDS = ["钱", "投资", "理财", "买", "花销", "工资", "收入", "房子", "彩礼"]
    INTIMACY_KEYWORDS = ["宝贝", "老公", "老婆", "亲爱的", "想你", "爱你", "我们以后", "结婚"]

    def __init__(self):
        self._snownlp_available = False
        try:
            from snownlp import SnowNLP
            self._SnowNLP = SnowNLP
            self._snownlp_available = True
        except ImportError:
            pass

    def analyze_text(self, text: str) -> ChatAnalysisResult:
        """Analyze raw chat text (WeFlow TXT export format)."""
        messages = self._parse_messages(text)
        if not messages:
            return self._empty_result()

        user_msgs = [m for m in messages if m["is_user"]]
        other_msgs = [m for m in messages if not m["is_user"]]

        return ChatAnalysisResult(
            message_count=len(messages),
            user_message_count=len(user_msgs),
            other_message_count=len(other_msgs),
            user_initiate_ratio=self._calc_initiative_ratio(messages),
            avg_response_time_minutes=self._calc_avg_response_time(messages),
            conflict_avoidance_score=self._calc_conflict_avoidance(messages),
            avg_time_to_intimacy_days=self._calc_time_to_intimacy(messages),
            sentiment_curve=self._calc_sentiment_curve(messages),
            emotion_distribution=self._calc_emotion_distribution(messages),
            topic_distribution=self._calc_topic_distribution(messages),
            partner_similarity_score=0.5,  # needs multi-chat comparison
            message_length_ratio=self._calc_length_ratio(user_msgs, other_msgs),
            keywords=self._extract_keywords(messages),
            conflict_episodes=self._detect_conflicts(messages),
        )

    def analyze_multiple_chats(self, chats: list[str]) -> ChatAnalysisResult:
        """Analyze multiple chat exports for cross-relationship comparison."""
        results = [self.analyze_text(c) for c in chats if c.strip()]

        if not results:
            return self._empty_result()
        if len(results) == 1:
            return results[0]

        # Cross-relationship metrics
        merged = results[0]
        merged.partner_similarity_score = self._calc_partner_similarity(results)

        return merged

    # ---- Parsing ----
    def _parse_messages(self, text: str) -> list[dict]:
        """Parse WeFlow TXT format: 'YYYY-MM-DD HH:MM:SS Name: content'"""
        messages = []
        pattern = r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+([^:]+):\s+(.+)'

        for line in text.split("\n"):
            match = re.match(pattern, line.strip())
            if match:
                timestamp, sender, content = match.groups()
                messages.append({
                    "timestamp": timestamp.strip(),
                    "sender": sender.strip(),
                    "content": content.strip(),
                })

        return messages

    # ---- Metrics ----
    def _calc_initiative_ratio(self, messages: list[dict]) -> float:
        """Calculate how often user initiates a conversation (after >4h gap)."""
        if len(messages) < 2:
            return 0.5
        user_starts = 0
        for i, msg in enumerate(messages):
            if i == 0 and msg["is_user"]:
                user_starts += 1
            elif i > 0 and msg["is_user"]:
                # Check if previous message was >4h ago
                prev = messages[i - 1]
                if not prev["is_user"]:  # previous was from other
                    user_starts += 1
        return user_starts / max(1, len([m for m in messages if m["is_user"]]))

    def _calc_avg_response_time(self, messages: list[dict]) -> float:
        """Average response time in minutes (simplified)."""
        from datetime import datetime
        response_times = []
        for i in range(1, len(messages)):
            if messages[i]["is_user"] != messages[i - 1]["is_user"]:
                try:
                    t1 = datetime.strptime(messages[i - 1]["timestamp"], "%Y-%m-%d %H:%M:%S")
                    t2 = datetime.strptime(messages[i]["timestamp"], "%Y-%m-%d %H:%M:%S")
                    diff = (t2 - t1).total_seconds() / 60
                    if diff < 1440:  # ignore >24h gaps
                        response_times.append(diff)
                except ValueError:
                    pass
        return sum(response_times) / len(response_times) if response_times else 30.0

    def _calc_conflict_avoidance(self, messages: list[dict]) -> float:
        """Detect conflict avoidance patterns. Higher = more avoidance."""
        user_msgs = [m for m in messages if m["is_user"]]
        if not user_msgs:
            return 0.5

        # Count conflict-related content
        conflict_related = sum(1 for m in user_msgs
                              if any(kw in m["content"] for kw in self.CONFLICT_KEYWORDS))
        avoidance_markers = sum(1 for m in user_msgs
                               if any(kw in m["content"] for kw in ["算了", "不说了", "随便", "没事"]))

        avoidance_ratio = avoidance_markers / len(user_msgs)
        return min(1.0, avoidance_ratio * 3)  # scale up

    def _calc_time_to_intimacy(self, messages: list[dict]) -> float:
        """Days until first intimate language appears."""
        from datetime import datetime
        if not messages:
            return 30.0

        try:
            start_date = datetime.strptime(messages[0]["timestamp"], "%Y-%m-%d %H:%M:%S")
        except (ValueError, IndexError):
            return 30.0

        other_msgs = [m for m in messages if not m["is_user"]]
        for msg in other_msgs:
            if any(kw in msg["content"] for kw in self.INTIMACY_KEYWORDS):
                try:
                    intimate_date = datetime.strptime(msg["timestamp"], "%Y-%m-%d %H:%M:%S")
                    return (intimate_date - start_date).days
                except ValueError:
                    continue
        return 30.0

    def _calc_sentiment_curve(self, messages: list[dict]) -> list[tuple[str, float]]:
        """Sentiment score over time."""
        curve = []
        for msg in messages:
            score = self._get_sentiment(msg["content"])
            date = msg["timestamp"][:10]  # YYYY-MM-DD
            curve.append((date, score))
        return curve

    def _get_sentiment(self, text: str) -> float:
        """Get sentiment score for a single message."""
        if self._snownlp_available:
            try:
                return self._SnowNLP(text).sentiments
            except Exception:
                pass
        # Fallback: keyword-based
        pos = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text)
        neg = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text)
        if pos + neg == 0:
            return 0.5
        return pos / (pos + neg)

    def _calc_emotion_distribution(self, messages: list[dict]) -> dict[str, float]:
        """Classify emotions across all messages."""
        counts = {"joy": 0, "anger": 0, "sadness": 0, "fear": 0, "surprise": 0, "disgust": 0, "neutral": 0}
        joy_kw = ["哈哈", "开心", "喜欢", "爱", "好", "棒", "太好了", "嘻嘻"]
        anger_kw = ["气", "烦", "凭什么", "操", "无语", "你TM"]
        sadness_kw = ["难过", "哭", "伤心", "想哭", "遗憾", "算了"]

        for msg in messages:
            text = msg["content"]
            if any(kw in text for kw in joy_kw):
                counts["joy"] += 1
            elif any(kw in text for kw in anger_kw):
                counts["anger"] += 1
            elif any(kw in text for kw in sadness_kw):
                counts["sadness"] += 1
            else:
                counts["neutral"] += 1

        total = max(1, sum(counts.values()))
        return {k: v / total for k, v in counts.items()}

    def _calc_topic_distribution(self, messages: list[dict]) -> dict[str, float]:
        """Estimate topic distribution."""
        topics = {"work": 0, "relationship": 0, "money": 0, "daily": 0, "conflict": 0}
        for msg in messages:
            text = msg["content"]
            if any(kw in text for kw in ["工作", "加班", "老板", "同事", "项目"]):
                topics["work"] += 1
            if any(kw in text for kw in ["想", "爱", "在乎", "我们", "在一起"]):
                topics["relationship"] += 1
            if any(kw in text for kw in self.MONEY_KEYWORDS):
                topics["money"] += 1
            if any(kw in text for kw in self.CONFLICT_KEYWORDS):
                topics["conflict"] += 1
            topics["daily"] += 1  # baseline

        total = max(1, sum(topics.values()))
        return {k: v / total for k, v in topics.items()}

    def _calc_length_ratio(self, user_msgs: list, other_msgs: list) -> float:
        """User avg message length / other avg message length. <1 = user writes less."""
        user_avg = sum(len(m["content"]) for m in user_msgs) / max(1, len(user_msgs))
        other_avg = sum(len(m["content"]) for m in other_msgs) / max(1, len(other_msgs))
        return user_avg / max(1, other_avg)

    def _extract_keywords(self, messages: list[dict]) -> list[str]:
        """Extract top emotional keywords."""
        all_words = []
        for msg in messages:
            for kw in self.POSITIVE_KEYWORDS + self.NEGATIVE_KEYWORDS + self.CONFLICT_KEYWORDS:
                if kw in msg["content"]:
                    all_words.append(kw)
        counter = Counter(all_words)
        return [word for word, _ in counter.most_common(20)]

    def _detect_conflicts(self, messages: list[dict]) -> list[dict]:
        """Detect discrete conflict episodes."""
        episodes = []
        current_conflict = []
        in_conflict = False

        for msg in messages:
            if any(kw in msg["content"] for kw in self.CONFLICT_KEYWORDS):
                if not in_conflict:
                    in_conflict = True
                    current_conflict = []
                current_conflict.append(msg)
            else:
                if in_conflict and len(current_conflict) > 3:
                    episodes.append({
                        "start": current_conflict[0]["timestamp"],
                        "end": current_conflict[-1]["timestamp"],
                        "message_count": len(current_conflict),
                        "resolution": self._classify_resolution(current_conflict),
                    })
                in_conflict = False
                current_conflict = []

        return episodes

    def _classify_resolution(self, conflict_msgs: list[dict]) -> str:
        """Classify how a conflict ended."""
        last = conflict_msgs[-1]["content"]
        if any(kw in last for kw in ["算了", "不说了", "随便"]):
            return "avoidance"
        if any(kw in last for kw in ["对不起", "我错了"]):
            return "apology"
        if any(kw in last for kw in ["我理解", "你说得对", "我们"]):
            return "repair"
        return "unresolved"

    def _calc_partner_similarity(self, results: list["ChatAnalysisResult"]) -> float:
        """Estimate how similar past partners were (0-1)."""
        if len(results) < 2:
            return 0.5
        # Compare topic distributions across chats
        similarities = []
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                topics_i = set(k for k, v in results[i].topic_distribution.items() if v > 0.15)
                topics_j = set(k for k, v in results[j].topic_distribution.items() if v > 0.15)
                if topics_i:
                    similarity = len(topics_i & topics_j) / len(topics_i | topics_j)
                    similarities.append(similarity)

        return sum(similarities) / len(similarities) if similarities else 0.5

    def _empty_result(self) -> ChatAnalysisResult:
        return ChatAnalysisResult(
            message_count=0, user_message_count=0, other_message_count=0,
            user_initiate_ratio=0.5, avg_response_time_minutes=30.0,
            conflict_avoidance_score=0.5, avg_time_to_intimacy_days=30.0,
            sentiment_curve=[], emotion_distribution={}, topic_distribution={},
            partner_similarity_score=0.5, message_length_ratio=1.0,
            keywords=[], conflict_episodes=[],
        )
