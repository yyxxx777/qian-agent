"""
乾Agent V2 - 闭环预测大脑 · 统一入口
========================================
predict → execute → learn 完整闭环 + 人格引擎 + 认知调度

核心能力：
- predict: 两级指纹(模板+实例)匹配 + 人格情绪 + 认知调度
- execute: 动态误差校验 + 对立视角深度审查
- learn: 反哺模板/指纹/权重 + 进化追踪 + 元自检 + 情绪更新

姚忻 · 2026.06.17
"""

import time
import sys
import os
from typing import Dict, List, Optional, Callable

# 路径处理
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.v1.fingerprint_db import ExperienceFingerprintDB
from core.v1.dynamic_check import DynamicCheckEngine
from core.v1.adaptive_weights import AdaptiveWeightSystem
from core.task_template import TaskTemplateDB, TaskTemplate
from core.meta_check import MetaCheckEngine
from core.personality import PersonalityEngine
from core.orchestrator import CognitiveOrchestrator, EngineMode
from shared.stats_tracker import StatsTracker


class QianAgent:
    """
    乾Agent V2 - 闭环预测大脑 + 人格引擎 + 认知调度
    """

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        
        os.makedirs(data_dir, exist_ok=True)
        self.fp_db = ExperienceFingerprintDB(
            os.path.join(data_dir, "fingerprints.json")
        )
        self.weight_system = AdaptiveWeightSystem(
            os.path.join(data_dir, "weights.json")
        )
        self.template_db = TaskTemplateDB(
            os.path.join(data_dir, "templates.json"),
            os.path.join(data_dir, "seed_templates.json"),
        )
        self.meta_check = MetaCheckEngine()
        self.tracker = StatsTracker(os.path.join(data_dir, "evolution.json"))
        self.personality = PersonalityEngine()
        self.orchestrator = CognitiveOrchestrator()
        self.task_type = "code"
        self.domain = "general"
        
        # 执行历史
        self.execution_history: List[Dict] = []
        self._predict_cache: Dict[str, Dict] = {}  # perf: session cache

    def predict(
        self, task: str, task_type: str = "code", domain: str = "general"
    ) -> Dict:
        """
        预测执行蓝图 — V2: 两级融合 (模板 + 实例指纹)
        """
        self.task_type = task_type
        self.domain = domain

        # perf: session cache
        ck = f"{task[:80]}|{task_type}|{domain}"
        if ck in self._predict_cache:
            return self._predict_cache[ck]

        # === Layer 0: Trivial tasks ===
        if len(task) < 6:  # perf: treat very short input as trivial
            bp = self._make_pred("trivial", confidence=0.95, steps=1, tokens=100,
                                   note="简单任务，直接执行", _task=task)
            self._predict_cache[ck] = bp
            return bp

        # === Layer 1: Template matching (new V2) ===
        template = None
        template_match = None
        try:
            template = self.template_db.extract(task)
            if template:
                template_match = self.template_db.match(template)
        except Exception:
            template_match = None

        # === Layer 2: Instance fingerprint (existing) ===
        match_result = None
        try:
            match_result = self.fp_db.match(task, task_type, domain)
        except Exception:
            match_result = None

        fp = match_result["fingerprint"] if match_result else None
        similarity = match_result.get("similarity", 0) if match_result else 0
        match_level = match_result.get("match_level", "none") if match_result else "none"
        experience_info = self.weight_system.get_experience_level(task_type, domain)

        # === Layer 3: Orchestrator evaluation ===
        tmpl_hit = bool(template_match)
        is_creative = domain in ("design", "creative") or task_type in ("design", "write")
        # Friction = how unfamiliar this feels; Pressure = urgency from personality
        friction = 80 if not tmpl_hit else (30 if match_level == "exact" else 55)
        pressure = self.personality.urgency * 100
        orch = self.orchestrator.evaluate(friction, pressure, tmpl_hit, is_creative)

        # === Fusion: template + instance ===
        if template_match:
            ewma = template_match.ewma_steps
            pits = template_match.get_active_pitfalls()
            steps = max(1, round(ewma)) if ewma and template_match.hit_count >= 2 else max(2, template.complexity // 2)
            tokens = steps * 120

            if match_level in ("exact", "fuzzy") and fp:
                model = fp.get("prediction_model", {})
                fp_steps = round(model.get("avg_steps", steps))
                steps = min(steps, fp_steps)
                note = "双重匹配 · 高度可信"
            else:
                note = f"模板匹配 · {template_match.hit_count}次参考"

            return self._make_pred(
                "template", confidence=min(0.7 + template_match.hit_count * 0.05, 0.95),
                match_level="template", similarity=0.5 + template_match.hit_count * 0.05,
                steps=steps, tokens=tokens,
                pitfalls=pits, use_count=template_match.hit_count,
                success_rate=template_match.success_count / max(template_match.hit_count, 1),
                experience=experience_info, note=note, template=template_match, _task=task)

        # === Instance only ===
        if match_level != "none" and fp:
            model = fp.get("prediction_model", {})
            confidence = similarity * 0.7 + fp.get("stats", {}).get("success_rate", 0.5) * 0.3
            steps = max(2, round(model.get("avg_steps", 5)))
            tokens = max(200, round(model.get("avg_tokens", steps * 80)))
            return self._make_pred(
                match_level, confidence=min(confidence, 0.95),
                match_level=match_level, similarity=round(similarity, 2),
                steps=steps, tokens=tokens,
                key_nodes=fp.get("solution_template", {}).get("key_nodes", []),
                pitfalls=fp.get("solution_template", {}).get("pitfall_list", []),
                use_count=fp.get("meta", {}).get("use_count", 0),
                success_rate=round(fp.get("stats", {}).get("success_rate", 0.5), 2),
                experience=experience_info, note="实例匹配 · 参考历史", _task=task)

        # === Cold start ===
        return self._make_pred(
            "cold", confidence=0.2, match_level="none", similarity=0.0,
            steps=6, tokens=500, experience=experience_info,
            note="新领域 · 执行后将自动学习", _task=task)

    def _make_pred(self, mode, **kw) -> Dict:
        """Build prediction dict with consistent keys + personality/orchestrator data"""
        personality = self.personality.snapshot()
        orch = self.orchestrator.snapshot()
        result = {
            "mode": mode,
            "confidence": kw.get("confidence", 0.2),
            "match_level": kw.get("match_level", "cold"),
            "similarity": kw.get("similarity", 0.0),
            "expected_steps": kw.get("steps", 6),
            "expected_tokens": kw.get("tokens", 500),
            "key_nodes": kw.get("key_nodes", []),
            "pitfall_list": kw.get("pitfalls", []),
            "verify_method": kw.get("verify_method", ""),
            "use_count": kw.get("use_count", 0),
            "success_rate": kw.get("success_rate", 0.0),
            "experience": kw.get("experience", {}),
            "note": kw.get("note", ""),
            "_template": kw.get("template"),
            "personality": personality,
            "orchestrator": orch,
        }
        # perf: auto-cache
        task = kw.get("_task", "")
        if len(task) >= 15:
            ck = f"{task[:80]}|{self.task_type}|{self.domain}"
            self._predict_cache[ck] = result
        return result

    def execute(
        self,
        task: str,
        blueprint: Dict,
        llm_call: Optional[Callable] = None,
        max_steps: int = None,
        on_step: Optional[Callable] = None,
    ) -> Dict:
        """
        执行任务（真实LLM模式）
        ----------------------
        智能步数控制：
        - exact匹配: 1-2步（直接复用经验）
        - fuzzy匹配: 2-4步（参考经验+校验）
        - loose/explore: 3-5步（先做出来再检查）
        - 每步检测完成度，提前终止
        
        on_step(event_type, data) — 实时回调:
          event_type: "exec" | "mid_check" | "god_check" | "refine" | "complete"
        """
        import re

        match_level = blueprint.get("match_level", "cold")
        confidence = blueprint.get("confidence", 0.2)
        bp_task_type = self.task_type

        # V2: Use blueprint's expected_steps directly (EWMA-driven, not dead mapping)
        expected_steps = max(2, int(blueprint.get("expected_steps", 5) or 5))

        if max_steps is None:
            max_steps = min(expected_steps + 1, 6)  # perf: tighter

        check_engine = DynamicCheckEngine(
            task,
            expected_steps,
            blueprint.get("key_nodes", []),
            blueprint.get("pitfall_list", []),
        )

        steps_executed = []
        check_logs = []
        total_tokens = 0
        start_time = time.time()

        # 第一步：直接尝试完整解答
        if llm_call:
            first_prompt = (
                "任务：{}\n\n"
                "请直接完成这个任务，输出完整答案。如果是代码，输出完整可运行代码。"
                "如果是设计方案，输出完整方案。不要分步，一次性给出最终结果。".format(task)
            )
            try:
                response = llm_call(first_prompt)
                steps_executed.append(response)
                step_tokens = len(response) // 2
                total_tokens += step_tokens
                check_engine.step(response)
                if on_step:
                    on_step("exec", {"step": 1, "tokens": step_tokens, "response": response})
            except Exception as e:
                steps_executed.append("[LLM调用失败: {}]".format(str(e)))
                if on_step:
                    on_step("exec", {"step": 1, "tokens": 0, "response": str(e), "error": True})
        else:
            steps_executed.append(self._simulate_step(task, blueprint, 0))
            total_tokens += 80
            if on_step:
                on_step("exec", {"step": 1, "tokens": 80, "response": steps_executed[0]})

        # 第二步起：校验 + 修正（最多再跑几步）
        for i in range(1, max_steps):
            last_response = steps_executed[-1]

            # 提前终止检测：答案已完整
            if self._is_answer_complete(last_response, bp_task_type):
                if on_step:
                    on_step("complete", {"step": i + 1, "reason": "答案完整"})
                break

            check_result = check_engine.step(last_response)

            # V2: Refine skip - don't call LLM if already complete
            if not check_result["trigger_mid"] and not check_result["trigger_god"]:
                if self._is_answer_complete(last_response, bp_task_type) and i >= expected_steps - 1:
                    if on_step:
                        on_step("complete", {"step": i + 1, "reason": "答案完整"})
                    break
                if i >= expected_steps + 1:
                    break
                # Only refine if explicitly needed (not silent skip)
                if i < max_steps - 1 and llm_call and not self._is_answer_complete(last_response, bp_task_type):
                    refine_prompt = (
                        "任务：{}\n当前输出：\n{}\n\n"
                        "请检查并完善以上输出。如有遗漏或错误，请修正。"
                        "如果已经完整，回复 DONE。".format(task, last_response[:600])
                    )
                    try:
                        refined = llm_call(refine_prompt)
                        step_tokens = len(refined) // 2
                        if "DONE" in refined[:20] or len(refined) < 20:
                            break
                        steps_executed.append(refined)
                        total_tokens += step_tokens
                        if on_step:
                            on_step("refine", {"step": i + 1, "tokens": step_tokens, "response": refined})
                    except Exception:
                        break
                else:
                    break
                continue

            # 触发了校验
            if check_result["trigger_mid"]:
                log_entry = {
                    "step": i + 1, "level": "mid",
                    "reason": check_result["reason"],
                    "severity": check_result.get("severity", "warning"),
                }
                check_logs.append(log_entry)
                if on_step:
                    on_step("mid_check", log_entry)
                if llm_call:
                    fix_prompt = (
                        "任务：{}\n当前输出：\n{}\n\n"
                        "【中层校验】触发原因：{}\n"
                        "请修正输出，确保符合任务要求。直接给出修正后的完整内容。".format(
                            task, last_response[:600], check_result["reason"]
                        )
                    )
                    try:
                        fixed = llm_call(fix_prompt)
                        steps_executed.append(fixed)
                        step_tokens = len(fixed) // 2
                        total_tokens += step_tokens
                        if on_step:
                            on_step("exec", {"step": i + 2, "tokens": step_tokens, "response": fixed, "mode": "fix"})
                    except Exception:
                        pass

            if check_result["trigger_god"]:
                log_entry = {
                    "step": i + 1, "level": "god",
                    "reason": check_result["reason"],
                    "severity": check_result.get("severity", "critical"),
                }
                check_logs.append(log_entry)
                if on_step:
                    on_step("god_check", log_entry)
                if llm_call:
                    god_prompt = (
                        "原始任务：{}\n\n已完成步骤摘要：\n{}\n\n"
                        "【上帝复盘】触发原因：{}\n"
                        "请从全局角度重新审视，给出修正后的完整方案。".format(
                            task,
                            "\n".join(s[-200:] for s in steps_executed[-3:]),
                            check_result["reason"]
                        )
                    )
                    try:
                        god_review = llm_call(god_prompt)
                        steps_executed.append(god_review)
                        step_tokens = len(god_review) // 2
                        total_tokens += step_tokens
                        if on_step:
                            on_step("exec", {"step": i + 2, "tokens": step_tokens, "response": god_review, "mode": "god_review"})
                    except Exception:
                        pass

        elapsed = time.time() - start_time
        stats = check_engine.get_stats()

        result = {
            "success": stats["is_stable"],
            "actual_steps": stats["total_steps"],
            "actual_tokens": total_tokens,
            "elapsed_seconds": round(elapsed, 1),
            "steps": steps_executed,
            "check_logs": check_logs,
            "step_error": (
                abs(stats["total_steps"] - expected_steps) / max(expected_steps, 1)
            ),
            "pitfall_error": (
                stats["total_corrections"] / max(stats["total_steps"], 1)
            ),
            "target_error": (
                1 - (stats["total_steps"] - stats["total_corrections"]) / max(stats["total_steps"], 1)
                if stats["total_steps"] > 0 else 0
            ),
            "confidence_error": abs(0.8 - confidence),
            "deviation_count": stats["total_deviations"],
            "correction_count": stats["total_corrections"],
            "mid_checks": stats["mid_checks"],
            "god_checks": stats["god_checks"],
        }

        self.execution_history.append({
            "task": task[:80],
            "task_type": self.task_type,
            "result": result,
            "blueprint": blueprint,
        })

        return result

    def _is_answer_complete(self, response: str, task_type: str) -> bool:
        """检测答案是否已经完整"""
        if not response or len(response) < 50:
            return False
        # 代码类：有完整的代码块和必要元素
        if task_type in ("code", "data"):
            has_code_block = "```" in response or "def " in response or "import " in response
            has_output = len(response) > 200
            return has_code_block and has_output
        # 设计类：有结构化的方案
        if task_type == "design":
            has_structure = "##" in response or "|" in response or "**" in response
            has_content = len(response) > 300
            return has_structure and has_content
        # 分析类：有明确的问题和修复
        if task_type == "analysis":
            has_issues = "问题" in response or "建议" in response
            return has_issues and len(response) > 100
        # 写作类：有标题和足够内容
        if task_type == "write":
            has_title = "# " in response or "**" in response
            return has_title and len(response) > 200
        return len(response) > 300

    def learn(self, task: str, result: Dict, blueprint: Dict):
        """V2: 同时更新实例指纹 + 模板 + 权重 + 进化追踪 + 元自检"""
        actual_steps = result.get("actual_steps", 1)
        actual_tokens = result.get("actual_tokens", 500)
        mid = result.get("mid_checks", 0)
        god = result.get("god_checks", 0)
        corrections = result.get("correction_count", 0)
        predicted = blueprint.get("expected_steps", 5)
        match_level = blueprint.get("match_level", "cold")

        # 1. Instance fingerprint
        fp = self.fp_db.generate_fingerprint(task, self.task_type, self.domain)
        self.fp_db.add_or_update(
            fp, result.get("success", True),
            actual_steps, actual_tokens,
            blueprint.get("key_nodes", [task]),
            blueprint.get("pitfall_list", []),
            blueprint.get("verify_method", ""),
        )

        # 2. Template tracking
        tmpl = blueprint.get("_template")
        if tmpl is None and len(task) >= 15:
            tmpl = self.template_db.get_or_create(task)
        template_type = tmpl.template_type if tmpl else self.task_type

        if tmpl:
            tmpl.track(actual_steps)
            triggered = [l["reason"] for l in result.get("check_logs", []) if l.get("reason")]
            for pit_name in triggered:
                tmpl.add_pitfall(pit_name)
            self.template_db._save()

        # 3. Weights
        new_weights = self.weight_system.update_weights(
            self.task_type, self.domain,
            result.get("success", True),
            result.get("step_error", 0.1),
            result.get("pitfall_error", 0.1),
            result.get("target_error", 0.05),
            result.get("confidence_error", 0.2),
        )

        # 4. Evolution tracking (V2 new)
        elapsed_ms = int(result.get("elapsed_seconds", 0) * 1000)
        self.tracker.record(task, template_type, predicted, actual_steps,
                           elapsed_ms, actual_tokens, mid, god, corrections)

        # 5. Meta self-check (V2 new)
        active_pits = tmpl.get_active_pitfalls() if tmpl else []
        self.meta_check.check_ewma(predicted, actual_steps, mid, god)
        self.meta_check.check_pitfall_self_fulfilling(
            active_pits,
            [l["reason"] for l in result.get("check_logs", []) if l.get("reason")]
        )

        # 6. Personality update (V2.1: emotion from execution outcomes)
        success = result.get("success", True)
        self.personality.decay()
        if match_level == "cold":
            self.personality.apply_event("cold_start")
        elif match_level == "template":
            self.personality.apply_event("template_match")
        if success:
            self.personality.apply_event("task_success")
            if abs(predicted - actual_steps) <= 1:
                self.personality.apply_event("prediction_correct")
            else:
                self.personality.apply_event("prediction_wrong")
        else:
            self.personality.apply_event("task_fail")
        if corrections > 0:
            self.personality.apply_event("pitfall_hit", magnitude=min(corrections / 3, 1.0))
        if mid == 0 and god == 0 and corrections == 0 and match_level != "cold":
            self.personality.apply_event("pitfall_avoided")

        return {
            "fingerprint_updated": True, "new_weights": new_weights,
            "fp_stats": self.fp_db.get_stats(),
            "template_stats": self.template_db.get_stats(),
            "evolution": self.tracker.get_summary(),
            "meta_alerts": self.meta_check.get_summary(),
            "personality": self.personality.snapshot(),
            "orchestrator": self.orchestrator.snapshot(),
        }

    def _build_step_prompt(
        self, task: str, context: str, step_num: int, blueprint: Dict
    ) -> str:
        """构建执行步骤的prompt"""
        parts = [
            f"任务：{task}",
            f"当前是第{step_num + 1}步执行",
        ]
        if context:
            parts.append(f"前面已完成：\n{context[:500]}")
        
        key_nodes = blueprint.get("key_nodes", [])
        if step_num < len(key_nodes):
            parts.append(f"当前关键节点：{key_nodes[step_num]}")

        pitfalls = blueprint.get("pitfall_list", [])
        if pitfalls:
            parts.append(f"注意避坑：{', '.join(p.get('name', '') for p in pitfalls[:3])}")

        parts.append("\n请继续执行下一步，直接给出代码或方案，不需要额外解释。")
        return "\n".join(parts)

    def _build_reflect_prompt(self, task: str, last_step: str, warning: str) -> str:
        """构建中层反思prompt"""
        return f"""原始任务：{task}
最后一步输出：{last_step[:300]}
触发预警：{warning}

【中层校验指令】请检查：
1. 上一步是否偏离了核心目标？
2. 如果有偏离，请修正方向，重新输出上一步的正确内容
3. 直接给出修正结果，不需要解释"""

    def _build_god_review_prompt(
        self, task: str, all_steps: List[str], reason: str
    ) -> str:
        """构建上帝视角复盘prompt"""
        summary = "\n".join(
            f"步骤{i+1}: {s[:100]}..." for i, s in enumerate(all_steps[-5:])
        )
        return f"""原始任务：{task}
触发上帝视角复盘原因：{reason}

已完成步骤摘要：
{summary}

【上帝视角复盘指令】请从全局角度评估：
1. 当前路线是否还在正确方向上？如果不是，正确的方向是什么？
2. 有没有更好的方案被忽略了？
3. 剩余任务预估还需要几步？

直接给出结论和修正路线，不需要详细解释。"""

    def _simulate_step(self, task: str, blueprint: Dict, i: int) -> str:
        """模拟执行步骤（无LLM时使用）"""
        key_nodes = blueprint.get("key_nodes", [])
        if i < len(key_nodes):
            return f"执行步骤{i+1}：{key_nodes[i]}"
        return f"执行步骤{i+1}：持续推进 {task[:30]}..."

    def get_status(self) -> Dict:
        """获取Agent当前状态"""
        return {
            "fingerprints": self.fp_db.get_stats(),
            "experience": self.weight_system.get_experience_level(
                self.task_type, self.domain
            ),
            "execution_count": len(self.execution_history),
            "mode": "v1 闭环预测大脑",
        }
