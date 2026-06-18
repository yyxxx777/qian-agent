"""
CognitiveOrchestrator — 乾 V2 认知调度器
==========================================
有机融合: BrainNetwork(老) + cognitive_scheduler(新 V2.0)

三脑网络提供语义标签(DMN/CEN/SN),
cognitive_scheduler提供数值驱动(困惑感+压力值),
融合 = 阈值决定 + 语义标签 → 可解释的快慢引擎切换

姚忻 · 2026.06.17
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional
import time


class BrainNetwork(Enum):
    DMN = "默认模式网络"    # 反思、自传体记忆、远距离联想 → 慢引擎
    CEN = "中央执行网络"    # 专注执行、工具调用 → 快引擎
    SN = "显著性网络"       # 注意力切换、异常检测 → 切换触发器


class EngineMode(Enum):
    FAST = "fast"           # 零元认知, 直觉驱动
    SLOW = "slow"           # 全内省: 监控+上帝+偏误
    EMERGENCY = "emergency" # 停止任务, 降维诊断


@dataclass
class OrchestratorState:
    """可串行化的调度器状态"""
    friction: float = 0.0          # 困惑感 0-100
    pressure: float = 0.0          # 认知压力 0-100
    engine: str = "fast"           # 当前引擎
    active_network: str = "CEN"    # 活跃脑网络
    network_switch_count: int = 0  # 脑网络切换次数
    last_switch: float = 0.0

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class CognitiveOrchestrator:
    """
    认知调度核心 — 困惑感+压力→快慢引擎 + 脑网络语义标签

    使用:
        orch = CognitiveOrchestrator()
        mode = orch.evaluate(friction=45, pressure=30)
        # → (EngineMode.FAST, BrainNetwork.CEN, "执行模式")
    """

    # 阈值(来自 config, 可调)
    FAST_CEILING: float = 60       # pressure < this AND friction < this → fast
    SLOW_TRIGGER: float = 70       # friction > this OR pressure > this → slow
    EMERGENCY_TRIGGER: float = 85  # pressure > this → emergency

    def __init__(self):
        self.state = OrchestratorState()
        self._network_history = []  # last 10 network switches
        self._init_time = time.time()

    def evaluate(self, friction: float, pressure: float,
                 template_hit: bool = False,
                 is_creative_task: bool = False) -> dict:
        """核心评估: 输入困惑感+压力 → 输出引擎+网络+行为建议"""

        self.state.friction = friction
        self.state.pressure = pressure

        # ── 引擎选择 ──
        if pressure >= self.EMERGENCY_TRIGGER:
            engine = EngineMode.EMERGENCY
        elif friction >= self.SLOW_TRIGGER or pressure >= self.SLOW_TRIGGER:
            engine = EngineMode.SLOW
        else:
            engine = EngineMode.FAST

        # ── 脑网络映射 ──
        if engine == EngineMode.SLOW:
            network = BrainNetwork.DMN  # 慢 → 默认模式网络(反思)
        elif friction > 50 or not template_hit:
            network = BrainNetwork.SN   # 异常/无经验 → 显著性网络(警觉)
        else:
            network = BrainNetwork.CEN  # 快 → 中央执行网络(执行)

        # 创意任务偏置
        if is_creative_task and engine != EngineMode.EMERGENCY:
            network = BrainNetwork.DMN  # 创意需要 DMN 的发散联想

        # 切换追踪
        prev = self.state.active_network
        if network.value != prev:
            self.state.network_switch_count += 1
            self.state.last_switch = time.time()
            self._network_history.append((prev, network.value, round(friction)))
            if len(self._network_history) > 10:
                self._network_history.pop(0)

        self.state.active_network = network.value
        self.state.engine = engine.value

        return {
            "engine": engine.value,
            "network": network.value,
            "network_cn": _NETWORK_CN.get(network, network.value),
            "is_fast": engine == EngineMode.FAST,
            "should_reflect": engine != EngineMode.FAST,
            "detail": self._describe(engine, network, friction, pressure),
        }

    def _describe(self, engine, network, friction, pressure):
        if engine == EngineMode.FAST:
            return "快引擎 · 零元认知 · 直接执行"
        if engine == EngineMode.SLOW:
            return f"慢引擎 · {network.value}激活 · 全面内省(f={friction:.0f}, p={pressure:.0f})"
        return f"应急模式 · 压力={pressure:.0f} · 降维诊断"

    def get_switching_pattern(self) -> str:
        """分析脑网络切换模式"""
        if len(self._network_history) < 3:
            return "稳定"
        switches = self.state.network_switch_count
        runtime_hours = (time.time() - self._init_time) / 3600
        rate = switches / max(runtime_hours, 0.1)
        if rate > 10: return "频繁切换(可能任务类型多变)"
        if rate > 3: return "正常切换"
        return "极少切换(可能过度专注单一领域)"

    def snapshot(self) -> dict:
        return {
            "engine": self.state.engine,
            "network": self.state.active_network,
            "switches": self.state.network_switch_count,
            "pattern": self.get_switching_pattern(),
        }


_NETWORK_CN = {
    BrainNetwork.DMN: "默认模式(反思)",
    BrainNetwork.CEN: "中央执行(专注)",
    BrainNetwork.SN: "显著性(警觉)",
}
