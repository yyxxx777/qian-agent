"""
Adversarial Perspective Engine — 乾 V2.5 对立视角深度审查
=============================================================
不做自说自话的复查。从4个外部视角深度审视输出。

角色:
  skeptic    — 最苛刻的批评者, 找最大漏洞
  outsider   — 完全不懂的门外汉, 找"像在编"的地方
  futurist   — 十年后的回头看, 找会被推翻的前提
  competitor — 竞争对手, 找可以利用的弱点

触发条件(分级):
  - 高风险任务: 全部4视角
  - 模板冷启动: skeptic + outsider
  - 连续3次无校验: 保底触发1次 outsider

姚忻 · 2026.06.17
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable


PERSPECTIVES = [
    ("skeptic", "You are the harshest critic. Find the BIGGEST logical flaw, missing premise, "
     "or unsupported claim. Be ruthless. Output: {{flaw: ..., severity: 1-10, fix: ...}}"),
    ("outsider", "You know NOTHING about this field. Read the output as a complete outsider. "
     "Where do you feel confused? Where does it sound like made-up jargon? Output: {{confusion: ..., jargon_suspect: ...}}"),
    ("futurist", "You are looking back from 10 years in the future. What assumption in this "
     "output will be proven wrong by then? What was overlooked? Output: {{outdated_assumption: ..., overlooked: ...}}"),
    ("competitor", "You are a competitor who wants to exploit weaknesses in this analysis. "
     "What would you attack? Where is the blind spot? Output: {{attack_vector: ..., blind_spot: ...}}"),
]


@dataclass
class AdversarialResult:
    perspective: str
    critique: str
    severity: int = 5        # 1-10, how serious
    actionable: bool = True  # can this be fixed?


class AdversarialEngine:
    """对立视角深度审查引擎"""

    def __init__(self, llm_call: Callable = None):
        self.llm = llm_call
        self.check_count = 0
        self.consecutive_clean = 0
        self.history: List[Dict] = []

    def should_trigger(self, task_risk: int, confidence: float,
                       consecutive_no_check: int) -> tuple:
        """判断是否触发对立视角 + 触发几个视角"""
        if task_risk >= 70:
            return (True, 4)  # 高风险: 4视角全开
        if confidence < 0.3:
            return (True, 2)  # 冷启动: skeptic + outsider
        if consecutive_no_check >= 3:
            return (True, 1)  # 保底: outsider
        return (False, 0)

    def deep_check(self, output: str, task: str,
                         num_perspectives: int = 2) -> List[AdversarialResult]:
        """执行对立视角审查"""
        if not self.llm or num_perspectives <= 0:
            return []

        results = []
        for role, prompt_template in PERSPECTIVES[:num_perspectives]:
            prompt = f"Role: {role}\n{prompt_template}\n\n--- Original Task ---\n{task}\n\n--- Output to Criticize ---\n{output[:2000]}\n\nYour critique (be honest, be harsh):"
            try:
                critique = self.llm(prompt, max_tokens=300, temperature=0.4)
                severity = self._estimate_severity(critique)
                results.append(AdversarialResult(
                    perspective=role, critique=critique,
                    severity=severity, actionable=True))
            except Exception:
                results.append(AdversarialResult(
                    perspective=role, critique="[check failed]",
                    severity=1, actionable=False))

        self.check_count += 1
        if not results or all(r.severity <= 2 for r in results):
            self.consecutive_clean += 1
        else:
            self.consecutive_clean = 0

        self.history.append({
            "task": task[:60], "perspectives": len(results),
            "max_severity": max((r.severity for r in results), default=0),
        })
        if len(self.history) > 20:
            self.history.pop(0)

        return results

    def synthesize(self, results: List[AdversarialResult]) -> str:
        """汇总对立视角, 生成修正建议"""
        if not results:
            return ""
        serious = [r for r in results if r.severity >= 5]
        lines = ["[Adversarial Deep Check]"]
        for r in results:
            icon = "!!" if r.severity >= 7 else ("!" if r.severity >= 5 else "-")
            lines.append(f"  {icon} [{r.perspective}] {r.critique[:120]}")
        if serious:
            lines.append(f"  ACTION: {len(serious)} high-severity issues found. Consider re-generating.")
        return "\n".join(lines)

    def _estimate_severity(self, critique: str) -> int:
        c = critique.lower()
        if any(w in c for w in ["fatal", "completely wrong", "fundamentally flawed", "关键错误"]):
            return 9
        if any(w in c for w in ["significant", "major", "严重", "明显错误"]):
            return 6
        if any(w in c for w in ["minor", "could improve", "建议", "可以"]):
            return 3
        return 2

    def snapshot(self) -> dict:
        return {"total_checks": self.check_count,
                "consecutive_clean": self.consecutive_clean}
