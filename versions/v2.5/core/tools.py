"""
乾 Tools — 基础文件操作 + 代码执行
====================================
write_file, read_file, list_dir, run_python

设计哲学: 乾不替代龙虾(OpenClaw), 但提供最小可用的自我操作能力
- 写报告/文档/代码到文件
- 检查文件是否存在
- 运行简单Python脚本

姚忻 · 2026.06.17
"""

import os, sys, subprocess, json
from pathlib import Path
from typing import Dict, Any


class QianTools:
    """乾的工具集 — 轻量, 安全, 可扩展"""

    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace or os.getcwd())
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.tool_log = []

    def _log(self, tool: str, params: dict, result: str):
        self.tool_log.append({"tool": tool, "params": params, "result": result[:100]})

    # ── File operations ──

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """写入文件到工作区"""
        full = self.workspace / path
        full.parent.mkdir(parents=True, exist_ok=True)
        try:
            full.write_text(content, encoding="utf-8")
            sz = len(content)
            self._log("write_file", {"path": path}, f"OK ({sz} chars)")
            return {"success": True, "path": str(full), "size": sz}
        except Exception as e:
            self._log("write_file", {"path": path}, f"FAIL: {e}")
            return {"success": False, "error": str(e)}

    def read_file(self, path: str) -> Dict[str, Any]:
        """读取文件"""
        full = self.workspace / path
        try:
            content = full.read_text(encoding="utf-8")
            self._log("read_file", {"path": path}, f"OK ({len(content)} chars)")
            return {"success": True, "content": content, "size": len(content)}
        except Exception as e:
            self._log("read_file", {"path": path}, f"FAIL: {e}")
            return {"success": False, "error": str(e)}

    def list_dir(self, path: str = ".") -> Dict[str, Any]:
        """列出目录内容"""
        full = self.workspace / path
        try:
            items = []
            for f in full.iterdir():
                items.append({"name": f.name, "type": "dir" if f.is_dir() else "file",
                              "size": f.stat().st_size if f.is_file() else 0})
            self._log("list_dir", {"path": path}, f"OK ({len(items)} items)")
            return {"success": True, "items": items}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def file_exists(self, path: str) -> bool:
        return (self.workspace / path).exists()

    # ── Code execution ──

    def run_python(self, code: str, timeout: int = 10) -> Dict[str, Any]:
        """运行Python代码并捕获输出 (沙箱: 独立进程)"""
        try:
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True, text=True,
                timeout=timeout, cwd=str(self.workspace),
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            self._log("run_python", {"code": code[:80]},
                      f"exit={result.returncode}")
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout ({timeout}s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_command(self, cmd: str, timeout: int = 10) -> Dict[str, Any]:
        """运行shell命令"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=str(self.workspace),
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Tool call parser ──

    TOOL_SCHEMA = {
        "write_file":  {"params": ["path", "content"], "desc": "写入文件"},
        "read_file":   {"params": ["path"],          "desc": "读取文件"},
        "list_dir":    {"params": ["path"],          "desc": "列出目录"},
        "run_python":  {"params": ["code"],          "desc": "运行Python"},
        "run_command": {"params": ["cmd"],           "desc": "运行命令"},
    }

    def execute_tool(self, tool_name: str, params: dict) -> dict:
        """统一工具调用入口"""
        tools = {
            "write_file": self.write_file,
            "read_file": self.read_file,
            "list_dir": self.list_dir,
            "run_python": self.run_python,
            "run_command": self.run_command,
        }
        if tool_name not in tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        try:
            return tools[tool_name](**params)
        except TypeError as e:
            return {"success": False, "error": f"Missing params for {tool_name}: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_tools_prompt(self) -> str:
        """生成工具说明, 注入到 agent prompt"""
        lines = ["[Available Tools]"]
        for name, schema in self.TOOL_SCHEMA.items():
            params = ", ".join(schema["params"])
            lines.append(f"  {name}({params}) — {schema['desc']}")
        lines.append(f"\nWorkspace: {self.workspace}")
        lines.append("To use a tool, output: [TOOL:tool_name] {{\"param\": \"value\"}}")
        return "\n".join(lines)

    def get_stats(self) -> dict:
        return {"total_calls": len(self.tool_log),
                "recent": self.tool_log[-5:] if self.tool_log else []}
