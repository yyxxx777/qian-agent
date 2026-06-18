"""
乾Agent v1 - L1+L2 动态误差校验引擎
=====================================
核心设计：三指标偏差计算 + 动态触发规则 + 零经验探索模式

三层校验体系：
- 执行层（L1）：按预测路径快跑，只在坑点前停一下
- 监控层（L2）：单步语义偏差 + 步数进度偏差 → 触发中层校验
- 上帝层（L3）：目标偏离超标 + 连续修正失败 → 触发全局复盘

姚忻 · 2026.06.17
"""

import re
from typing import Dict, List, Tuple


class DynamicCheckEngine:
    """
    动态误差校验引擎
    -----------------
    不固定校验频次，只在预测失效时才干预：
    - 熟悉任务：几乎不触发，全速跑
    - 陌生任务：高密度校验，步步确认
    """

    # 触发阈值（全部按讨论结论设定）
    STEP_DEVIATION_THRESHOLD = 0.3       # 单步语义偏差触发中层
    STEP_RATE_THRESHOLD_MID = 0.2        # 步数偏差触发中层
    STEP_RATE_THRESHOLD_GOD = 0.5        # 步数偏差触发上帝
    TARGET_DEVIATION_THRESHOLD = 0.4     # 目标偏离触发上帝
    CONSECUTIVE_FAIL_THRESHOLD = 2        # 连续修正失败触发上帝

    def __init__(
        self,
        target_task: str,
        expected_steps: int,
        key_nodes: List[str],
        pitfalls: List[Dict],
    ):
        self.target_keywords = self._extract_keywords(target_task)
        self.expected_steps = max(expected_steps, 1)
        self.key_nodes = key_nodes if key_nodes else []
        self.pitfalls = pitfalls if pitfalls else []

        # 坑点位置索引
        self.pitfall_positions = []
        for i, node in enumerate(key_nodes):
            for p in pitfalls:
                if p.get("name", "") in node:
                    self.pitfall_positions.append(i)
                    break

        self.current_step = 0
        self.consecutive_deviation_count = 0
        self.mid_check_count = 0
        self.god_check_count = 0
        self.total_deviations = 0
        self.total_corrections = 0

    def _extract_keywords(self, text: str) -> List[str]:
        words = re.findall(r"[\u4e00-\u9fa5a-zA-Z0-9]+", text.lower())
        return [w for w in words if len(w) > 1]

    def _calc_semantic_similarity(self, text1: str, text2: str) -> float:
        """关键词重合度计算语义相似度"""
        set1 = set(self._extract_keywords(text1))
        set2 = set(self._extract_keywords(text2))
        if not set1 or not set2:
            return 0.0
        return len(set1 & set2) / len(set2)

    def step(self, step_content: str) -> Dict:
        """
        执行一步，返回校验结果
        -----------------------
        返回 dict:
        - trigger_mid: 是否触发中层校验
        - trigger_god: 是否触发上帝视角复盘
        - reason: 触发原因
        - severity: 严重程度 (info/warning/critical)
        """
        self.current_step += 1
        result = {
            "trigger_mid": False,
            "trigger_god": False,
            "reason": "",
            "severity": "info",
            "step": self.current_step,
        }

        # 0. 首步保护：第一步不触发校验
        if self.current_step == 1:
            return result

        # 1. 坑点前一步强制校验（最高优先级）
        if self.current_step + 1 in self.pitfall_positions:
            result["trigger_mid"] = True
            result["reason"] = "即将进入预判坑点，前置校验"
            result["severity"] = "warning"
            return result

        # 2. 单步语义偏差（与对应关键节点的偏差）
        if self.key_nodes:
            node_idx = min(self.current_step - 1, len(self.key_nodes) - 1)
            expected_node = self.key_nodes[node_idx] if node_idx < len(self.key_nodes) else ""
            if expected_node:
                step_deviation = 1 - self._calc_semantic_similarity(
                    step_content, expected_node
                )
                if step_deviation > self.STEP_DEVIATION_THRESHOLD:
                    self.consecutive_deviation_count += 1
                    self.total_deviations += 1
                    # 防抖：连续2步超标才触发
                    if self.consecutive_deviation_count >= 2:
                        result["trigger_mid"] = True
                        result["reason"] = (
                            f"连续2步语义偏差超标（当前{step_deviation:.1%}）"
                        )
                        result["severity"] = "warning"
                        self.consecutive_deviation_count = 0
                        self.total_corrections += 1
                        return result
                else:
                    self.consecutive_deviation_count = 0

        # 3. 步数进度偏差
        if self.expected_steps > 0:
            expected_progress = self.current_step / self.expected_steps
            actual_progress = self.current_step / max(self.expected_steps, self.current_step)
            step_rate_deviation = abs(expected_progress - actual_progress)

            if step_rate_deviation > self.STEP_RATE_THRESHOLD_GOD:
                result["trigger_god"] = True
                result["reason"] = f"步数进度严重失控（偏差{step_rate_deviation:.1%}）"
                result["severity"] = "critical"
                self.god_check_count += 1
                self.total_corrections += 1
                return result

            if step_rate_deviation > self.STEP_RATE_THRESHOLD_MID:
                result["trigger_mid"] = True
                result["reason"] = f"步数进度偏差超标（{step_rate_deviation:.1%}）"
                result["severity"] = "warning"
                self.total_corrections += 1

        # 4. 目标偏离度（核心目标是否还在主线上）
        target_deviation = 1 - self._calc_semantic_similarity(
            step_content, " ".join(self.target_keywords)
        )
        if target_deviation > self.TARGET_DEVIATION_THRESHOLD:
            result["trigger_god"] = True
            result["reason"] = f"核心目标偏离超标（{target_deviation:.1%}），触发上帝视角"
            result["severity"] = "critical"
            self.god_check_count += 1
            self.total_corrections += 1

        return result

    def mid_check_failed(self) -> bool:
        """
        中层校验修正失败计数
        连续失败达到阈值 → 升级为上帝视角
        """
        self.mid_check_count += 1
        if self.mid_check_count >= self.CONSECUTIVE_FAIL_THRESHOLD:
            self.mid_check_count = 0
            return True
        return False

    def get_stats(self) -> Dict:
        """获取校验统计"""
        return {
            "total_steps": self.current_step,
            "total_deviations": self.total_deviations,
            "total_corrections": self.total_corrections,
            "mid_checks": self.mid_check_count,
            "god_checks": self.god_check_count,
            "correction_rate": (
                self.total_corrections / self.current_step
                if self.current_step > 0 else 0.0
            ),
            "is_stable": (
                self.total_corrections / self.current_step < 0.3
                if self.current_step > 0 else True
            ),
        }
