# 🌌 乾 Agent | Qian Agent（language:zh/en）(zh)

tips:Translate this sentence please, but don't rely on machine/ai translation — focus on making it sound natural in Chinese

真心招募技术伙伴以及珍贵建议
Genuinely looking for tech partners and valuable insights.




> **给 AI Agent 装上思考的刹车、护栏与记录仪**
>
> 认知层元架构 · 机制驱动 · 自进化成长

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

| 版本 | 状态 | 预告 |
|------|------|------|
| V3.1 | 已设计 | 深度系统 · 对话记忆 · 中文 bug 修复 |
| Qianyuan V1.0 | 已设计 | 动态深度 · 语义缓存 · 约束引擎 |
| Qianyuan Pro (萌灵) | 已设计 | 13 层架构 · 灵魂涌现 · 10 碎片 · 心情系统 |
|tai yi （太一）| 已设计（技术层不够）||暂不公开（后续有效果和意见打磨再公开）||

> 后续 demo 将随迭代逐步开放。蹲更新请 **⭐ Star / 🔔 Watch**。

---

## 🚀 快速开始

```bash
# 1. 克隆
git clone https://github.com/YOUR_USER/qian-agent.git
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

## 🤝 参与共建

- 💬 想法、建议、Bug 反馈：直接提 **Issue**，每一条都会认真回复
- ⭐ 支持项目：点个 **Star**，就是对独立开发者最大的鼓励
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


## 🇬🇧 English Version

### 🌌 Qian Agent

**Brakes, guardrails, and recorders for AI Agent thinking.**

Qian Agent is a cognitive layer meta-architecture focused on thinking process control. It does not replace any execution Agent — instead, it adds core capabilities of **self-verification, deviation correction, and experience accumulation**.

### Current Status

**V1.0 → V3.0 released as open source demos.** V3.0 is the most complete demo to date.

### Pain Points We Solve

- 🔀 **Goal Drift** — Deviating from the original goal after a few steps
- 💰 **Wasted Compute** — Re-inferring from scratch for repeated tasks
- 🚫 **No Stop-Loss** — Never actively reviews or corrects mistakes
- 🧠 **No Memory** — After doing a task 100 times, still starts from zero

### Core Design Philosophy

1. **Mechanism First, Model Second** — Hard-coded rules, not prompt soft constraints
2. **Confusion-Driven Computing** — Deep thinking only activates at "confused moments"
3. **Precipitable Experience** — Structured experience fingerprints, faster and more accurate with use
4. **Pluggable Cognitive Styles** — Personality units can be loaded, fused, and switched on demand

### Quick Start

```bash
git clone https://github.com/YOUR_USER/qian-agent.git
cd qian-agent
cp .env.example .env  # Add your DeepSeek API key
python chat.py
```

### Roadmap (Preview)

V3.1, Qianyuan V1.0, and Pro (13-layer architecture with soul emergence, mood system, and 10 personality fragments) are designed and will be released as demos in future iterations. **Star ⭐ / Watch 🔔 to stay updated.**

---

**As heaven moves through strength, so the superior man never ceases to strive.**
