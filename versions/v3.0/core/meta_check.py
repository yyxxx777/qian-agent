"""
V2 元自检层 — 检查乾自身架构偏误，不只检查 LLM 输出
====================================================
两条核心检查：
1. EWMA 过拟合：连续 N 次无修正 → 降低 alpha 增加敏感性
2. 坑点自证：freq > 0.9 但从未被实际触发 → 可能假阳性

姚忻 · 2026.06.17
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class MetaAlert:
    name: str
    severity: str      # "info" | "warning" | "critical"
    detail: str
    suggested_action: str
    timestamp: float = field(default_factory=time.time)


class MetaCheckEngine:
    """乾自检 — 检查自身的认知偏误"""

    EWMA_OVERFIT_THRESHOLD = 10     # 连续 N 次无修正 → 可能过拟合
    PITFALL_SELF_FULFILL = 0.90     # freq > this but never triggered → 假阳性
    PITFALL_MIN_HITS = 3            # 至少触发过 N 次才不怀疑

    def __init__(self):
        self.alerts: List[MetaAlert] = []
        self.consecutive_no_correction = 0
        self.last_check_time = time.time()

    def check_ewma(self, predicted: int, actual: int, mid_checks: int, god_checks: int) -> Optional[MetaAlert]:
        """检查 EWMA 是否过拟合"""
        error = abs(predicted - actual)
        has_correction = mid_checks > 0 or god_checks > 0

        if error <= 1 and not has_correction:
            self.consecutive_no_correction += 1
        else:
            self.consecutive_no_correction = 0

        if self.consecutive_no_correction >= self.EWMA_OVERFIT_THRESHOLD:
            alert = MetaAlert(
                name="EWMA过拟合",
                severity="warning",
                detail=f"连续 {self.consecutive_no_correction} 次预测准确且无校验触发 — "
                       f"EWMA 可能过拟合到当前任务模式。降低 alpha 可恢复敏感性。",
                suggested_action="建议临时提高 template_match_threshold → 更多冷启动 → 重新积累多样性",
            )
            self.alerts.append(alert)
            self.consecutive_no_correction = 0
            return alert
        return None

    def check_pitfall_self_fulfilling(self, pitfalls: List[dict],
                                       triggered_names: List[str]) -> Optional[MetaAlert]:
        """检查坑点是否假阳性（freq 高但从未实际触发）"""
        for p in pitfalls:
            freq = p.get("freq", 0)
            hits = p.get("hit_count", 0)
            name = p.get("name", "unknown")

            if freq > self.PITFALL_SELF_FULFILL and hits < self.PITFALL_MIN_HITS:
                alert = MetaAlert(
                    name="坑点假阳性",
                    severity="warning",
                    detail=f"坑点 '{name}' freq={freq:.2f} 但只触发过 {hits} 次 — "
                           f"可能是自证预言（提示了坑点 → 用户刻意避开 → 坑点看起来有用）",
                    suggested_action=f"降低 '{name}' 置信度或将其移到观察区",
                )
                self.alerts.append(alert)
                return alert
        return None

    def get_summary(self) -> dict:
        return {
            "total_alerts": len(self.alerts),
            "recent": [{"name": a.name, "severity": a.severity,
                        "detail": a.detail[:80]} for a in self.alerts[-5:]],
        }
