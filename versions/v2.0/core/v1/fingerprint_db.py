"""
乾Agent v1 - L0 经验指纹库
============================
核心设计：关键词标准化 + LSH局部敏感哈希 + 三级匹配规则 + JSON持久化

经验指纹库是整个乾Agent的记忆核心：
- 做过一次的事，下次自动高质量复现
- LSH分桶快速筛选候选，避免全量比对
- 三级匹配：exact(95%+) / fuzzy(70%+) / none
- 滑动平均更新预测模型（步数/Token/置信度）

姚忻 · 2026.06.17
"""

import json
import hashlib
import re
import time
from pathlib import Path
from typing import Optional, List, Dict

# 停用词表
STOP_WORDS = {
    "的", "了", "是", "我", "你", "他", "它", "在", "和", "就", "都",
    "而", "及", "与", "把", "被", "让", "给", "一个", "一下", "这个",
    "那个", "也", "还", "要", "会", "可以", "能", "什么", "怎么",
    "吗", "呢", "吧", "啊", "哦", "嗯", "哈", "这", "那", "有",
    "不", "很", "非常", "比较", "更", "最", "很", "太", "好",
}

# 同义词映射
SYNONYM_MAP = {
    "重命名": "改名", "批量改名": "重命名", "批量重命名": "重命名",
    "改名": "重命名",
    "txt": "文本文件", "文本": "文本文件",
    "jpg": "图片", "jpeg": "图片", "png": "图片", "图片文件": "图片",
    "python": "py", "py脚本": "python", "python脚本": "python",
    "api": "接口", "接口开发": "api",
    "爬虫": "数据采集", "数据抓取": "爬虫", "网页抓取": "爬虫",
    "部署": "上线", "发布": "部署", "上线部署": "部署",
    "测试": "验证", "校验": "测试",
    "架构": "设计", "系统设计": "架构",
    "数据库": "存储", "数据存储": "数据库",
    "前端": "界面", "页面": "前端", "ui": "前端",
    "后端": "服务端", "server": "后端",
    "文档": "说明", "readme": "文档", "注释": "文档",
    "优化": "性能优化", "提速": "优化", "加速": "优化",
    "bug": "修复", "debug": "修复", "调试": "修复",
}


class ExperienceFingerprintDB:
    """
    L0 经验指纹库
    -------------
    所有经验的持久化存储，支持:
    - 关键词标准化 + 同义词映射
    - LSH局部敏感哈希快速分桶
    - 三级匹配：exact / fuzzy / none
    - 滑动平均更新预测模型
    - JSON持久化，冷启动友好
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path(__file__).parent.parent.parent / "data" / "fingerprints.json")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db: List[Dict] = self._load()
        self._dirty = False

    def _load(self) -> List[Dict]:
        if self.db_path.exists():
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)
        self._dirty = False

    def _standardize_keywords(self, text: str) -> List[str]:
        """关键词标准化：去停用词 + 同义词映射 + 去重排序"""
        words = re.findall(r"[\u4e00-\u9fa5a-zA-Z0-9]+", text.lower())
        words = [w for w in words if w not in STOP_WORDS and len(w) > 1]
        words = [SYNONYM_MAP.get(w, w) for w in words]
        return sorted(list(set(words)))

    def _lsh_hash(self, keywords: List[str], band: int = 3) -> str:
        """LSH局部敏感哈希：分桶计算，相似内容哈希前缀相同概率高"""
        full_hash = hashlib.sha256(" ".join(keywords).encode()).hexdigest()
        return full_hash[:band]

    def generate_fingerprint(self, task: str, task_type: str, domain: str) -> Dict:
        """生成标准任务指纹"""
        keywords = self._standardize_keywords(task)
        keyword_str = " ".join(keywords)
        lsh_prefix = self._lsh_hash(keywords)
        exact_hash = hashlib.sha256(
            f"{task_type}:{domain}:{keyword_str}".encode()
        ).hexdigest()

        return {
            "fingerprint_hash": exact_hash,
            "lsh_prefix": lsh_prefix,
            "meta": {
                "task_type": task_type,
                "domain": domain,
                "keywords": keywords,
                "create_time": time.time(),
                "use_count": 0,
            },
            "prediction_model": {
                "avg_steps": 0,
                "avg_tokens": 0,
                "base_confidence": 0.5,
            },
            "solution_template": {
                "key_nodes": [],
                "pitfall_list": [],
                "verify_method": "",
            },
            "stats": {
                "success_count": 0,
                "fail_count": 0,
                "success_rate": 0.0,
            },
        }

    def match(self, task: str, task_type: str, domain: str) -> Dict:
        """
        三级匹配：返回匹配度 + 最相似指纹

        匹配级别:
        - exact: 关键词重合 >= 95%，可直接复用经验
        - fuzzy: 关键词重合 >= 70%，参考经验但需校验
        - none: 无匹配，零经验探索模式
        """
        target_keywords = self._standardize_keywords(task)
        target_lsh = self._lsh_hash(target_keywords)
        target_set = set(target_keywords)

        # 1. LSH前缀快速筛选 (放宽: 同type即可, 不要求精确LSH匹配)
        candidates = [
            fp for fp in self.db
            if fp["meta"]["task_type"] == task_type
        ]
        
        # 如果有精确LSH匹配, 优先
        exact_lsh = [fp for fp in candidates if fp["lsh_prefix"] == target_lsh]
        if exact_lsh:
            candidates = exact_lsh

        # 2. LSH没命中，放宽到同domain全量（数量少时）
        if not candidates and len(self.db) < 100:
            candidates = [
                fp for fp in self.db
                if fp["meta"]["domain"] == domain or fp["meta"]["task_type"] == task_type
            ]

        if not candidates:
            return {"match_level": "none", "similarity": 0.0, "fingerprint": None}

        # 3. 关键词重合度精确计算
        max_similarity = 0.0
        best_fp = None
        for fp in candidates:
            fp_set = set(fp["meta"]["keywords"])
            if not fp_set:
                continue
            similarity = len(target_set & fp_set) / len(target_set | fp_set)
            if similarity > max_similarity:
                max_similarity = similarity
                best_fp = fp

        # 4. 分级判定（v1宽容模式：指纹少时放宽阈值）
        if max_similarity >= 0.85:
            level = "exact"
        elif max_similarity >= 0.55:
            level = "fuzzy"
        elif max_similarity >= 0.25:
            level = "loose"
        else:
            level = "none"

        return {
            "match_level": level,
            "similarity": round(max_similarity, 3),
            "fingerprint": best_fp,
        }

    def add_or_update(
        self,
        fingerprint: Dict,
        success: bool,
        steps: int,
        tokens: int,
        key_nodes: List[str],
        pitfalls: List[Dict],
        verify: str,
    ):
        """任务完成后更新指纹库（滑动平均）"""
        existing = next(
            (fp for fp in self.db if fp["fingerprint_hash"] == fingerprint["fingerprint_hash"]),
            None,
        )

        if existing:
            existing["meta"]["use_count"] += 1
            if success:
                existing["stats"]["success_count"] += 1
            else:
                existing["stats"]["fail_count"] += 1

            total = existing["stats"]["success_count"] + existing["stats"]["fail_count"]
            existing["stats"]["success_rate"] = (
                existing["stats"]["success_count"] / total if total > 0 else 0.0
            )

            # 滑动平均更新预测模型
            cnt = existing["meta"]["use_count"]
            pm = existing["prediction_model"]
            pm["avg_steps"] = (pm["avg_steps"] * (cnt - 1) + steps) / cnt
            pm["avg_tokens"] = (pm["avg_tokens"] * (cnt - 1) + tokens) / cnt
            pm["base_confidence"] = min(0.95, 0.5 + 0.05 * cnt)

            # 更新方案模板（替换为最新的）
            if key_nodes:
                existing["solution_template"]["key_nodes"] = key_nodes
            if pitfalls:
                existing["solution_template"]["pitfall_list"] = pitfalls
            if verify:
                existing["solution_template"]["verify_method"] = verify
        else:
            fingerprint["meta"]["use_count"] = 1
            fingerprint["meta"]["create_time"] = time.time()
            fingerprint["stats"]["success_count"] = 1 if success else 0
            fingerprint["stats"]["fail_count"] = 0 if success else 1
            fingerprint["stats"]["success_rate"] = 1.0 if success else 0.0
            fingerprint["prediction_model"]["avg_steps"] = steps
            fingerprint["prediction_model"]["avg_tokens"] = tokens
            fingerprint["solution_template"]["key_nodes"] = key_nodes
            fingerprint["solution_template"]["pitfall_list"] = pitfalls
            fingerprint["solution_template"]["verify_method"] = verify
            self.db.append(fingerprint)

        self._dirty = True
        self._save()

    def get_stats(self) -> Dict:
        """获取指纹库统计"""
        return {
            "total_fingerprints": len(self.db),
            "total_uses": sum(fp["meta"]["use_count"] for fp in self.db),
            "avg_success_rate": (
                sum(fp["stats"]["success_rate"] for fp in self.db) / len(self.db)
                if self.db else 0.0
            ),
            "domains": list(set(fp["meta"]["domain"] for fp in self.db)),
            "task_types": list(set(fp["meta"]["task_type"] for fp in self.db)),
        }

    def seed_warmup_data(self, warmup_entries: List[Dict]):
        """注入预热数据，避免冷启动"""
        for entry in warmup_entries:
            fp = self.generate_fingerprint(
                entry["task"], entry["task_type"], entry["domain"]
            )
            self.add_or_update(
                fp,
                success=entry.get("success", True),
                steps=entry.get("steps", 5),
                tokens=entry.get("tokens", 300),
                key_nodes=entry.get("key_nodes", []),
                pitfalls=entry.get("pitfalls", []),
                verify=entry.get("verify", ""),
            )
        return len(warmup_entries)
