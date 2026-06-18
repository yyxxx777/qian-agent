"""
乾Agent v1 - L3 自适应领域权重系统
=====================================
核心设计：领域分桶 + 四维权重向量 + 非对称迭代 + 上下限约束

四维权重：
- [0] 步数预测权重：对步骤预测的依赖程度
- [1] 坑点预测权重：对预判坑点的依赖程度
- [2] 目标偏离权重：对目标匹配的敏感程度
- [3] 置信度权重：对自身预测的信任程度

非对称迭代：失败惩罚(0.10) > 成功奖励(0.05)，宁可保守不过拟合

姚忻 · 2026.06.17
"""

import json
from pathlib import Path
from typing import Dict, List


class AdaptiveWeightSystem:
    """
    自适应领域权重系统
    ------------------
    - 按 task_type:domain 独立维护权重
    - 冷启动使用基线权重
    - 非对称迭代：失败惩罚大于成功奖励
    - 上下限约束 + 归一化，防止极端值
    """

    SUCCESS_BONUS = 0.05
    FAIL_PENALTY = 0.10
    WEIGHT_MIN = 0.05
    WEIGHT_MAX = 0.80

    # 冷启动基线权重 [步数, 坑点, 目标偏离, 置信度]
    BASELINE_WEIGHTS = {
        "code":     [0.40, 0.40, 0.10, 0.10],
        "design":   [0.20, 0.30, 0.30, 0.20],
        "analysis": [0.10, 0.20, 0.40, 0.30],
        "write":    [0.10, 0.10, 0.30, 0.50],
        "data":     [0.30, 0.30, 0.20, 0.20],
    }

    def __init__(self, weights_path: str = None):
        if weights_path is None:
            weights_path = str(Path(__file__).parent.parent.parent / "data" / "weights.json")
        self.weights_path = Path(weights_path)
        self.weights_path.parent.mkdir(parents=True, exist_ok=True)
        self.weights: Dict[str, List[float]] = self._load()
        self.iteration_count: Dict[str, int] = {}

    def _load(self) -> Dict[str, List[float]]:
        if self.weights_path.exists():
            try:
                with open(self.weights_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save(self):
        self.weights_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.weights_path, "w", encoding="utf-8") as f:
            json.dump(self.weights, f, ensure_ascii=False, indent=2)

    def get_weights(self, task_type: str, domain: str) -> List[float]:
        """获取指定领域的权重，无则返回基线"""
        key = f"{task_type}:{domain}"
        if key not in self.weights:
            baseline = self.BASELINE_WEIGHTS.get(task_type, [0.25, 0.25, 0.25, 0.25]).copy()
            self.weights[key] = baseline
            self.iteration_count[key] = 0
            self._save()
        return self.weights[key]

    def update_weights(
        self,
        task_type: str,
        domain: str,
        success: bool,
        step_error: float,
        pitfall_error: float,
        target_error: float,
        confidence_error: float,
    ) -> List[float]:
        """
        任务结束后迭代权重
        -------------------
        非对称逻辑：
        - 成功时：预测准的维度 +0.05
        - 失败时：预测错的维度 -0.10
        - 无论如何，最终归一化
        """
        key = f"{task_type}:{domain}"
        w = self.get_weights(task_type, domain).copy()
        errors = [step_error, pitfall_error, target_error, confidence_error]

        for i in range(4):
            if success:
                if errors[i] < 0.1:   # 预测准，提权
                    w[i] += self.SUCCESS_BONUS
            else:
                if errors[i] > 0.3:   # 预测错，降权
                    w[i] -= self.FAIL_PENALTY

            # 上下限约束
            w[i] = max(self.WEIGHT_MIN, min(self.WEIGHT_MAX, w[i]))

        # 归一化
        total = sum(w)
        if total > 0:
            w = [round(x / total, 4) for x in w]

        self.weights[key] = w
        self.iteration_count[key] = self.iteration_count.get(key, 0) + 1
        self._save()
        return w

    def get_experience_level(self, task_type: str, domain: str) -> Dict:
        """评估当前领域经验水平"""
        weights = self.get_weights(task_type, domain)
        iterations = self.iteration_count.get(f"{task_type}:{domain}", 0)

        max_weight = max(weights)
        if iterations == 0:
            level = "cold_start"
        elif iterations < 3:
            level = "warming_up"
        elif max_weight > 0.5:
            level = "expert"
        elif max_weight > 0.3:
            level = "familiar"
        else:
            level = "learning"

        return {
            "level": level,
            "iterations": iterations,
            "max_weight": max_weight,
            "weights": weights,
        }
