"""
乾Agent V1 - 经验指纹闭环 · 初代大脑
======================================
predict → execute → learn 闭环
只依赖实例指纹库(LSH精确匹配)，无模板系统

特点: 冷启动, 硬编码步数预测, 无跨任务迁移

姚忻 · 2026.06.17
"""

import time, sys, os
from typing import Dict, List, Optional, Callable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.v1.fingerprint_db import ExperienceFingerprintDB
from core.v1.dynamic_check import DynamicCheckEngine
from core.v1.adaptive_weights import AdaptiveWeightSystem


class QianAgentV1:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(data_dir, exist_ok=True)
        self.fp_db = ExperienceFingerprintDB(os.path.join(data_dir, "fingerprints.json"))
        self.weight_system = AdaptiveWeightSystem(os.path.join(data_dir, "weights.json"))
        self.task_type = "code"
        self.domain = "general"
        self.execution_history: List[Dict] = []
        self._predict_cache: Dict[str, Dict] = {}  # perf: session cache

    def predict(self, task: str, task_type: str = "code", domain: str = "general") -> Dict:
        self.task_type = task_type; self.domain = domain
        # perf: session cache
        ck = f"{task[:80]}|{task_type}|{domain}"
        if ck in self._predict_cache:
            return self._predict_cache[ck]
        match_result = self.fp_db.match(task, task_type, domain)
        fp = match_result.get("fingerprint")
        similarity = match_result.get("similarity", 0)
        match_level = match_result.get("match_level", "none")
        experience_info = self.weight_system.get_experience_level(task_type, domain)

        if match_level == "none":
            result = {
                "mode": "explore", "confidence": 0.2, "match_level": "none",
                "similarity": 0.0, "expected_steps": 8, "expected_tokens": 600,
                "key_nodes": [], "pitfall_list": [], "verify_method": "",
                "use_count": 0, "success_rate": 0.0, "experience": experience_info,
                "note": "cold start · exploring",
            }
            self._predict_cache[ck] = result
            return result

        model = fp["prediction_model"]
        confidence = similarity * 0.7 + fp["stats"]["success_rate"] * 0.3
        steps = max(2, round(model["avg_steps"]))
        tokens = max(200, round(model["avg_tokens"])) if model["avg_tokens"] > 0 else steps * 80

        result = {
            "mode": match_level, "confidence": min(confidence, 0.95),
            "match_level": match_level, "similarity": round(similarity, 2),
            "expected_steps": steps, "expected_tokens": tokens,
            "key_nodes": fp["solution_template"]["key_nodes"],
            "pitfall_list": fp["solution_template"]["pitfall_list"],
            "verify_method": fp["solution_template"].get("verify_method", ""),
            "use_count": fp["meta"]["use_count"],
            "success_rate": round(fp["stats"]["success_rate"], 2),
            "experience": experience_info,
            "note": "exact match" if match_level == "exact" else "fuzzy match · verify more",
        }
        self._predict_cache[ck] = result
        return result

    def execute(self, task: str, blueprint: Dict, llm_call=None, max_steps=None, on_step=None) -> Dict:
        match_level = blueprint.get("match_level", "none")
        confidence = blueprint.get("confidence", 0.2)
        # perf: tighter max_steps for high-confidence matches
        base = {"exact": 2, "fuzzy": 3, "loose": 4}.get(match_level, 5)
        if confidence > 0.8: base = max(1, base - 1)
        expected_steps = base
        if max_steps is None: max_steps = min(base + 1, 6)  # perf: was +2/8

        check_engine = DynamicCheckEngine(task, expected_steps,
            blueprint.get("key_nodes", []), blueprint.get("pitfall_list", []))

        steps_executed, check_logs, total_tokens = [], [], 0
        start_time = time.time()

        if llm_call:
            try:
                response = llm_call(f"Task: {task}\n\nPlease complete this task directly.")
                steps_executed.append(response)
                total_tokens += len(response) // 2
                check_engine.step(response)
                if on_step: on_step("exec", {"step": 1, "tokens": len(response) // 2})
            except Exception as e:
                steps_executed.append(f"[LLM Error: {e}]")
        else:
            steps_executed.append(f"[Simulated response for: {task[:50]}]")
            total_tokens += 80

        for i in range(1, max_steps):
            last = steps_executed[-1]
            if self._is_answer_complete(last):
                if on_step: on_step("complete", {"step": i + 1, "reason": "complete"})
                break

            check = check_engine.step(last)
            if check["trigger_mid"]:
                check_logs.append({"step": i + 1, "level": "mid", "reason": check["reason"]})
                if on_step: on_step("mid_check", check_logs[-1])
                if llm_call:
                    try:
                        fixed = llm_call(f"Task: {task}\nCurrent: {last[:500]}\nIssue: {check['reason']}\nFix it.")
                        steps_executed.append(fixed); total_tokens += len(fixed) // 2
                    except: pass
            elif check["trigger_god"]:
                check_logs.append({"step": i + 1, "level": "god", "reason": check["reason"]})
                if on_step: on_step("god_check", check_logs[-1])
                if llm_call:
                    try:
                        review = llm_call(f"Original: {task}\nSummary: {last[:500]}\nIssue: {check['reason']}\nRe-do from global view.")
                        steps_executed.append(review); total_tokens += len(review) // 2
                    except: pass
            else:
                break

        elapsed = time.time() - start_time
        stats = check_engine.get_stats()

        result = {
            "success": stats["is_stable"], "actual_steps": stats["total_steps"],
            "actual_tokens": total_tokens, "elapsed_seconds": round(elapsed, 1),
            "steps": steps_executed, "check_logs": check_logs,
            "step_error": abs(stats["total_steps"] - expected_steps) / max(expected_steps, 1),
            "pitfall_error": stats["total_corrections"] / max(stats["total_steps"], 1),
            "target_error": 0.05, "confidence_error": abs(0.8 - confidence),
            "deviation_count": stats["total_deviations"],
            "correction_count": stats["total_corrections"],
            "mid_checks": stats["mid_checks"], "god_checks": stats["god_checks"],
        }
        self.execution_history.append({"task": task[:80], "result": result})
        return result

    def learn(self, task: str, result: Dict, blueprint: Dict):
        fp = self.fp_db.generate_fingerprint(task, self.task_type, self.domain)
        self.fp_db.add_or_update(fp, result.get("success", True),
            result.get("actual_steps", 5), result.get("actual_tokens", 500),
            blueprint.get("key_nodes", [task]), blueprint.get("pitfall_list", []), "")
        new_weights = self.weight_system.update_weights(self.task_type, self.domain,
            result.get("success", True), result.get("step_error", 0.1),
            result.get("pitfall_error", 0.1), result.get("target_error", 0.05),
            result.get("confidence_error", 0.2))
        return {"fingerprint_updated": True, "new_weights": new_weights,
                "fp_stats": self.fp_db.get_stats()}

    def get_status(self) -> dict:
        stats = self.fp_db.get_stats()
        exp = self.weight_system.get_experience_level(self.task_type, self.domain)
        return {"fingerprints": stats, "experience": exp, "execution_count": len(self.execution_history)}

    def _is_answer_complete(self, response: str) -> bool:
        return len(response) > 100 and (any(k in response[:100] for k in
            ["conclusion", "summary", "总结", "结论", "推荐"]))
