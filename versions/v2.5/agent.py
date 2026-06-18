"""
乾Agent V2.5 — 对立视角 + 发散模式 + 人格引擎 + 认知调度
===========================================================
V2.1 全部能力 + AdversarialEngine + DivergentEngine

姚忻 · 2026.06.17
"""

import time, sys, os
from typing import Dict, List, Optional, Callable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.v1.fingerprint_db import ExperienceFingerprintDB
from core.v1.dynamic_check import DynamicCheckEngine
from core.v1.adaptive_weights import AdaptiveWeightSystem
from core.task_template import TaskTemplateDB, TaskTemplate
from core.meta_check import MetaCheckEngine
from core.personality import PersonalityEngine
from core.orchestrator import CognitiveOrchestrator, EngineMode
from core.adversarial import AdversarialEngine
from core.divergent import DivergentEngine
from core.tools import QianTools
from core.self_heal import SelfHealEngine
from shared.stats_tracker import StatsTracker


class QianAgent:
    """乾 V2.5 — 会学习 + 有性格 + 能深度反思 + 有创造力"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(data_dir, exist_ok=True)
        self.fp_db = ExperienceFingerprintDB(os.path.join(data_dir, "fingerprints.json"))
        self.weight_system = AdaptiveWeightSystem(os.path.join(data_dir, "weights.json"))
        self.template_db = TaskTemplateDB(
            os.path.join(data_dir, "templates.json"),
            os.path.join(data_dir, "seed_templates.json"))
        self.meta_check = MetaCheckEngine()
        self.tracker = StatsTracker(os.path.join(data_dir, "evolution.json"))
        self.personality = PersonalityEngine()
        self.orchestrator = CognitiveOrchestrator()
        self.adversarial = AdversarialEngine()
        self.divergent = DivergentEngine()
        self.tools = QianTools(os.path.join(data_dir, "workspace"))
        self.healer = SelfHealEngine(llm_call=None, workspace=data_dir)
        self.task_type = "code"
        self.domain = "general"
        self.consecutive_no_adversarial = 0
        self.execution_history: List[Dict] = []
        self._predict_cache: Dict[str, Dict] = {}  # perf

    # ── Predict (same as V2.1 + divergent awareness) ──
    def predict(self, task: str, task_type: str = "code", domain: str = "general") -> Dict:
        self.task_type = task_type; self.domain = domain
        # perf: session cache
        ck = f"{task[:80]}|{task_type}|{domain}"
        if ck in self._predict_cache:
            return self._predict_cache[ck]
        if len(task) < 6:  # perf: treat very short input as trivial
            return self._make_pred("trivial", confidence=0.95, steps=1, tokens=100,
                                   note="trivial task", _task=task)

        # Template
        template = None; template_match = None
        try:
            template = self.template_db.extract(task)
            if template: template_match = self.template_db.match(template)
        except: pass

        # Instance fingerprint
        match_result = None
        try: match_result = self.fp_db.match(task, task_type, domain)
        except: pass
        fp = match_result["fingerprint"] if match_result else None
        similarity = match_result.get("similarity", 0) if match_result else 0
        match_level = match_result.get("match_level", "none") if match_result else "none"
        experience_info = self.weight_system.get_experience_level(task_type, domain)

        # Orchestrator
        tmpl_hit = bool(template_match)
        is_creative = domain in ("design", "creative") or task_type in ("design", "write")
        friction = 80 if not tmpl_hit else (30 if match_level == "exact" else 55)
        pressure = self.personality.urgency * 100
        self.orchestrator.evaluate(friction, pressure, tmpl_hit, is_creative)

        # Divergent check
        div_config = self.divergent.get_config(task, template.template_type if template else task_type)
        is_divergent = div_config.active

        # Fusion
        if template_match:
            ewma = template_match.ewma_steps
            pits = template_match.get_active_pitfalls()
            steps = max(1, round(ewma)) if ewma and template_match.hit_count >= 2 else max(2, template.complexity // 2)
            tokens = steps * 120
            if match_level in ("exact", "fuzzy") and fp:
                fp_steps = round(fp.get("prediction_model", {}).get("avg_steps", steps))
                steps = min(steps, fp_steps)
            return self._make_pred("template", confidence=min(0.7+template_match.hit_count*0.05, 0.95),
                match_level="template", similarity=0.5+template_match.hit_count*0.05,
                steps=steps, tokens=tokens, pitfalls=pits, use_count=template_match.hit_count,
                success_rate=template_match.success_count/max(template_match.hit_count,1),
                experience=experience_info, template=template_match,
                note=f"模板匹配 · {template_match.hit_count}次参考" + (" [发散模式]" if is_divergent else ""),
                divergent=is_divergent, _task=task)

        if match_level != "none" and fp:
            model = fp.get("prediction_model", {})
            confidence = similarity*0.7 + fp.get("stats",{}).get("success_rate",0.5)*0.3
            steps = max(2, round(model.get("avg_steps",5)))
            tokens = max(200, round(model.get("avg_tokens", steps*80)))
            return self._make_pred(match_level, confidence=min(confidence,0.95),
                match_level=match_level, similarity=round(similarity,2),
                steps=steps, tokens=tokens,
                key_nodes=fp.get("solution_template",{}).get("key_nodes",[]),
                pitfalls=fp.get("solution_template",{}).get("pitfall_list",[]),
                use_count=fp.get("meta",{}).get("use_count",0),
                success_rate=round(fp.get("stats",{}).get("success_rate",0.5),2),
                experience=experience_info, note="实例匹配",
                divergent=is_divergent, _task=task)

        return self._make_pred("cold", confidence=0.2, match_level="none", similarity=0.0,
            steps=6, tokens=500, experience=experience_info,
            note="新领域 · 执行后将自动学习", divergent=is_divergent, _task=task)

    def _make_pred(self, mode, **kw) -> Dict:
        result = {
            "mode": mode, "confidence": kw.get("confidence",0.2),
            "match_level": kw.get("match_level","cold"),
            "similarity": kw.get("similarity",0.0),
            "expected_steps": kw.get("steps",6),
            "expected_tokens": kw.get("tokens",500),
            "key_nodes": kw.get("key_nodes",[]),
            "pitfall_list": kw.get("pitfalls",[]),
            "verify_method": kw.get("verify_method",""),
            "use_count": kw.get("use_count",0),
            "success_rate": kw.get("success_rate",0.0),
            "experience": kw.get("experience",{}),
            "note": kw.get("note",""),
            "_template": kw.get("template"),
            "personality": self.personality.snapshot(),
            "orchestrator": self.orchestrator.snapshot(),
            "divergent": kw.get("divergent", False),
        }
        # perf: auto-cache
        task = kw.get("_task","")
        if len(task) >= 15:
            ck = f"{task[:80]}|{self.task_type}|{self.domain}"
            self._predict_cache[ck] = result
        return result
    # ── Execute (V2.5: + adversarial deep check + divergent mode) ──
    def execute(self, task: str, blueprint: Dict, llm_call=None,
                max_steps=None, on_step=None) -> Dict:
        match_level = blueprint.get("match_level", "cold") or "cold"
        is_divergent = blueprint.get("divergent", False)
        expected_steps = max(2, int(blueprint.get("expected_steps", 5) or 5))
        if max_steps is None: max_steps = min(expected_steps + 1, 6)  # perf: tighter

        check_engine = DynamicCheckEngine(task, expected_steps,
            blueprint.get("key_nodes", []), blueprint.get("pitfall_list", []))

        steps_executed, check_logs, total_tokens = [], [], 0
        start_time = time.time()

        # Divergent: boost temperature + inject stimulus
        extra_prompt = ""
        if is_divergent:
            extra_prompt = self.divergent.to_prompt_extension(
                task, self.task_type, self.template_db)

        if llm_call:
            prompt = f"Task: {task}\n{extra_prompt}\n{self.tools.get_tools_prompt()}\n\nPlease complete this task. Use tools if needed."
            try:
                temp = 0.9 if is_divergent else 0.7
                response = llm_call(prompt, temperature=temp)
                steps_executed.append(response)
                total_tokens += len(response) // 2
                check_engine.step(response)
                # Tool execution interception
                tool_results = _execute_tools_in_response(response, self.tools)
                if tool_results:
                    for tr in tool_results:
                        steps_executed.append(tr)
                        total_tokens += len(tr) // 2
                if on_step: on_step("exec", {"step":1, "tokens":len(response)//2})
            except Exception as e:
                steps_executed.append(f"[LLM Error: {e}]")
        else:
            steps_executed.append(f"[Simulated] {task[:50]}")
            total_tokens += 80

        
        # perf: fast-path for high-confidence matches
        _conf = blueprint.get("confidence", 0.2)
        if (not is_divergent and _conf > 0.75 and
            match_level in ("exact", "template") and
            len(steps_executed[-1]) > 200):
            max_steps = 1
            if on_step: on_step("complete", {"step": 1, "reason": "fast-path"})

        for i in range(1, max_steps):
            last = steps_executed[-1]
            if self._is_answer_complete(last) and i >= expected_steps - 1:
                break

            # Divergent: skip mid-check to allow creativity
            if is_divergent:
                if on_step: on_step("complete", {"step": i+1, "reason": "divergent complete"})
                break

            check = check_engine.step(last)
            if check["trigger_mid"]:
                check_logs.append({"step":i+1,"level":"mid","reason":check["reason"]})
                if on_step: on_step("mid_check", check_logs[-1])
                if llm_call:
                    try:
                        fixed = llm_call(f"Fix: {check['reason']}\n{last[:500]}")
                        steps_executed.append(fixed); total_tokens += len(fixed)//2
                    except: pass
            elif check["trigger_god"]:
                check_logs.append({"step":i+1,"level":"god","reason":check["reason"]})
                if on_step: on_step("god_check", check_logs[-1])
                if llm_call:
                    try:
                        review = llm_call(f"Re-do: {task}\nIssue: {check['reason']}\n{last[:500]}")
                        steps_executed.append(review); total_tokens += len(review)//2
                    except: pass
            else:
                break

        # V2.5: Adversarial deep check (only for non-trivial, non-divergent tasks)
        ad_result = ""
        if not is_divergent and len(steps_executed[-1]) > 200 and llm_call:
            risk = {"exact": 20, "fuzzy": 40, "template": 50, "cold": 70}.get(match_level, 50)
            should, num = self.adversarial.should_trigger(risk, blueprint["confidence"],
                                                          self.consecutive_no_adversarial)
            if should:
                # Inject adversarial critique into output
                self.adversarial.llm = llm_call
                results = self.adversarial.synthesize(
                    self.adversarial.deep_check(steps_executed[-1], task, num))
                if results:
                    ad_result = results
                    self.consecutive_no_adversarial = 0
                    check_logs.append({"step": i+2, "level": "adversarial", "reason": results[:80]})
                    if on_step: on_step("mid_check", {"step":i+2,"level":"adversarial","reason":results[:80]})
                else:
                    self.consecutive_no_adversarial += 1
            else:
                self.consecutive_no_adversarial += 1

        elapsed = time.time() - start_time
        stats = check_engine.get_stats()

        return {
            "success": stats["is_stable"], "actual_steps": stats["total_steps"],
            "actual_tokens": total_tokens, "elapsed_seconds": round(elapsed, 1),
            "steps": steps_executed, "check_logs": check_logs,
            "step_error": abs(stats["total_steps"]-expected_steps)/max(expected_steps,1),
            "pitfall_error": stats["total_corrections"]/max(stats["total_steps"],1),
            "target_error": 0.05, "confidence_error": abs(0.8-blueprint.get("confidence",0.5)),
            "deviation_count": stats["total_deviations"],
            "correction_count": stats["total_corrections"],
            "mid_checks": stats["mid_checks"], "god_checks": stats["god_checks"],
            "adversarial_result": ad_result,
        }

    # ── Learn ──
    def learn(self, task: str, result: Dict, blueprint: Dict):
        actual_steps = result.get("actual_steps", 1)
        actual_tokens = result.get("actual_tokens", 500)
        mid = result.get("mid_checks", 0); god = result.get("god_checks", 0)
        corrections = result.get("correction_count", 0)
        predicted = blueprint.get("expected_steps", 5)
        match_level = blueprint.get("match_level", "cold")
        success = result.get("success", True)

        fp = self.fp_db.generate_fingerprint(task, self.task_type, self.domain)
        self.fp_db.add_or_update(fp, success, actual_steps, actual_tokens,
            blueprint.get("key_nodes", [task]), blueprint.get("pitfall_list", []), "")

        tmpl = blueprint.get("_template")
        if tmpl is None and len(task) >= 15:
            tmpl = self.template_db.get_or_create(task)
        template_type = tmpl.template_type if tmpl else self.task_type
        if tmpl:
            tmpl.track(actual_steps)
            for l in result.get("check_logs", []):
                if l.get("reason"): tmpl.add_pitfall(l["reason"])
            self.template_db._save()

        new_weights = self.weight_system.update_weights(
            self.task_type, self.domain, success,
            result.get("step_error", 0.1), result.get("pitfall_error", 0.1),
            result.get("target_error", 0.05), result.get("confidence_error", 0.2))

        self.tracker.record(task, template_type, predicted, actual_steps,
            int(result.get("elapsed_seconds",0)*1000), actual_tokens, mid, god, corrections)

        active_pits = tmpl.get_active_pitfalls() if tmpl else []
        self.meta_check.check_ewma(predicted, actual_steps, mid, god)
        self.meta_check.check_pitfall_self_fulfilling(
            active_pits, [l["reason"] for l in result.get("check_logs",[]) if l.get("reason")])

        # Personality
        self.personality.decay()
        if match_level == "cold": self.personality.apply_event("cold_start")
        elif match_level == "template": self.personality.apply_event("template_match")
        if success:
            self.personality.apply_event("task_success")
            if abs(predicted-actual_steps) <= 1: self.personality.apply_event("prediction_correct")
            else: self.personality.apply_event("prediction_wrong")
        else: self.personality.apply_event("task_fail")
        if corrections > 0: self.personality.apply_event("pitfall_hit", magnitude=min(corrections/3,1.0))
        if mid==0 and god==0 and corrections==0 and match_level!="cold":
            self.personality.apply_event("pitfall_avoided")

        return {
            "fingerprint_updated": True, "new_weights": new_weights,
            "fp_stats": self.fp_db.get_stats(),
            "template_stats": self.template_db.get_stats(),
            "evolution": self.tracker.get_summary(),
            "meta_alerts": self.meta_check.get_summary(),
            "personality": self.personality.snapshot(),
            "orchestrator": self.orchestrator.snapshot(),
            "divergent": self.divergent.snapshot(),
            "adversarial": self.adversarial.snapshot(),
        }

    def get_status(self) -> dict:
        stats = self.fp_db.get_stats()
        exp = self.weight_system.get_experience_level(self.task_type, self.domain)
        return {"fingerprints": stats, "experience": exp, "execution_count": len(self.execution_history)}

    def self_heal(self, error_log: str, target_file: str,
                  test_code: str = None, llm_call=None) -> dict:
        """TDD熔断自修复: 尝试修复自己的代码"""
        if llm_call: self.healer.llm = llm_call
        result = self.healer.heal(error_log, target_file, test_code)
        return {
            "success": result.success,
            "target": result.target_file,
            "backup": result.backup_file,
            "attempts": len(result.attempts),
            "passed": sum(1 for a in result.attempts if a.passed),
            "doc": result.doc_generated,
            "reason": result.reason,
        }

    def _is_answer_complete(self, response: str) -> bool:
        return len(response) > 100 and any(k in response[:100] for k in
            ["conclusion","summary","总结","结论","推荐","综上","最终"])


def _execute_tools_in_response(response: str, tools) -> list:
    """从LLM输出中检测并执行工具调用"""
    import re, json as _json
    results = []
    pattern = r'\[TOOL:(\w+)\]\s*(\{[^}]+\})'
    for match in re.finditer(pattern, response):
        tool_name = match.group(1)
        try:
            params = _json.loads(match.group(2))
        except: continue
        result = tools.execute_tool(tool_name, params)
        results.append(f"[TOOL:{tool_name}] " + _json.dumps(result, ensure_ascii=False))
    return results
