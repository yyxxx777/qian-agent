"""
Divergent Mode + Cross-Stimulus Engine — 乾 V2.5 创造力引擎
=============================================================
发散模式: 当任务需要创造力时, 降低校验强度, 注入跨界刺激
跨界刺激: 从不相关模板拉取经验, 催化创造性联想

设计哲学:
  "创造力不是生成随机想法, 是在看似无关的东西之间发现连接"
  — 乾不增加创造力, 乾只是不阻碍创造力, 并催化跨界连接

姚忻 · 2026.06.17
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import random


CREATIVE_TASK_TYPES = {"design_planning", "text_generation", "code_explanation",
                      "design", "write", "creative"}
DIVERGENT_TRIGGERS = ["创意", "创新", "发散", "自由发挥", "creative", "novel",
                      "brainstorm", "invent", "与众不同", "别出心裁"]


@dataclass
class DivergentConfig:
    active: bool = False
    check_intensity: float = 0.3      # 校验强度降至30%
    bias_check: bool = False           # 跳过偏误检查(允许"有益的偏差")
    stimulus_sources: int = 2          # 跨界刺激源数量
    temperature_boost: float = 0.2     # LLM温度提升


class DivergentEngine:
    """发散模式 + 跨界刺激引擎"""

    def __init__(self):
        self.total_divergent_sessions = 0
        self.total_stimuli_injected = 0

    def should_diverge(self, task: str, template_type: str) -> bool:
        """判断是否激活发散模式"""
        if template_type in CREATIVE_TASK_TYPES:
            return True
        tl = task.lower()
        if any(t in tl for t in DIVERGENT_TRIGGERS):
            return True
        return False

    def get_config(self, task: str, template_type: str) -> DivergentConfig:
        """获取发散模式配置"""
        if not self.should_diverge(task, template_type):
            return DivergentConfig(active=False)

        self.total_divergent_sessions += 1
        return DivergentConfig(
            active=True,
            check_intensity=0.3,
            bias_check=False,
            stimulus_sources=2,
            temperature_boost=0.2,
        )

    def inject_stimulus(self, template_db, current_type: str) -> Optional[str]:
        """
        跨界刺激: 从不相关模板中随机拉取经验, 催化联想
        
        "你上次做财务分析时学到: 先验证基准假设。
         这次写小说——有没有一个需要验证的'故事假设'?"
        """
        if not template_db:
            return None

        # 找与当前类型不同的模板
        other_templates = [t for tid, t in template_db.templates.items()
                          if t.template_type != current_type and t.hit_count > 0]
        if not other_templates:
            return None

        source = random.choice(other_templates)
        # 找这个模板里最有价值的坑点/经验
        pits = source.get_active_pitfalls(min_freq=0.5)
        if not pits:
            return None

        pit = random.choice(pits)
        self.total_stimuli_injected += 1

        return (
            f"[跨界刺激] 来自 {source.template_type} 的经验:\n"
            f"  「{pit['name']}」\n"
            f"  思考: 这个教训在你的当前任务中, 有没有类似的模式需要警惕? "
            f"有没有可以从这个教训中学到的通用智慧?"
        )

    def to_prompt_extension(self, task: str, template_type: str,
                            template_db=None) -> str:
        """生成发散模式的额外 prompt"""
        config = self.get_config(task, template_type)
        if not config.active:
            return ""

        lines = ["[Divergent Mode Activated]",
                 f"  Check intensity: {config.check_intensity:.0%}",
                 f"  Bias check: OFF (allow creative deviation)",
                 "  Think freely. Cross boundaries. Challenge assumptions."]

        # Inject cross-stimulus
        stimulus = self.inject_stimulus(template_db, template_type) if template_db else None
        if stimulus:
            lines.append(f"\n{stimulus}")

        return "\n".join(lines)

    def snapshot(self) -> dict:
        return {"divergent_sessions": self.total_divergent_sessions,
                "stimuli_injected": self.total_stimuli_injected}
