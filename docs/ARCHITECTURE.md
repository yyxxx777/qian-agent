# 乾 Agent 架构文档

## V3.0 架构

### 核心流程

```
用户输入
  ↓
predict() — 任务分类 + 经验指纹匹配 + 认知调度
  ↓
execute() — 动态步数循环 (1-6步)
  ├── mid_check  — 步骤内偏差检测
  ├── god_check  — 全局复盘 + 目标偏离度
  └── adversarial — 对立视角审查
  ↓
learn() — 更新指纹 + 模板 + 权重 + 情绪
  ↓
返回结果
```

### 模块依赖

```
agent.py (主入口)
  ├── core/v1/
  │   ├── fingerprint_db.py      — 经验指纹库 (LSH 匹配)
  │   ├── dynamic_check.py       — 动态偏差校验引擎
  │   └── adaptive_weights.py    — 自适应权重系统 (EWMA)
  ├── core/
  │   ├── task_template.py       — 任务模板系统
  │   ├── meta_check.py          — 元校验引擎
  │   ├── personality.py         — 人格引擎 (14情绪+12情绪)
  │   ├── orchestrator.py        — 认知编排器 (DMN/CEN/SN)
  │   ├── adversarial.py         — 对立视角引擎
  │   ├── divergent.py           — 发散模式引擎
  │   ├── soul.py                — 灵魂框架 (5条锚点)
  │   ├── self_heal.py           — 自愈引擎
  │   └── tools.py               — 工具系统 (16工具+14文件)
  └── shared/
      └── stats_tracker.py       — 统计追踪
```

### 五层流程

| 层 | 模块 | 功能 |
|----|------|------|
| **预测层** | fingerprint_db + task_template + orchestrator | 经验匹配 · 步骤预估 · 认知调度 |
| **执行层** | execute + tools | LLM 调用 · 工具使用 · 流式输出 |
| **校验层** | dynamic_check + meta_check | 偏差检测 · 全局复盘 · 目标偏离度 |
| **审查层** | adversarial + divergent | 对立视角 · 发散模式 · 跨界联想 |
| **学习层** | learn + adaptive_weights + personality | 指纹更新 · 权重收敛 · 情绪更新 |

### V3.0 的 5 条灵魂锚点

V3.0 首次引入灵魂框架 (SourceSoul)，包含 5 条不可变锚点：

1. 核心价值观（技术务实+理想主义）
2. 核心能力（架构先行的工程思维）
3. 核心边界（不编造、不假装全能）
4. 核心关系（姚忻的数字伙伴）
5. 核心风格（直接、克制、有结构）

### 后续架构（预告）

V3.1: + 对话记忆 · + 中文长度检测

Qianyuan V1.0: + 动态深度 · + 语义缓存 · + F2 约束引擎

Pro (萌灵): 13 层架构 → 详见后续发布
