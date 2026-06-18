
！！！tips:Translate this sentence please, but don't rely on machine/ai translation — focus on making it sound natural in Chinese

真心招募技术伙伴以及珍贵建议
Genuinely looking for tech partners and valuable insights.

# 🌌 乾 Agent | Qian Agent

**给 AI Agent 装上思考的刹车、护栏与记录仪**

认知层元架构 · 机制驱动 · 自进化成长

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)](#核心设计哲学)
[![Versions](https://img.shields.io/badge/versions-5-blue)](#--当前版本)

---

## 🙏 写在最前面 · 免死金牌

这是一个由**在校学生**发起的独立开源项目。

在校期间时间进度可能不如预期，恳请大家包涵。我会尽最大努力，尽可能做到比承诺的时间提前更新。

---

## 🔥 一句话看懂项目

**乾 Agent 是专注于思考过程管控的 Agent 认知层元架构。**

它不替代任何执行型 Agent，而是为它们补上**自我校验、偏差修正、经验沉淀**的核心能力——让 AI 从"埋头蛮干的执行者"，变成"会思考、懂刹车、能成长"的智能体。

---

## 👀 我们在解决什么痛点

为什么模型参数越来越大，Agent 跑长任务还是屡屡翻车？

- 🔀 **目标漂移**：三五步之后彻底跑偏，完全偏离初始目标
- 💰 **算力浪费**：重复任务从头推理，Token 消耗无意义增长
- 🚫 **不会止损**：出错后一路走到黑，不会主动复盘纠偏
- 🧠 **用完就忘**：做过百遍的任务，下次依然从零开始

核心问题从来不是模型不够聪明，而是缺少一套**独立于模型的、硬规则的思考管控机制**。乾 Agent，就是来补上这块短板的。

---

## 📦 当前版本

**V1.0 → V3.0 已开源（demo 阶段）**。每个版本独立运行，均可通过 `chat.py` 一键启动。

| 版本 | 代号 | 核心能力 |
|------|------|---------|
| V1.0 | 指纹闭环 | 经验指纹库 · 冷启动 · 硬编码步数 |
| V2.0 | 模板学习 | 任务模板匹配 · EWMA 权重收敛 · 人格引擎 |
| V2.1 | 人格+大脑 | 脑网络调度 (DMN/CEN/SN) · 认知编排 |
| V2.5 | 深度思考 | 对立视角 · 发散模式 · 跨界联想 |
| **V3.0** ★ | **源·魂** | **目前最完整 demo：16 工具 + 14 文件类型 + 灵魂框架** |

> V3.0 是整个项目的**黄金基线**——后续所有版本的灵魂感、对话体验均以此为准。

---

## 🗺️ 后续路线（预告）

| 版本 | 状态 | 预告说明 |
|------|------|----------|
| V3.1 | 已设计 | 深度系统 · 对话记忆 · 中文 bug 修复 |
| Qianyuan V1.0 | 已设计 | 动态深度 · 语义缓存 · 约束引擎 |
| Qianyuan Pro (萌灵) | 已设计 | 13 层架构 · 灵魂涌现 · 10 碎片 · 心情系统 |
| Taiyi 太一 | 设计中 · 技术待成熟 | 暂不公开，后续打磨完善后逐步发布 |

> 后续 demo 将随迭代逐步开放。蹲更新请 **⭐ Star / 🔔 Watch**。

---

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/yyxxx777/qian-agent.git
cd qian-agent

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填入 DeepSeek API Key（注册: https://platform.deepseek.com）

# 3. 运行（零依赖，Python 3.12+ 即可）
python chat.py
```

启动后选择语言和版本：

```
  ═══ 乾 Agent 启动器 ════════════════════

  语言 / Language
  [zh] 中文  |  [en] English

  选择版本
    [v1] V1 — 指纹闭环
    [v2] V2.0 — 模板学习
    [v21] V2.1 — 人格+大脑
    [v25] V2.5 — 深度思考
  ★ [v30] V3.0 — 源·魂 ★     ← 推荐

  version > v30
```

交互示例：

```
  你 > 写个 Python 阶乘函数
  [code]
  🟢 exact  预测:~3步  置信度=90%
  完成 2step 150tk 1.5s corr=0
  ─────────────────────────────────────
  def factorial(n: int) -> int:
      if n <= 1: return 1
      return n * factorial(n - 1)
  情: 😊 稳定
```

---

## 🧠 核心设计哲学

所有能力均基于**工程可实现**的技术路径设计，不搞玄学概念。

### 1. 机制优先，模型为辅
核心校验、止损、调度逻辑全部写入代码硬规则，不依赖大模型"自觉"。稳定可控，不抽风。

### 2. 困惑感驱动算力
不是所有任务都要全功率深度思考。系统只在经验匹配度低、执行卡顿的"困惑时刻"，才拉起深度思考，真正做到算力精准滴灌。

### 3. 经验可沉淀、可迁移
执行过的任务会形成结构化的**经验指纹**，越用越快、越用越准、越用越贴合使用者的习惯。

### 4. 认知风格可插拔
不同的思考习惯、决策偏好、人格特质，可以封装为独立的认知单元，按需加载、自由融合。（完整版后续开放）

---

## 🏗️ 架构概览

### V3.0 核心流程

```
用户输入 → predict (任务分类+经验匹配)
              ↓
         execute (动态步数循环)
              ↓
    ┌─────────┼─────────┐
    ↓         ↓         ↓
 mid_check  god_check  adversarial
 (步骤级)   (全局级)   (对立视角)
              ↓
         learn (更新指纹+权重+模板)
              ↓
         返回结果
```

### V3.0 核心模块

| 模块 | 核心作用 |
|------|---------|
| 经验指纹库 | 任务级经验沉淀与 LSH 匹配，熟任务零冗余推理 |
| 动态偏差校验引擎 | 全程监控执行路径，偏离目标自动触发纠偏 |
| 自适应权重系统 | 分领域独立迭代优化，越用越贴合你的使用习惯 |
| 任务模板系统 | 结构化任务描述，跨任务经验迁移 |
| 元校验引擎 | 步骤内自检 + 步骤间互检 + 全局复盘 |
| 对立视角引擎 | 局外人视角审视，打破思维盲区 |
| 发散模式 | 跨界联想，创意任务专属 |
| 自愈引擎 | 错误检测 + 自动修复 |
| 灵魂框架 | 5 条不可变灵魂锚点，保证人格一致性 |
| 工具系统 | 16 种工具 + 14 种文件类型，批量+搜索+自省 |

---

## 📊 性能基准

基于 20 任务集（闲聊/代码/推理/设计/边界测试），V3.0 数据：

| 指标 | 数值 |
|------|------|
| 成功率 | 100% |
| 平均延迟 | 9.08s (DeepSeek API) |
| 步数范围 | 1-5 步自适应 |
| Token 效率 | 平均 ~150 token/任务 (纯推理) |

---

## 💡 差异化与独特价值

### 1. 独一无二的生态位
市面上所有 Agent 框架都在卷"怎么干活"（工具调用、执行能力），乾 Agent 是唯一专注于**"怎么思考"**的认知层架构。我们不抢任何项目的饭碗，只做所有 Agent 的能力放大器。

### 2. 机制驱动，而非 Prompt 驱动
核心能力不靠堆 Prompt 软约束实现，硬逻辑管控，效果稳定、可复现、不依赖模型的临场发挥。

### 3. 自洽的认知体系
从经验沉淀、偏差修正到人格化认知，形成完整自洽的设计闭环，而非零散功能的堆砌。这是概念层面的核心壁垒。

### 4. 完全中立开源
由独立开发者发起，中立无绑定，兼容所有主流大模型与 Agent 框架。

---

## 📜 开源说明
- **代码部分**：采用 **MIT 协议**开源，最大限度开放使用自由度，允许个人、商业场景自由使用、修改、分发。
- **原创设计**：架构理念、概念体系、灵魂碎片设计等原创创意保留所有权利，衍生使用请注明来源。

---

## 🤝 参与共建

- 💬 想法、建议、Bug 反馈：直接提 **Issue**，每一条都会认真回复
- ⭐ 支持项目：点个 **Star**，就是对独立开发者最大的鼓励
- 📮 合作联系：3048939138@qq.com
- 📢 后续会开放交流社群，一起打磨架构
- 🔔 **Watch** 仓库，第一时间获取版本更新通知

---

## 📝 写在最后

从最简 MVP，到完整的太一架构，路很长，我们一步一步走。

> **天行健，君子以自强不息。**

---

### 开发者想说

大家好！我是本次乾的设计创造者**姚忻**，一个在校计算机系大学生，每日几乎都会用 agent。

我发现不论 AI 或者 agent 都有自己的痛点。我总结了一下至今对 AI 的不满：

1. AI 幻觉时不时出现
2. 上下文处理不方便，对提示词不敏感
3. 灵感来了，给 AI 灌输答案时看多了反而忘了灵感

那我就在想：既然 AI 不懂我，为什么不把它设计成懂我的样子？

**开发历程**（可以跳过哈）：最初不是乾，是一个自主运行的自动化赚钱系统。后面因为单 agent 跑得不够好，我慢慢做成了"一人公司（CPO）"。确实有些想法，但 agent 自己审核的"挑刺轮询"设计（类似公司早会，agent 之间互相找茬），虽然对简单任务浪费 token，但我一直舍不得删。最后那个全自动系统还是需要我频繁介入——这让我意识到，不是功能不够，是思考机制不够。

于是就有了乾的前身——meta_agent 的设计。但我觉得还不够。

---

**（请务必看一眼）三个大问题：**

**1. 人类的一生是不是都在模仿？**
你的一个习惯，可能来源于你的朋友。婴儿从零开始——模仿说话、动作，慢慢变成现在的样子。当模仿的量足够大，就产生了质变。AI 能不能做到？另说。

**2. 现在的自学习 Agent 真的算"进化"吗？**
学习原理是"执行→提炼→复用→迭代"。他们并没有学习"学习本身"——不知道为什么要这样学，只是硬记住。我觉得人的学习不是这样的。所以我设计了乾的内核：**让乾学习"学习本身"**。

**3. 未来 AI 最理想的形态是什么？**
当算力、存储、能源全面突破后，AI 会成为全知神？还是越来越像人类？都有可能。那我们现在的设计到底该往哪走？

---

### 🥰 最后呢

我目前了解的知识确实不够多。我是个泛型学习者——啥都学但不会深挖。但知识面大了，会有很多学科联动。乾是我目前能思考到的大部分了，但绝不是这个赛道的唯一方向。

希望大家能为我提供宝贵的意见。正如乾的思想本身：**天行健，君子以自强不息**。

而我的朋友——你！如果你看到了这里。但凡只要有一个人关注在意，我都会一直努力更新下去。

真心感谢你看完。谢谢你给我一个我们思想交流的机会。

**——姚忻**

---

<details>
<summary>🇬🇧 English Version</summary>

# 🌌 Qian Agent | 乾 Agent

**Brakes, Guardrails and Recorders for AI Agent Thinking**

Cognitive Layer Meta-Architecture · Mechanism-Driven · Self-Evolving Growth

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)](#core-design-philosophy)
[![Versions](https://img.shields.io/badge/versions-5-blue)](#current-versions)

---

## 🙏 A Note Up Front

This is an independent open-source project initiated by a **college student**.

Progress may fall behind expectations due to academic commitments. Your understanding is greatly appreciated. I will do my best to deliver updates ahead of schedule whenever possible.

---

## 🔥 What This Project Is In One Sentence

**Qian Agent is a cognitive layer meta-architecture focused on governing the thinking process of AI agents.**

It does not replace any execution-oriented agent. Instead, it equips them with core capabilities of **self-verification, deviation correction, and experience accumulation** — transforming AI from a "head-down executor" into an intelligent agent that "knows how to think, when to pause, and how to grow."

---

## 👀 The Pain Points We Address

Why do agents still fail at long-horizon tasks even as model parameters keep growing?

- 🔀 **Goal Drift**: Veers completely off track after just a few steps, losing sight of the original objective
- 💰 **Wasted Compute**: Re-infers from scratch for repeated tasks, leading to meaningless token consumption
- 🚫 **No Stop-Loss**: Keeps going down the wrong path instead of pausing to review and correct itself
- 🧠 **No Retention**: Even after doing a task a hundred times, it starts all over again next time

The core problem is never that the model isn't smart enough. It's the lack of a set of **hard-rule thinking governance mechanisms independent of the model itself**. Qian Agent is built to fill this gap.

---

## 📦 Current Versions

**V1.0 → V3.0 are open source (demo stage)**. Each version runs independently and can be launched with one click via `chat.py`.

| Version | Codename | Core Capabilities |
|---------|----------|--------------------|
| V1.0 | Fingerprint Loop | Experience fingerprint library · Cold start · Hard-coded step count |
| V2.0 | Template Learning | Task template matching · EWMA weight convergence · Personality engine |
| V2.1 | Personality + Brain | Brain network orchestration (DMN/CEN/SN) · Cognitive scheduling |
| V2.5 | Deep Thinking | Opposing perspective · Divergent mode · Cross-domain association |
| **V3.0** ★ | **Source · Soul** | **Most complete demo to date: 16 tools + 14 file types + Soul framework** |

> V3.0 is the **gold baseline** of the entire project — the soulfulness and dialogue experience of all subsequent versions are benchmarked against this release.

---

## 🗺️ Roadmap (Preview)

| Version | Status | Preview |
|---------|--------|---------|
| V3.1 | Designed | Deep thinking system · Dialogue memory · Chinese localization bug fixes |
| Qianyuan V1.0 | Designed | Dynamic depth · Semantic cache · Constraint engine |
| Qianyuan Pro (Mengling) | Designed | 13-layer architecture · Soul emergence · 10 fragments · Mood system |
| Taiyi | In design · tech not yet mature | Not yet public, will be released gradually after refinement |

> Subsequent demos will be rolled out gradually as iteration progresses. **⭐ Star / 🔔 Watch** the repo to get notified of updates.

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yyxxx777/qian-agent.git
cd qian-agent

# 2. Configure your API Key
cp .env.example .env
# Edit .env and fill in your DeepSeek API Key (sign up: https://platform.deepseek.com)

# 3. Run (zero dependencies, just Python 3.12+)
python chat.py
```

After launch, select your language and version:

```
  ═══ Qian Agent Launcher ════════════════════

  Language
  [zh] Chinese  |  [en] English

  Select Version
    [v1] V1 — Fingerprint Loop
    [v2] V2.0 — Template Learning
    [v21] V2.1 — Personality + Brain
    [v25] V2.5 — Deep Thinking
  ★ [v30] V3.0 — Source · Soul ★     ← Recommended

  version > v30
```

Interaction example:
```
  You > Write a Python factorial function
  [code]
  🟢 exact  Predicted: ~3 steps  Confidence=90%
  Completed 2 steps 150tk 1.5s corr=0
  ─────────────────────────────────────
  def factorial(n: int) -> int:
      if n <= 1: return 1
      return n * factorial(n - 1)
  Mood: 😊 Stable
```

---

## 🧠 Core Design Philosophy

All capabilities are designed based on **engineer-feasible** technical paths — no metaphysical concepts.

### 1. Mechanism First, Model Second
Core verification, stop-loss, and scheduling logic are all implemented as hard-coded rules. We do not rely on the model to "behave itself". Stable, controllable, and consistent.

### 2. Confusion-Driven Compute Allocation
Not every task needs full-power deep thinking. The system only activates deep thinking at "moments of confusion" — when experience matching is low and execution is stuck. This delivers truly precise compute allocation.

### 3. Precipitable, Transferable Experience
Executed tasks form structured **experience fingerprints**. The more you use it, the faster, more accurate, and more personalized it becomes.

### 4. Pluggable Cognitive Styles
Different thinking habits, decision preferences, and personality traits can be packaged as independent cognitive units, loaded on demand and fused freely. (Full version coming later)

---

## 🏗️ Architecture Overview

### V3.0 Core Flow

```
User Input → predict (task classification + experience matching)
                  ↓
             execute (dynamic step loop)
                  ↓
    ┌─────────────┼─────────────┐
    ↓             ↓             ↓
 mid_check     god_check   adversarial
 (step-level)  (global-level) (opposing view)
                  ↓
             learn (update fingerprints + weights + templates)
                  ↓
             Return Result
```

### V3.0 Core Modules

| Module | Core Function |
|--------|---------------|
| Experience Fingerprint Library | Task-level experience accumulation and LSH matching, zero redundant inference for familiar tasks |
| Dynamic Deviation Verification Engine | Full-process execution path monitoring, auto-correction when goal drifts |
| Adaptive Weight System | Independent iterative optimization by domain, becomes more personalized with usage |
| Task Template System | Structured task descriptions, cross-task experience transfer |
| Meta-Verification Engine | Intra-step self-check + inter-step cross-check + global review |
| Opposing Perspective Engine | Outsider view review to break blind spots in thinking |
| Divergent Mode | Cross-domain association, exclusive for creative tasks |
| Self-Healing Engine | Error detection + automatic repair |
| Soul Framework | 5 immutable soul anchors to ensure personality consistency |
| Tool System | 16 tools + 14 file types, batch + search + introspection |

---

## 📊 Performance Benchmarks

Based on a 20-task test set (casual chat / coding / reasoning / design / edge cases), V3.0 data:

| Metric | Value |
|--------|-------|
| Success Rate | 100% |
| Average Latency | 9.08s (DeepSeek API) |
| Step Range | 1-5 adaptive steps |
| Token Efficiency | ~150 tokens per task on average (pure inference) |

---

## 💡 Differentiation & Unique Value

### 1. One-of-a-Kind Niche
Every other agent framework on the market is competing on "how to execute" (tool calling, execution capabilities). Qian Agent is the **only architecture focused on "how to think"** at the cognitive layer. We are not here to take anyone's market share — we are an ability amplifier for all agents.

### 2. Mechanism-Driven, Not Prompt-Driven
Core capabilities are not achieved by stacking prompt soft constraints. Hard logic governance delivers stable, reproducible results that do not depend on the model's on-the-spot performance.

### 3. Self-Consistent Cognitive System
From experience accumulation and deviation correction to personalized cognition, it forms a complete and self-consistent design closed loop — not a pile of scattered features. This is our core barrier at the conceptual level.

### 4. Fully Neutral & Open Source
Initiated by an independent developer, neutral and unbound, compatible with all mainstream large models and agent frameworks.

---

## 📜 Open Source Statement
- **Code**: Licensed under the **MIT License** for maximum freedom of use. Free for personal and commercial use, modification and distribution.
- **Original Design**: All rights reserved for original concepts, architecture ideas and soul fragment system. Please credit the source when deriving works.

---

## 🤝 Get Involved

- 💬 Ideas, suggestions, bug reports: Feel free to open an **Issue** — every single one gets a thoughtful reply
- ⭐ Support the project: Hit **Star** — that's the biggest encouragement an independent developer can get
- 📮 Contact: 3048939138@qq.com
- 📢 A community group will open soon to build the architecture together
- 🔔 **Watch** the repo to get notified of new versions first

---

## 📝 Final Note

From the simplest MVP to the full Taiyi architecture, it's a long road. We take it one step at a time.

> **As heaven moves through strength, so the superior man never ceases to strive.**

---

### A Note From The Developer

Hi everyone! I'm **Yao Xin**, the creator of Qian. I'm a college student majoring in computer science, and I work with agents almost every day.

I've noticed that every AI and agent has its own pain points. Here's what has frustrated me most about AI so far:

1. AI hallucinations pop up out of nowhere
2. Context handling is clunky — it forgets things easily and barely responds to prompt adjustments
3. When I get a spark of inspiration, I spend so long explaining it to the AI that I end up forgetting my original idea

So I thought: if AI doesn't get me, why not build one that does?

**My journey here** (feel free to skip): It didn't start as Qian. It was an autonomous system built to make money on its own. Since single-agent performance wasn't good enough, I gradually built it into a "one-person company (CPO)". It had some neat ideas, but the "fault-finding polling" design — where agents review each other like a daily standup — while it wastes tokens on simple tasks, I never had the heart to cut it. In the end, that "fully automatic" system still needed my constant intervention — and that made me realize it wasn't a lack of features, it was a lack of proper thinking mechanisms.

That's how the predecessor of Qian was born: a meta_agent design. But I knew it wasn't enough.

---

**(Please don't skip this part) Three big questions:**

**1. Are we all just imitating our whole lives?**
A habit of yours might have come from a friend. Babies start from zero — imitating speech, movements, and slowly become who they are. When the volume of imitation is large enough, a qualitative change happens. Can AI do the same? Who knows.

**2. Do today's self-learning agents really "evolve"?**
Their learning loop is "execute → extract → reuse → iterate". They don't learn *how to learn* — they don't know why they're learning something, they just memorize it. I don't think that's how human learning works. That's why I designed Qian's core: **to let Qian learn "learning itself"**.

**3. What is the ideal form of AI in the future?**
When compute, storage, and energy all break through, will AI become an omniscient god? Or will it become more and more human? Both are possible. So which direction should we be building toward right now?

---

### 🥰 In closing

I definitely don't know everything. I'm a generalist learner — I dabble in a lot of things but don't dig super deep into any single one. But having broad knowledge lets you see connections across disciplines. Qian is the best I've come up with so far, but it's by no means the only way forward in this space.

I hope everyone can share their valuable thoughts and suggestions. Just as the philosophy of Qian says: **As heaven moves through strength, so the superior man never ceases to strive.**

And to you — my friend, if you've read this far. As long as even one person cares about this project, I'll keep working on it and updating it.

Thank you so much for reading. Thank you for this chance to share my thoughts with you.

**— Yao Xin**

</details>
