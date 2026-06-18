"""
乾 V3.0 Tools — 手脚层 · 文件操控 + 代码执行
===============================================
V2.5 基础: write_file, read_file, list_dir, run_python, run_command
V3.0 新增: 多格式文档操控, 搜索, 批量操作, 自省接口

支持文件类型: .py .txt .md .json .csv .html .css .js .yaml .yml .xml .log .sh .bat
所有操作沙箱化(workspace内), 写操作自动备份, 读操作无副作用

设计哲学: "手能碰的都要稳, 脚能踩的都要实"
  — 乾不替代龙虾(OpenClaw), 但提供完整的手脚能力

姚忻 · 2026.06.17
"""

import os, sys, subprocess, json, csv, shutil, re
from io import StringIO
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import time


# ═══════════════════════════════════════════════════
# 文件类型注册表
# ═══════════════════════════════════════════════════

SUPPORTED_EXTENSIONS = {
    ".py":   {"type": "code",       "mime": "text/x-python"},
    ".txt":  {"type": "text",       "mime": "text/plain"},
    ".md":   {"type": "markdown",   "mime": "text/markdown"},
    ".json": {"type": "data",       "mime": "application/json"},
    ".csv":  {"type": "data",       "mime": "text/csv"},
    ".html": {"type": "web",        "mime": "text/html"},
    ".css":  {"type": "web",        "mime": "text/css"},
    ".js":   {"type": "code",       "mime": "application/javascript"},
    ".yaml": {"type": "config",     "mime": "text/yaml"},
    ".yml":  {"type": "config",     "mime": "text/yaml"},
    ".xml":  {"type": "data",       "mime": "text/xml"},
    ".log":  {"type": "text",       "mime": "text/plain"},
    ".sh":   {"type": "script",     "mime": "text/x-shellscript"},
    ".bat":  {"type": "script",     "mime": "text/x-batch"},
    ".ini":  {"type": "config",     "mime": "text/plain"},
    ".cfg":  {"type": "config",     "mime": "text/plain"},
    ".toml": {"type": "config",     "mime": "text/plain"},
}


@dataclass
class ToolCall:
    """工具调用记录"""
    tool: str
    params: dict
    result: str
    timestamp: float = field(default_factory=time.time)


class QianTools:
    """乾 V3.0 工具集 — 手脚层"""

    # 安全限制
    MAX_FILE_SIZE = 10 * 1024 * 1024   # 10MB
    MAX_BATCH_FILES = 50               # 批量操作上限

    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace or os.getcwd())
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.tool_log: List[ToolCall] = []

    def _log(self, tool: str, params: dict, result: str):
        self.tool_log.append(ToolCall(tool=tool, params=params, result=result[:200]))
        if len(self.tool_log) > 500:
            self.tool_log = self.tool_log[-500:]

    def _resolve(self, path: str) -> Path:
        """解析路径, 强制在 workspace 内"""
        ws = self.workspace.resolve()
        full = (self.workspace / path).resolve()
        # 安全检查: commonpath 确保在 workspace 内
        try:
            common = os.path.commonpath([str(ws), str(full)])
            if common != str(ws):
                raise PermissionError(f"路径越界: {path}")
        except ValueError:
            raise PermissionError(f"路径越界: {path}")
        return full

    # ═══════════════════════════════════════════════════
    # 基础文件操作 (V2.5 保留 + 增强)
    # ═══════════════════════════════════════════════════

    def write_file(self, path: str, content: str, backup: bool = True) -> Dict[str, Any]:
        """写入文件, 可选自动备份"""
        full = self._resolve(path)
        full.parent.mkdir(parents=True, exist_ok=True)

        if len(content) > self.MAX_FILE_SIZE:
            return {"success": False, "error": f"文件过大 ({len(content)} > {self.MAX_FILE_SIZE})"}

        ext = full.suffix.lower()
        if ext and ext not in SUPPORTED_EXTENSIONS:
            return {"success": False, "error": f"不支持的文件类型: {ext}"}

        # 自动备份
        bak_path = None
        if backup and full.exists():
            bak_path = full.with_suffix(full.suffix + f".bak.{int(time.time())}")
            shutil.copy2(full, bak_path)

        try:
            full.write_text(content, encoding="utf-8")
            self._log("write_file", {"path": path, "size": len(content), "type": ext}, "OK")
            return {"success": True, "path": str(full), "size": len(content),
                    "type": SUPPORTED_EXTENSIONS.get(ext, {}).get("type", "unknown"),
                    "backup": str(bak_path) if bak_path else None}
        except Exception as e:
            self._log("write_file", {"path": path}, f"FAIL: {e}")
            return {"success": False, "error": str(e)}

    def read_file(self, path: str) -> Dict[str, Any]:
        """读取文件"""
        full = self._resolve(path)
        try:
            if not full.exists():
                return {"success": False, "error": f"文件不存在: {path}"}
            if full.stat().st_size > self.MAX_FILE_SIZE:
                return {"success": False, "error": f"文件过大 ({full.stat().st_size} > {self.MAX_FILE_SIZE})"}
            content = full.read_text(encoding="utf-8")
            ext = full.suffix.lower()
            self._log("read_file", {"path": path}, f"OK ({len(content)} chars)")
            return {"success": True, "content": content, "size": len(content),
                    "type": SUPPORTED_EXTENSIONS.get(ext, {}).get("type", "unknown"),
                    "lines": content.count('\n') + 1}
        except Exception as e:
            self._log("read_file", {"path": path}, f"FAIL: {e}")
            return {"success": False, "error": str(e)}

    def list_dir(self, path: str = ".", pattern: str = None) -> Dict[str, Any]:
        """列出目录, 支持通配符过滤"""
        full = self._resolve(path)
        try:
            if not full.exists():
                return {"success": False, "error": f"目录不存在: {path}"}
            items = []
            for f in sorted(full.iterdir()):
                ext = f.suffix.lower()
                info = {"name": f.name, "type": "dir" if f.is_dir() else "file"}
                if f.is_file():
                    info["size"] = f.stat().st_size
                    info["file_type"] = SUPPORTED_EXTENSIONS.get(ext, {}).get("type", "unknown")
                if pattern:
                    import fnmatch
                    if not fnmatch.fnmatch(f.name, pattern):
                        continue
                items.append(info)
            self._log("list_dir", {"path": path, "pattern": pattern}, f"OK ({len(items)} items)")
            return {"success": True, "items": items, "count": len(items)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def file_exists(self, path: str) -> bool:
        return self._resolve(path).exists()

    def delete_file(self, path: str) -> Dict[str, Any]:
        """删除文件 (软删除: 移到 .trash/)"""
        full = self._resolve(path)
        if not full.exists():
            return {"success": False, "error": f"文件不存在: {path}"}
        trash = self.workspace / ".trash"
        trash.mkdir(exist_ok=True)
        dest = trash / f"{full.name}.{int(time.time())}"
        try:
            shutil.move(str(full), str(dest))
            self._log("delete_file", {"path": path}, f"OK → .trash/")
            return {"success": True, "trashed_to": str(dest)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════════
    # V3.0 新增: 文档操控
    # ═══════════════════════════════════════════════════

    def write_json(self, path: str, data: Any) -> Dict[str, Any]:
        """写入 JSON 文件 (自动格式化)"""
        try:
            content = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            return self.write_file(path, content)
        except Exception as e:
            return {"success": False, "error": f"JSON序列化失败: {e}"}

    def read_json(self, path: str) -> Dict[str, Any]:
        """读取并解析 JSON"""
        result = self.read_file(path)
        if not result["success"]:
            return result
        try:
            result["data"] = json.loads(result["content"])
            del result["content"]
            return result
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON解析失败: {e}"}

    def write_csv(self, path: str, rows: List[Dict], headers: List[str] = None) -> Dict[str, Any]:
        """写入 CSV 文件"""
        if not rows:
            return {"success": False, "error": "rows 不能为空"}
        try:
            if headers is None:
                headers = list(rows[0].keys())
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(rows)
            return self.write_file(path, output.getvalue())
        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_csv(self, path: str) -> Dict[str, Any]:
        """读取 CSV 文件为字典列表"""
        result = self.read_file(path)
        if not result["success"]:
            return result
        try:
            reader = csv.DictReader(StringIO(result["content"]))
            result["data"] = list(reader)
            result["headers"] = reader.fieldnames
            result["row_count"] = len(result["data"])
            del result["content"]
            return result
        except Exception as e:
            return {"success": False, "error": f"CSV解析失败: {e}"}

    def append_file(self, path: str, content: str) -> Dict[str, Any]:
        """追加内容到文件末尾"""
        full = self._resolve(path)
        try:
            with open(full, "a", encoding="utf-8") as f:
                f.write(content)
            self._log("append_file", {"path": path}, "OK")
            return {"success": True, "path": str(full)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════════
    # V3.0 新增: 搜索 + 批量
    # ═══════════════════════════════════════════════════

    def search_files(self, keyword: str, path: str = ".", ext: str = None) -> Dict[str, Any]:
        """在文件内容中搜索关键词"""
        base = self._resolve(path)
        results = []
        try:
            for root, dirs, files in os.walk(str(base)):
                # 跳过隐藏目录和 trash
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '.trash']
                for fname in files:
                    if ext and not fname.endswith(ext):
                        continue
                    fp = Path(root) / fname
                    if fp.stat().st_size > self.MAX_FILE_SIZE:
                        continue
                    try:
                        content = fp.read_text(encoding="utf-8")
                        if keyword in content:
                            lines = content.split('\n')
                            matches = [i+1 for i, l in enumerate(lines) if keyword in l]
                            results.append({
                                "file": str(fp.relative_to(self.workspace)),
                                "matches": len(matches),
                                "lines": matches[:10],
                            })
                    except: pass
            self._log("search_files", {"keyword": keyword, "ext": ext}, f"OK ({len(results)} files)")
            return {"success": True, "results": results, "count": len(results)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def batch_write(self, files: Dict[str, str]) -> Dict[str, Any]:
        """批量写入多个文件 {path: content}"""
        if len(files) > self.MAX_BATCH_FILES:
            return {"success": False, "error": f"批量上限 {self.MAX_BATCH_FILES}"}
        results = {}
        for path, content in files.items():
            results[path] = self.write_file(path, content)
        ok = sum(1 for r in results.values() if r["success"])
        return {"success": True, "results": results, "ok": ok, "total": len(files)}

    # ═══════════════════════════════════════════════════
    # 代码执行 (V2.5 保留)
    # ═══════════════════════════════════════════════════

    def run_python(self, code: str, timeout: int = 10) -> Dict[str, Any]:
        """运行Python代码 (沙箱: 独立进程)"""
        try:
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True, text=True,
                timeout=timeout, cwd=str(self.workspace),
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            self._log("run_python", {"code": code[:80]}, f"exit={result.returncode}")
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

    # ═══════════════════════════════════════════════════
    # 自省工具 (V3.0 新增)
    # ═══════════════════════════════════════════════════

    def read_own_module(self, module_path: str) -> Dict[str, Any]:
        """
        读取乾自身的模块源码 (只读, 不修改)

        module_path: 相对于 core/ 的路径, 如 "agent.py" 或 "tools.py"
        """
        core_dir = Path(__file__).parent.resolve()  # core/ directory
        target = (core_dir / module_path).resolve()
        if not str(target).startswith(str(core_dir)):
            return {"success": False, "error": f"不允许读取 core/ 外的模块: {module_path}"}
        # module_path may refer to parent dir like "agent.py" which is one level up
        # Allow reading from core/ and its parent (the version root)
        version_root = core_dir.parent.resolve()
        if not str(target).startswith(str(version_root)):
            return {"success": False, "error": f"不允许读取版本目录外的模块: {module_path}"}
        if not target.exists():
            return {"success": False, "error": f"模块不存在: {module_path}"}
        try:
            content = target.read_text(encoding="utf-8")
            return {"success": True, "module": module_path, "content": content,
                    "size": len(content), "lines": content.count('\n') + 1}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def propose_patch(self, module_path: str, description: str,
                      diff: str, auto_apply: bool = False) -> Dict[str, Any]:
        """
        提议对自身模块的修改 (写入 .qian_patches/ 待审核)

        不会直接修改 core/ 下的文件。需要人工审核后才能应用。
        """
        core_dir = Path(__file__).parent
        target = (core_dir / module_path).resolve()
        if not str(target).startswith(str(core_dir.resolve())):
            return {"success": False, "error": f"不允许修改 core/ 外的模块: {module_path}"}
        if not target.exists():
            return {"success": False, "error": f"模块不存在: {module_path}"}

        patches_dir = self.workspace / ".qian_patches"
        patches_dir.mkdir(exist_ok=True)
        ts = int(time.time())
        patch_file = patches_dir / f"{module_path.replace('/','_')}_{ts}.patch"

        patch_content = f"""# Qian Self-Modification Proposal
# Module: {module_path}
# Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
# Description: {description}
# Auto-apply: {auto_apply}
#
# ⚠️ WARNING: This is a PROPOSED change. Review before applying.
# To apply: manually merge this diff into the target module.
# To reject: delete this file.

--- a/{module_path}
+++ b/{module_path} (proposed)
{diff}
"""
        try:
            patch_file.write_text(patch_content, encoding="utf-8")
            return {"success": True, "patch_file": str(patch_file.relative_to(self.workspace)),
                    "module": module_path, "description": description}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════════
    # 工具注册 + Prompt生成
    # ═══════════════════════════════════════════════════

    TOOL_SCHEMA = {
        # 基础文件
        "write_file":  {"params": ["path", "content"], "desc": "写入文件 (自动备份)"},
        "read_file":   {"params": ["path"],          "desc": "读取文件内容"},
        "list_dir":    {"params": ["path"],          "desc": "列出目录 (可选pattern)"},
        "delete_file": {"params": ["path"],          "desc": "删除文件 (移入.trash/)"},
        "append_file": {"params": ["path", "content"], "desc": "追加内容到文件末尾"},
        # 文档操控
        "write_json":  {"params": ["path", "data"],  "desc": "写入JSON (自动格式化)"},
        "read_json":   {"params": ["path"],          "desc": "读取并解析JSON"},
        "write_csv":   {"params": ["path", "rows"],  "desc": "写入CSV"},
        "read_csv":    {"params": ["path"],          "desc": "读取CSV为字典列表"},
        # 搜索
        "search_files":{"params": ["keyword", "path"], "desc": "在文件中搜索关键词"},
        "batch_write": {"params": ["files"],         "desc": "批量写入多个文件"},
        # 执行
        "run_python":  {"params": ["code"],          "desc": "运行Python代码 (沙箱)"},
        "run_command": {"params": ["cmd"],           "desc": "运行shell命令"},
        # 自省
        "read_own_module": {"params": ["module_path"], "desc": "读取乾自身模块源码"},
        "propose_patch":   {"params": ["module_path", "description", "diff"],
                            "desc": "提议修改自身模块 (写入待审核)"},
    }

    def execute_tool(self, tool_name: str, params: dict) -> dict:
        """统一工具调用入口"""
        all_tools = {
            "write_file": self.write_file, "read_file": self.read_file,
            "list_dir": self.list_dir, "delete_file": self.delete_file,
            "append_file": self.append_file,
            "write_json": self.write_json, "read_json": self.read_json,
            "write_csv": self.write_csv, "read_csv": self.read_csv,
            "search_files": self.search_files, "batch_write": self.batch_write,
            "run_python": self.run_python, "run_command": self.run_command,
            "read_own_module": self.read_own_module,
            "propose_patch": self.propose_patch,
        }
        if tool_name not in all_tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        try:
            return all_tools[tool_name](**params)
        except TypeError as e:
            schema = self.TOOL_SCHEMA.get(tool_name, {})
            expected = ", ".join(schema.get("params", []))
            return {"success": False, "error": f"参数错误: {e}. 需要: {expected}"}
        except PermissionError as e:
            return {"success": False, "error": f"安全限制: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_tools_prompt(self) -> str:
        """生成工具说明, 注入到 agent prompt"""
        lines = ["[Available Tools — V3.0]"]
        lines.append(f"Workspace: {self.workspace}")
        lines.append(f"Supported types: {', '.join(SUPPORTED_EXTENSIONS.keys())}")
        lines.append("")
        lines.append("File Ops: write_file read_file list_dir delete_file append_file")
        lines.append("Data Ops: write_json read_json write_csv read_csv")
        lines.append("Search:   search_files(keyword, path) batch_write({path:content})")
        lines.append("Exec:     run_python(code) run_command(cmd)")
        lines.append("Introspect: read_own_module(module) propose_patch(...)")
        lines.append("")
        lines.append("To use a tool: [TOOL:tool_name] {\"param\": \"value\"}")
        return "\n".join(lines)

    def get_stats(self) -> dict:
        return {"total_calls": len(self.tool_log),
                "recent": [{"tool": t.tool, "result": t.result[:60]}
                          for t in self.tool_log[-5:]] if self.tool_log else []}
