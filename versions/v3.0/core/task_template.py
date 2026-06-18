import re
"""
Task Template System — 乾 V2 核心壁垒
========================================
两级指纹的第二级：任务骨架提取与跨任务迁移学习

Level 1: 9种枚举类型 + 三段加权匹配 → 跨实例经验迁移
Level 2: LSH 精确匹配 (fingerprint_db.py, 不动)

姚忻 · 2026.06.17
"""

import json, time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from shared.config import config as cfg

TEMPLATE_TYPES = list(cfg.template_types)
MATCH_WEIGHTS = {
    "verbs": cfg.match_weight_verbs,
    "entities": cfg.match_weight_entities,
    "complexity": cfg.match_weight_complexity,
    "confidence": cfg.match_weight_confidence,
}
EWMA_ALPHA = cfg.ewma_alpha
PITFALL_DECAY = cfg.pitfall_decay_rate
PITFALL_ARCHIVE = cfg.pitfall_archive_threshold
SPLIT_VARIANCE = cfg.template_split_variance


@dataclass
class Pitfall:
    name: str
    freq: float = 1.0
    scope: List[str] = field(default_factory=list)
    last_seen: float = 0.0
    hit_count: int = 0
    miss_count: int = 0

    def to_dict(self): return {"name": self.name, "freq": self.freq, "scope": self.scope,
        "last_seen": self.last_seen, "hit_count": self.hit_count, "miss_count": self.miss_count}
    @classmethod
    def from_dict(cls, d): return cls(**{k: d.get(k, v) for k, v in
        {"name": "", "freq": 1.0, "scope": [], "last_seen": 0.0, "hit_count": 0, "miss_count": 0}.items()})


@dataclass
class TaskTemplate:
    template_id: str
    template_type: str
    verbs: List[str] = field(default_factory=list)
    entity_types: List[str] = field(default_factory=list)
    output_type: str = "text"
    complexity: int = 5
    ewma_steps: Optional[float] = None
    ewma_tokens: Optional[float] = None
    hit_count: int = 0
    success_count: int = 0
    last_updated: float = 0.0
    active_pitfalls: List[Pitfall] = field(default_factory=list)
    archived_pitfalls: List[Pitfall] = field(default_factory=list)
    step_variance: float = 0.0
    recent_steps: List[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"template_id": self.template_id, "template_type": self.template_type,
            "verbs": self.verbs, "entity_types": self.entity_types, "output_type": self.output_type,
            "complexity": self.complexity, "ewma_steps": self.ewma_steps, "ewma_tokens": self.ewma_tokens,
            "hit_count": self.hit_count, "success_count": self.success_count,
            "last_updated": self.last_updated,
            "active_pitfalls": [p.to_dict() for p in self.active_pitfalls],
            "archived_pitfalls": [p.to_dict() for p in self.archived_pitfalls],
            "step_variance": self.step_variance, "recent_steps": self.recent_steps[-10:]}

    @classmethod
    def from_dict(cls, d: dict) -> "TaskTemplate":
        return cls(template_id=d.get("template_id",""), template_type=d.get("template_type","general"),
            verbs=d.get("verbs",[]), entity_types=d.get("entity_types",[]),
            output_type=d.get("output_type","text"), complexity=d.get("complexity",5),
            ewma_steps=d.get("ewma_steps"), ewma_tokens=d.get("ewma_tokens"),
            hit_count=d.get("hit_count",0), success_count=d.get("success_count",0),
            last_updated=d.get("last_updated",0.0),
            active_pitfalls=[Pitfall.from_dict(p) for p in d.get("active_pitfalls",[])],
            archived_pitfalls=[Pitfall.from_dict(p) for p in d.get("archived_pitfalls",[])],
            step_variance=d.get("step_variance",0.0), recent_steps=d.get("recent_steps",[]))

    def get_active_pitfalls(self, min_freq=0.15) -> list:
        a = [p for p in self.active_pitfalls if p.freq >= min_freq]
        a.sort(key=lambda p: p.freq, reverse=True)
        return [{"name": p.name, "freq": round(p.freq, 2), "scope": p.scope} for p in a[:5]]

    def track(self, actual_steps: int, triggered_pitfalls: List[str] = None):
        """Update EWMA, variance, and pitfalls after execution"""
        if self.ewma_steps is None:
            self.ewma_steps = float(actual_steps)
        else:
            self.ewma_steps = EWMA_ALPHA * actual_steps + (1 - EWMA_ALPHA) * self.ewma_steps

        self.recent_steps.append(actual_steps)
        if len(self.recent_steps) > 10:
            self.recent_steps.pop(0)
        if len(self.recent_steps) >= 3:
            m = sum(self.recent_steps) / len(self.recent_steps)
            self.step_variance = sum((s - m) ** 2 for s in self.recent_steps) / len(self.recent_steps)

        self.hit_count += 1
        self.last_updated = time.time()

        # Pitfall decay/boost
        triggered = set(triggered_pitfalls or [])
        for p in self.active_pitfalls:
            if p.name in triggered:
                p.freq = min(1.0, p.freq * 1.1)
                p.hit_count += 1
                p.last_seen = time.time()
            else:
                p.freq *= PITFALL_DECAY
                p.miss_count += 1

        self.active_pitfalls = [p for p in self.active_pitfalls if p.freq >= PITFALL_ARCHIVE]

    def add_pitfall(self, name: str, scope: List[str] = None):
        existing = [p for p in self.active_pitfalls + self.archived_pitfalls if p.name == name]
        if existing:
            existing[0].freq = min(1.0, existing[0].freq * 1.2)
            existing[0].last_seen = time.time()
            if existing[0] in self.archived_pitfalls:
                self.archived_pitfalls.remove(existing[0])
                self.active_pitfalls.append(existing[0])
        else:
            self.active_pitfalls.append(Pitfall(
                name=name, freq=1.0, scope=scope or [self.template_type], last_seen=time.time()))

    def should_split(self) -> bool:
        return len(self.recent_steps) >= 8 and self.step_variance > SPLIT_VARIANCE


# ═══════════════════════════════════════
# Template Database
# ═══════════════════════════════════════
class TaskTemplateDB:
    def __init__(self, db_path=None, seed_path=None):
        base = Path(__file__).parent.parent
        self.db_path = Path(db_path or str(base / "data" / "templates.json"))
        # Always fall back to version's seed file
        default_seed = base / "data" / "seed_templates.json"
        self.seed_path = Path(seed_path or str(default_seed))
        if not self.seed_path.exists() and default_seed.exists():
            self.seed_path = default_seed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.templates: Dict[str, TaskTemplate] = self._load()

    def _load(self) -> dict:
        result = {}
        if self.db_path.exists():
            try:
                data = json.loads(self.db_path.read_text(encoding="utf-8"))
                for tid, td in data.get("templates", {}).items():
                    result[tid] = TaskTemplate.from_dict(td)
            except: pass
        if self.seed_path.exists():
            try:
                seeds = json.loads(self.seed_path.read_text(encoding="utf-8"))
                for s in seeds:
                    tmpl = TaskTemplate(
                        template_id=s["template_id"], template_type=s["template_type"],
                        verbs=s.get("verbs", []), entity_types=s.get("entity_types", []),
                        output_type=s.get("output_type", "text"), complexity=s.get("complexity", 5))
                    # Load seed pitfalls if present
                    for pd in s.get("pitfalls", []):
                        tmpl.active_pitfalls.append(Pitfall.from_dict(pd))
                    if sid not in result: result[sid] = tmpl
                self._save(result)
            except: pass
        return result

    def _save(self, templates=None):
        data = {"templates": {tid: t.to_dict() for tid, t in (templates or self.templates).items()}}
        self.db_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def extract(self, task: str) -> Optional[TaskTemplate]:
        """Rule-based template extraction (0 API calls)"""
                # Count meaningful chunks: each CJK char or English word counts as 1
        chunks = len(re.findall(r'[一-鿿]', task)) + len(re.findall(r'[a-zA-Z]{2,}', task))
        if chunks < 3:
            return None
        tl = task.lower()

        type_map = [
            (["code", "script", "python script", "function", "class ", "implement",
              "def ", "import ", "api", "bug", "fix", "debug", "sql", "query", "爬"],
             "code_generation"),
            (["explain", "what is", "how does", "原理", "区别", "difference", "概念"], "text_explanation"),
            (["analyze", "分析", "stock", "股票", "投资", "数据", "trend", "趋势",
              "evaluate", "评估", "report", "报告"], "data_analysis"),
            (["write", "article", "email", "blog", "写", "generate", "创作", "翻译"], "text_generation"),
            (["design", "architecture", "架构", "system", "系统", "plan", "方案"], "design_planning"),
            (["debug", "diagnose", "诊断", "error", "报错", "出错", "not working"], "debug_diagnosis"),
            (["how to", "tool", "docker", "git", "command", "怎么用", "使用", "配置"], "tool_usage"),
        ]
        tt = "general"
        for keywords, t in type_map:
            if any(k in tl for k in keywords):
                tt = t; break

        verbs = self._extract_verbs(tl)
        entities = self._extract_entities(tl)
        complexity = self._estimate_complexity(task, tl)

        return TaskTemplate(
            template_id=f"{tt}_{hash(task) % 100000:05d}",
            template_type=tt, verbs=verbs, entity_types=entities,
            output_type="code" if tt == "code_generation" else ("report" if tt == "data_analysis" else "text"),
            complexity=complexity)

    def _extract_verbs(self, task_lower: str) -> list:
        m = {"write":"generate","create":"generate","generate":"generate","make":"generate",
             "analyze":"analyze","evaluate":"evaluate","assess":"evaluate","predict":"predict",
             "forecast":"predict","explain":"explain","describe":"explain","tell":"explain",
             "translate":"translate","design":"design","plan":"design","architect":"design",
             "diagnose":"diagnose","debug":"debug","fix":"fix","repair":"fix",
             "configure":"configure","install":"install","setup":"configure","deploy":"deploy",
             "scrape":"scrape","crawl":"scrape","collect":"scrape",
             "optimize":"optimize","improve":"optimize","refactor":"refactor",
             "写":"generate","创建":"create","生成":"generate","分析":"analyze","评估":"evaluate",
             "预测":"predict","解释":"explain","说明":"explain","翻译":"translate","设计":"design",
             "诊断":"diagnose","调试":"debug","修复":"fix","配置":"configure","安装":"install",
             "部署":"deploy","爬":"scrape","优化":"optimize","重构":"refactor"}
        return list(set(en for cn, en in m.items() if cn in task_lower)) or ["execute"]

    def _extract_entities(self, task_lower: str) -> list:
        m = {"python":"python","js":"javascript","javascript":"javascript","sql":"database",
             "api":"api","docker":"docker","股票":"stock","财报":"financial","数据":"data",
             "投资":"investment","架构":"architecture","系统":"system","bug":"bug","error":"error"}
        return list(set(en for cn, en in m.items() if cn in task_lower)) or ["general"]

    def _estimate_complexity(self, task: str, task_lower: str) -> int:
        s = 3
        if len(task) > 50: s += 1
        if any(w in task for w in ["完整","全部","详细","comprehensive","full"]): s += 2
        if any(w in task for w in ["系统","架构","framework","platform"]): s += 2
        if any(w in task_lower for w in ["简单","simple","basic"]): s -= 1
        return max(1, min(10, s))

    def match(self, incoming: TaskTemplate) -> Optional[TaskTemplate]:
        """Find best matching template by type + weighted features"""
        candidates = [t for t in self.templates.values()
                     if t.template_type == incoming.template_type]
        if not candidates:
            return None

        scored = []
        for c in candidates:
            verb_overlap = len(set(incoming.verbs) & set(c.verbs))
            verb_score = MATCH_WEIGHTS["verbs"] * min(verb_overlap / max(len(incoming.verbs), 1), 1.0)

            entity_overlap = len(set(incoming.entity_types) & set(c.entity_types))
            entity_score = MATCH_WEIGHTS["entities"] * min(entity_overlap / max(len(incoming.entity_types), 1), 1.0)

            complexity_diff = abs(incoming.complexity - c.complexity)
            complexity_score = MATCH_WEIGHTS["complexity"] * max(0, 1 - complexity_diff / 10)

            conf = min(1.0, c.hit_count / 10) if c.hit_count > 0 else 0.5
            confidence_score = MATCH_WEIGHTS["confidence"] * conf

            total = verb_score + entity_score + complexity_score + confidence_score
            if total > 0.25:
                scored.append((total, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1] if scored else None

    def get_or_create(self, task: str) -> TaskTemplate:
        template = self.extract(task)
        if template is None:
            return None
        match = self.match(template)
        if match:
            return match
        self.templates[template.template_id] = template
        self._save()
        return template

    def get_stats(self) -> dict:
        total = len(self.templates)
        used = sum(1 for t in self.templates.values() if t.hit_count > 0)
        by_type = {}
        for t in self.templates.values():
            by_type[t.template_type] = by_type.get(t.template_type, 0) + 1
        total_hits = sum(t.hit_count for t in self.templates.values())
        return {"total": total, "used": used, "by_type": by_type, "total_hits": total_hits}
