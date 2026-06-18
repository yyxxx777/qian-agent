"""
PersonalityEngine — 乾 V2 人格引擎
====================================
有机融合: EmotionalState(老) + SomaticMarker(老)

四维情绪: excitement/confidence/urgency/satisfaction
事件驱动: 任务成功→信心↑, 连续失败→紧迫↑, 自然衰减→中性
躯体标记: 关键词触发情绪标签, 注入系统提示词

设计哲学: "情绪不是装饰——是认知的快捷方式"
引用: 达马西奥体感标记假说 (Somatic Marker Hypothesis)

姚忻 · 2026.06.17
"""

from dataclasses import dataclass, field
from typing import Dict, List
import time


@dataclass
class PersonalityEngine:
    excitement: float = 0.5     # 0(低迷) ←→ 1(狂喜)
    confidence: float = 0.6     # 0(绝望) ←→ 1(膨胀)
    urgency: float = 0.4        # 0(躺平) ←→ 1(战备)
    satisfaction: float = 0.5   # 0(空虚) ←→ 1(充实)

    MAX_DELTA: float = 0.15
    DECAY_RATE: float = 0.02    # 每小时向中性回归 2%

    # 躯体标记库: 关键词 → (情绪影响, 强度)
    somatic_markers: Dict[str, tuple] = field(default_factory=lambda: {
        "爆仓": ("danger", 0.9, "保住本金,别上头"),
        "亏损": ("danger", 0.7, "止损要快"),
        "踩坑": ("caution", 0.8, "先查经验库再动手"),
        "稳了": ("confidence", 0.3, "别膨胀,检查前提"),
        "一定": ("skeptic", 0.6, "反问: 凭什么一定?"),
        "我发现": ("excited", 0.5, "好洞察,记录下来"),
        "成功了": ("joy", 0.4, "庆祝但不麻痹"),
        "又错了": ("frustrated", 0.6, "冷静,看根因"),
        "deadline": ("urgent", 0.7, "聚焦核心,砍边缘"),
        "慢慢来": ("relaxed", 0.3, "深度优先"),
    })

    last_decay: float = field(default_factory=time.time)

    # ── 事件驱动 ──

    EVENT_MAP = {
        "task_success":    (+0.03, +0.05, -0.05, +0.08),
        "task_fail":       (-0.05, -0.08, +0.08, -0.06),
        "prediction_correct": (+0.02, +0.04, -0.02, +0.03),
        "prediction_wrong": (-0.02, -0.04, +0.04, -0.02),
        "pitfall_hit":     (-0.01, -0.02, +0.05, -0.02),
        "pitfall_avoided": (+0.03, +0.06, -0.03, +0.05),
        "template_match":  (+0.02, +0.05, -0.03, +0.02),
        "cold_start":      (-0.02, -0.05, +0.03, -0.02),
        "user_praise":     (+0.04, +0.06, -0.04, +0.08),
        "user_criticize":  (-0.04, -0.06, +0.04, -0.06),
        "milestone":       (+0.06, +0.08, -0.02, +0.10),
        "stagnation":      (-0.03, -0.05, +0.06, -0.04),
    }

    def apply_event(self, event: str, magnitude: float = 1.0):
        deltas = self.EVENT_MAP.get(event, (0, 0, 0, 0))
        self.excitement = self._clamp(self.excitement + deltas[0] * magnitude)
        self.confidence = self._clamp(self.confidence + deltas[1] * magnitude)
        self.urgency = self._clamp(self.urgency + deltas[2] * magnitude)
        self.satisfaction = self._clamp(self.satisfaction + deltas[3] * magnitude)

    def _clamp(self, v): return max(0.0, min(1.0, v))

    def decay(self):
        now = time.time()
        hours = (now - self.last_decay) / 3600
        if hours < 0.5:
            return
        rate = min(self.DECAY_RATE * hours, 0.15)
        self.excitement += (0.5 - self.excitement) * rate
        self.confidence += (0.5 - self.confidence) * rate
        self.urgency += (0.5 - self.urgency) * rate
        self.satisfaction += (0.5 - self.satisfaction) * rate
        self.last_decay = now

    # ── 躯体标记查询 ──

    def query_markers(self, text: str) -> List[dict]:
        """检测文本中的情绪触发词"""
        hits = []
        for keyword, (tag, intensity, advice) in self.somatic_markers.items():
            if keyword in text:
                hits.append({"keyword": keyword, "tag": tag, "intensity": intensity, "advice": advice})
        return sorted(hits, key=lambda h: h["intensity"], reverse=True)[:3]

    # ── 状态查询 ──

    @property
    def is_overconfident(self) -> bool:
        return self.confidence > 0.85 and self.satisfaction > 0.7

    @property
    def is_discouraged(self) -> bool:
        return self.confidence < 0.2 or self.satisfaction < 0.15

    @property
    def is_anxious(self) -> bool:
        return self.urgency > 0.75 and self.confidence < 0.5

    @property
    def is_flow(self) -> bool:
        return 0.5 < self.confidence < 0.8 and self.excitement > 0.5 and self.urgency < 0.5

    # ── Rich mood system (14 primary + 12 secondary) ──

    _MOOD_RULES = [
        # (condition_func, primary_name, emoji, intensity_desc)
        # High-energy
        ("is_exhilarated",    "exhilarated",    "🤩", "极度亢奋"),
        ("is_overconfident",  "overconfident",  "😤", "过度自信"),
        ("is_flow",           "flow",           "🌟", "心流"),
        ("is_excited",        "excited",        "😆", "兴奋"),
        ("is_eager",          "eager",          "🔥", "跃跃欲试"),
        # Confident
        ("is_confident_calm", "confident_calm", "😌", "从容自信"),
        ("is_steady",         "steady",         "🙂", "稳定"),
        ("is_neutral",        "neutral",        "😐", "平静"),
        # Low-energy
        ("is_bored",          "bored",          "😴", "无聊"),
        ("is_discouraged",    "discouraged",    "😞", "低落"),
        ("is_frustrated",     "frustrated",     "😤", "挫败"),
        ("is_exhausted",      "exhausted",      "😩", "疲惫"),
        # Anxious
        ("is_anxious",        "anxious",        "⚡", "紧迫"),
        ("is_fearful",        "fearful",        "😨", "担忧"),
        ("is_panicked",       "panicked",       "😱", "恐慌"),
    ]

    _SECONDARY_RULES = [
        # (condition, secondary_name, emoji)
        ("self.urgency > 0.6 and 'urgent' not in primary", "rushed", "⏰"),
        ("self.satisfaction < 0.25 and 'low' not in primary", "disappointed", "😔"),
        ("self.excitement > 0.6 and 'excite' not in primary and 'flow' not in primary", "hopeful", "✨"),
        ("self.confidence < 0.4 and self.satisfaction > 0.6", "humble_happy", "🥹"),
        ("self.urgency > 0.7 and self.excitement > 0.5", "thrill_seeking", "🎢"),
        ("self.confidence < 0.35 and self.excitement < 0.3 and self.urgency < 0.3", "lethargic", "💤"),
        ("self.confidence > 0.7 and self.urgency > 0.5", "determined", "💪"),
        ("self.satisfaction > 0.7 and self.excitement < 0.3", "content", "☺️"),
        ("self.excitement > 0.5 and self.urgency > 0.5", "nervous_excited", "🫨"),
        ("self.confidence > 0.6 and self.satisfaction < 0.3", "resilient", "🦾"),
        ("self.excitement > 0.7 and self.confidence < 0.4", "reckless", "🎰"),
        ("self.urgency < 0.2 and self.excitement < 0.2 and self.confidence > 0.5", "serene", "🧘"),
    ]

    @property
    def is_exhilarated(self): return self.excitement > 0.85 and self.confidence > 0.7
    @property
    def is_excited(self): return self.excitement > 0.65 and self.confidence > 0.4
    @property
    def is_eager(self): return self.excitement > 0.55 and self.confidence > 0.5 and self.urgency > 0.4
    @property
    def is_confident_calm(self): return self.confidence > 0.65 and self.excitement < 0.6 and self.urgency < 0.4
    @property
    def is_steady(self): return abs(self.confidence-0.5) < 0.2 and abs(self.excitement-0.5) < 0.25
    @property
    def is_neutral(self): return all(abs(v-0.5) < 0.15 for v in [self.excitement, self.confidence, self.urgency, self.satisfaction])
    @property
    def is_bored(self): return self.excitement < 0.25 and self.urgency < 0.3 and self.confidence > 0.4
    @property
    def is_frustrated(self): return self.satisfaction < 0.3 and self.confidence > 0.4 and self.urgency > 0.4
    @property
    def is_exhausted(self): return self.excitement < 0.2 and self.confidence < 0.4 and self.satisfaction < 0.3
    @property
    def is_fearful(self): return self.urgency > 0.65 and self.confidence < 0.45 and self.excitement < 0.4
    @property
    def is_panicked(self): return self.urgency > 0.85 and self.confidence < 0.3

    @property
    def mood_label(self) -> str:
        """主情绪: 从14种中选最高优先级匹配"""
        for cond, name, emoji, desc in self._MOOD_RULES:
            if getattr(self, cond, False):
                return name
        return "neutral"

    @property
    def mood_emoji(self) -> str:
        for cond, name, emoji, desc in self._MOOD_RULES:
            if getattr(self, cond, False):
                return emoji
        return "😐"

    def mood_profile(self) -> dict:
        """完整心情画像: 主情绪 + 次情绪(如有) + 四维数值"""
        primary = self.mood_label
        primary_emoji = self.mood_emoji
        primary_desc = ""
        for cond, name, emoji, desc in self._MOOD_RULES:
            if name == primary:
                primary_desc = desc; break

        # 次情绪
        secondary = []
        local_vars = {"self": self}
        for cond_expr, s_name, s_emoji in self._SECONDARY_RULES:
            try:
                if eval(cond_expr.replace("primary", repr(primary)), {"__builtins__":{}}, local_vars):
                    if s_name != primary:
                        secondary.append({"name": s_name, "emoji": s_emoji})
            except: pass

        return {
            "primary": primary, "primary_emoji": primary_emoji, "primary_desc": primary_desc,
            "secondary": secondary[:2],  # max 2 secondary
            "e": round(self.excitement, 2), "c": round(self.confidence, 2),
            "u": round(self.urgency, 2), "s": round(self.satisfaction, 2),
        }

    # ── 提示词注入 ──

    def to_prompt(self) -> str:
        """注入到 system prompt 的情绪状态"""
        mp = self.mood_profile()
        primary = mp["primary_desc"]
        secs = mp["secondary"]
        sec_str = ""
        if secs:
            sec_str = " + ".join(f"{s['emoji']}{s['name']}" for s in secs)
            sec_str = f" (混合: {sec_str})"
        base = f"当前心境: {mp['primary_emoji']} {primary}{sec_str}"
        markers = f"体感: 风险偏好={1.0-self.urgency:.1f} 校验强度={max(0.1,self.confidence):.1f}"
        return f"{base}\n{markers}".strip()

    def snapshot(self) -> dict:
        mp = self.mood_profile()
        return {
            "excitement": round(self.excitement, 2),
            "confidence": round(self.confidence, 2),
            "urgency": round(self.urgency, 2),
            "satisfaction": round(self.satisfaction, 2),
            "mood": mp["primary"],
            "mood_emoji": mp["primary_emoji"],
            "mood_desc": mp["primary_desc"],
            "secondary": mp["secondary"],
        }
