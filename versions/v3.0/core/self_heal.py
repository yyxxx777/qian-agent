"""
Self-Healing Engine — 乾 V2.5 自修复熔断回路
================================================
TDD式自我修复: 检测错误 → 读代码 → LLM生成修复 → 备份 → 应用 → 测试
  → 通过 → 提交 → 写文档
  → 失败 → 分析 → 重试(max 3) → 全失败 → 回滚 → 报告

设计哲学: 能修就修, 修不好不乱动, 每次都留后路

姚忻 · 2026.06.17
"""

import os, time, shutil, json, subprocess, sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple


@dataclass
class HealAttempt:
    attempt: int
    fix_code: str
    test_result: dict
    passed: bool
    analysis: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class HealResult:
    success: bool
    target_file: str
    backup_file: str
    attempts: List[HealAttempt]
    doc_generated: str = ""
    reason: str = ""


class SelfHealEngine:
    """TDD熔断自修复引擎"""

    MAX_ATTEMPTS = 3
    DOC_DIR = ".qian_heal_logs"

    def __init__(self, llm_call: Callable, workspace: str = None):
        self.llm = llm_call
        self.workspace = Path(workspace or os.getcwd())
        self.log_dir = self.workspace / self.DOC_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.heal_history: List[HealResult] = []

    # ── Main entry ──
    def heal(self, error_log: str, target_file: str,
             test_code: str = None) -> HealResult:
        """
        主入口: 给定错误日志 + 目标文件 + 测试代码 → 自动修复
        
        error_log: 错误信息 (traceback)
        target_file: 要修复的文件路径 (相对workspace)
        test_code: 验证修复的Python测试代码
        """
        target_path = self.workspace / target_file
        if not target_path.exists():
            return HealResult(False, target_file, "",
                            [], "", f"Target file not found: {target_file}")

        # 1. 备份
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"{target_file}.bak.{timestamp}"
        backup_path = self.workspace / backup_name
        shutil.copy2(target_path, backup_path)

        # 2. 读取原代码
        original = target_path.read_text(encoding="utf-8")

        attempts = []
        current_code = original

        for i in range(1, self.MAX_ATTEMPTS + 1):
            # 生成修复
            fix_code = self._generate_fix(target_file, current_code, error_log, test_code, i)

            if not fix_code or fix_code == current_code:
                attempts.append(HealAttempt(i, "", {}, False, "LLM无法生成有效修复"))
                continue

            # 写入
            try:
                target_path.write_text(fix_code, encoding="utf-8")
            except Exception as e:
                attempts.append(HealAttempt(i, fix_code[:200], {}, False, f"写入失败: {e}"))
                continue

            # 测试
            test_result = self._run_test(test_code) if test_code else {"success": True, "note": "no test provided"}
            passed = test_result.get("success", False)

            analysis = ""
            if not passed:
                analysis = self._analyze_failure(test_result, fix_code, error_log)

            attempts.append(HealAttempt(i, fix_code[:200], test_result, passed, analysis))

            if passed:
                # 成功! 生成文档
                doc = self._generate_doc(target_file, original, fix_code, error_log, attempts)
                break
            else:
                current_code = fix_code

        # 3. 判断结果
        all_failed = all(not a.passed for a in attempts)
        if all_failed:
            # 回滚
            shutil.copy2(backup_path, target_path)
            return HealResult(False, target_file, backup_name,
                            attempts, "", "所有修复尝试均失败, 已回滚")

        return HealResult(True, target_file, backup_name,
                        attempts, doc, "修复成功")

    # ── Internal methods ──

    def _generate_fix(self, filename: str, code: str, error: str,
                      test: str, attempt: int) -> str:
        """LLM生成修复代码"""
        prompt = f"""You are debugging a Python project. Fix the error.

File: {filename}
Error:
{error}

Current code:
```python
{code[:3000]}
```

{("Test code that MUST pass after fix:\n```python\n" + test + "\n```") if test else ""}

This is attempt {attempt} of {self.MAX_ATTEMPTS}.
{f'Previous attempt failed. Try a different approach.' if attempt > 1 else ''}

Rules:
1. Make MINIMAL changes - only fix what's broken
2. Keep all existing imports and class structure
3. Output ONLY the complete fixed file, nothing else
4. Do NOT add markdown code blocks - output raw Python

Output the complete fixed file:"""

        try:
            result = self.llm(prompt, max_tokens=4000, temperature=0.2)
            # Strip any markdown wrapping
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("python"): result = result[6:]
                result = result.strip()
            return result.strip()
        except Exception as e:
            return ""

    def _run_test(self, test_code: str) -> dict:
        """运行测试代码, 返回 {success, stdout, stderr}"""
        try:
            r = subprocess.run(
                [sys.executable, "-c", test_code],
                capture_output=True, text=True,
                timeout=10, cwd=str(self.workspace),
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            return {
                "success": r.returncode == 0,
                "stdout": r.stdout.strip(),
                "stderr": r.stderr.strip(),
                "exit_code": r.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "stderr": "Timeout (10s)"}
        except Exception as e:
            return {"success": False, "stderr": str(e)}

    def _analyze_failure(self, test_result: dict, fix_code: str,
                         original_error: str) -> str:
        """分析失败原因"""
        stderr = test_result.get("stderr", "")
        if not stderr: return "test failed with no output"
        return stderr[:500]

    def _generate_doc(self, filename: str, original: str,
                      fixed: str, error: str,
                      attempts: List[HealAttempt]) -> str:
        """生成修复文档"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        doc_name = f"{filename.replace('/','_')}_heal_{timestamp}.md"
        doc_path = self.log_dir / doc_name

        attempted = len(attempts)
        passed_attempt = next((i+1 for i, a in enumerate(attempts) if a.passed), attempted)

        content = f"""# Self-Heal Report: {filename}

**Time**: {timestamp}
**Error**: 
```
{error[:500]}
```

**Result**: ✅ Fixed (attempt {passed_attempt}/{attempted})

## Changes Made
```diff
# Original → Fixed
# Attempts: {attempted}, Succeeded on attempt {passed_attempt}
```

## Verification
```
{attempts[-1].test_result.get('stdout','(no output)')}
```

## Backup
Restore with: `cp {filename}.bak.* {filename}`

---
Generated by Qian SelfHeal Engine
"""
        doc_path.write_text(content, encoding="utf-8")
        return str(doc_path)

    def get_history(self) -> list:
        return [{
            "file": h.target_file,
            "success": h.success,
            "attempts": len(h.attempts),
            "reason": h.reason[:80] if h.reason else "",
        } for h in self.heal_history]
