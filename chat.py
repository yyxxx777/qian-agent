#!/usr/bin/env python3
"""
乾 Agent — Version Selector + Interactive Chat
================================================
pick version + language, then talk to Qian.

usage: python chat.py [--v1|--v2|--v21|--v25|--v30|--v31] [--en|--zh] [--data]
"""

import sys, os, json, time, re

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ═════════════════════════════════════════
# Colors
# ═════════════════════════════════════════
C = {"r": "\033[0m", "b": "\033[1m", "d": "\033[2m",
     "g": "\033[92m", "y": "\033[93m", "R": "\033[91m",
     "c": "\033[96m", "m": "\033[95m", "w": "\033[97m"}
def c(t, s): return f"{C.get(t,'')}{s}{C['r']}"

# ═════════════════════════════════════════
# Version aliases — O(1) dict, zero cost
# ═════════════════════════════════════════
V_ALIAS = {
    "1": "v1", "v1": "v1",
    "2": "v2", "v2": "v2", "2.0": "v2", "v2.0": "v2", "v20": "v2", "20": "v2",
    "21": "v21", "v21": "v21", "2.1": "v21", "v2.1": "v21",
    "25": "v25", "v25": "v25", "2.5": "v25", "v2.5": "v25",
    "3": "v30", "30": "v30", "v30": "v30", "3.0": "v30", "v3.0": "v30",
    "31": "v31", "v31": "v31", "3.1": "v31", "v3.1": "v31",
    "qy": "qy", "": "qy",  # default
}

VERSIONS = {
    "v1":  {"name_zh": "V1 — 指纹闭环",           "name_en": "V1 — fingerprint loop",
            "desc_zh": "实例指纹仅匹配 · 冷启动 · 硬编码步数",
            "desc_en": "instance fingerprint · cold start · hard-coded steps",
            "path": "versions/v1"},
    "v2":  {"name_zh": "V2.0 — 模板学习",         "name_en": "V2.0 — template learning",
            "desc_zh": "模板匹配 · 跨任务迁移 · EWMA收敛",
            "desc_en": "template matching · cross-task transfer · EWMA",
            "path": "versions/v2.0"},
    "v21": {"name_zh": "V2.1 — 人格+大脑",        "name_en": "V2.1 — personality + brain",
            "desc_zh": "人格引擎 · 脑网络调度 · 情绪+DMN/CEN/SN",
            "desc_en": "personality engine · brain orchestrator · DMN/CEN/SN",
            "path": "versions/v2.1"},
    "v25": {"name_zh": "V2.5 — 深度思考",         "name_en": "V2.5 — deep thinking",
            "desc_zh": "对立视角审查 · 发散模式 · 跨界刺激",
            "desc_en": "adversarial check · divergent mode · cross-stimulus",
            "path": "versions/v2.5"},
    "v30": {"name_zh": "V3.0 — 源·魂",            "name_en": "V3.0 — source soul",
            "desc_zh": "源·魂框架 · 手脚层增强 · 16工具+14文件类型",
            "desc_en": "source soul · enhanced tools · 16 tools + 14 types",
            "path": "versions/v3.0"},
    "v31": {"name_zh": "V3.1 — 深度系统 ★",       "name_en": "V3.1 — deep systems",
            "desc_zh": "P0学习强度+P1局外人+P2坑推演+知识图谱+性能优化",
            "desc_en": "learning intensity + outsider + pitfalls + KG + perf",
            "path": "versions/v3.1"},
    "qy":  {"name_zh": "Qianyuan V1.0", "name_en": "QianYuan V1.0",
            "desc_zh": "+dynamicDepth+cache+constraint+compress",
            "desc_en": "mechanism-driven · dynamic depth · cache · constraints",
            "path": "versions/qianyuan_v1"},
}

# ═════════════════════════════════════════
# Display Mode
# ═════════════════════════════════════════
DATA_MODE = False

def mood_detail(pers: dict) -> str:
    if not pers: return ""
    primary = pers.get("mood", "neutral")
    emoji = pers.get("mood_emoji", "😐")
    desc = pers.get("mood_desc", "")
    label = f"{emoji} {desc}" if desc else f"{emoji} {primary}"
    if DATA_MODE:
        e = pers.get("excitement", 0); cf = pers.get("confidence", 0)
        u = pers.get("urgency", 0); s = pers.get("satisfaction", 0)
        label += f" e={e:.1f} c={cf:.1f} u={u:.1f} s={s:.1f}"
    secondary = pers.get("secondary", [])
    if secondary:
        label += c("d", " +" + " +".join(f"{s['emoji']}{s['name']}" for s in secondary))
    return label

# ═════════════════════════════════════════
# I18N — all UI text in both languages
# ═════════════════════════════════════════
LANG = "zh"
T = {}

T_ZH = {
    "banner": "乾 Agent 启动器",
    "select_lang": "语言 / Language",
    "lang_zh": "[zh] 中文",
    "lang_en": "[en] English",
    "hint_lang": "输入 zh 或 en (默认: zh)",
    "select_ver": "选择版本",
    "hint_ver": "输入版本号, 如 31 / 3.1 / v3.1 (默认: v3.1)",
    "retry_lang": "无效输入, 请输入 zh 或 en",
    "retry_ver": "未知版本, 请重新输入",
    "retry_ver_hint": "可选: 1 / 2 / 21 / 25 / 30 / 31",
    "api_ok": "DeepSeek API 已连接",
    "api_no": "未找到 API Key · 模拟模式",
    "api_help": "设置: export DEEPSEEK_API_KEY=sk-xxx 或创建 .env",
    "commands": "/status /soul /history /quit  |  直接输入任务",
    "data_on": "数据模式",
    "data_off": "简洁模式",
    "data_toggle": "/data 切换显示模式",
    "you": "你",
    "bye": "乾已退出",
    "done": "完成",
    "pred": "预测",
    "pitfalls": "坑点",
    "corr": "修正",
    "step": "步",
    "tk": "词",
    "conf": "置信度",
    "cold": "新领域 · 执行后自动学习",
    "learn": "学习",
    "thinking": "思考中...",
    "checks": "校验",
    "adversarial": "对立审查",
    "soul_no": "此版本无灵魂模块",
}
T_EN = {
    "banner": "Qian Agent Launcher",
    "select_lang": "Language",
    "lang_zh": "[zh] Chinese",
    "lang_en": "[en] English",
    "hint_lang": "type zh or en (default: zh)",
    "select_ver": "Select Version",
    "hint_ver": "type version, e.g. 31 / 3.1 / v3.1 (default: v3.1)",
    "retry_lang": "Invalid input, please type zh or en",
    "retry_ver": "Unknown version, please retry",
    "retry_ver_hint": "options: 1 / 2 / 21 / 25 / 30 / 31",
    "api_ok": "DeepSeek API connected",
    "api_no": "No API Key · simulate mode",
    "api_help": "set DEEPSEEK_API_KEY or create .env",
    "commands": "/status /soul /history /quit  |  type your task",
    "data_on": "data mode",
    "data_off": "simple mode",
    "data_toggle": "/data toggles display mode",
    "you": "you",
    "bye": "Qian exited",
    "done": "done",
    "pred": "pred",
    "pitfalls": "pitfalls",
    "corr": "corr",
    "step": "st",
    "tk": "tk",
    "conf": "conf",
    "cold": "new domain · will learn after execution",
    "learn": "learn",
    "thinking": "thinking...",
    "checks": "checks",
    "adversarial": "adversarial",
    "soul_no": "no soul module in this version",
}

def t(key): return T.get(key, key)

# ═════════════════════════════════════════
# API Key
# ═════════════════════════════════════════
def auto_api_key():
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if key: return key
    paths = [".env", os.path.expanduser("~/.qian/.env"), os.path.expanduser("~/qian.env")]
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(3):
        paths.append(os.path.join(d, ".env"))
        d = os.path.dirname(d)
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"): continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip().strip('"').strip("'")
                        v = v.strip().strip('"').strip("'")
                        if "DEEPSEEK_API_KEY" in k: return v
        except: pass
    return ""

API_KEY = auto_api_key()

import urllib.request
def call_llm(prompt, max_tokens=None, temperature=None, max_tok=None, temp=None, **_):
    tok = max_tokens or max_tok or 1024
    tmp = temperature if temperature is not None else (temp if temp is not None else 0.7)
    if not API_KEY: return f"[simulate] {prompt[:50]}..."
    payload = json.dumps({"model":"deepseek-v4-flash","messages":[{"role":"user","content":prompt}],
        "max_tokens":tok,"temperature":tmp}).encode()
    req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions",
        data=payload, headers={"Content-Type":"application/json","Authorization":f"Bearer {API_KEY}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"].strip()

# ═════════════════════════════════════════
# Selection with retry
# ═════════════════════════════════════════
def select_all():
    global LANG, T
    MAX_RETRY = 3

    # Initialize with default language for banner display
    T = T_ZH
    LANG = "zh"

    print()
    print(f"  {c('b','══')} {c('c',t('banner'))} {c('b','═'*42)}")

    # ── Language (with retry) ──
    print(f"\n  {c('b',t('select_lang'))}")
    print(f"  {c('d',t('lang_zh'))}")
    print(f"  {c('d',t('lang_en'))}")
    print(f"  {c('d',t('hint_lang'))}")

    for attempt in range(MAX_RETRY):
        try:
            raw = input(f"  {c('c','lang')} > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None, None
        if raw in ("en", "english", "e"):
            LANG = "en"; break
        elif raw in ("zh", "chinese", "c", "中文", ""):
            LANG = "zh"; break
        else:
            if attempt < MAX_RETRY - 1:
                print(f"  {c('R',t('retry_lang'))}")
            else:
                LANG = "zh"  # default after max retries
    T = T_EN if LANG == "en" else T_ZH

    # ── Version (with retry) ──
    print(f"\n  {c('b',t('select_ver'))}")
    star_ver = "qy"
    for k, v in VERSIONS.items():
        tag = c('g','★') if k == star_ver else " "
        n = v["name_zh"] if LANG == "zh" else v["name_en"]
        d = v["desc_zh"] if LANG == "zh" else v["desc_en"]
        print(f"  {tag} [{k}] {c('c',n)}")
        print(f"      {c('d',d)}")
        print()
    print(f"  {c('d',t('hint_ver'))}")

    for attempt in range(MAX_RETRY):
        try:
            raw = input(f"  {c('c','version')} > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None, None
        # Normalize: strip 'v' prefix, keep only the alias key
        cleaned = raw.lstrip("v")
        ver = V_ALIAS.get(cleaned)
        if ver and ver in VERSIONS:
            return ver, LANG
        if attempt < MAX_RETRY - 1:
            print(f"  {c('R',t('retry_ver'))} ({t('retry_ver_hint')})")

    # Default after max retries
    ver = V_ALIAS[""]
    print(f"  {c('y','→')} {c('d',f'默认使用 {ver}')}")
    return ver, LANG


def guess_type(task):
    """任务分类 — UI层路由逻辑, 不包含引擎逻辑"""
    t_text = task.lower().strip()
    # 短文本/疑问句 → 聊天
    if len(t_text) < 15 or t_text.endswith("?") or t_text.endswith("？") or \
       t_text.endswith("吗") or t_text.endswith("呢") or t_text.endswith("吧"):
        return ("chat", "general")
    # 代码类
    if any(w in t_text for w in ["code","script","def ","class","function",
                                  "bug","fix","爬","写代码","实现","编程","脚本"]):
        return ("code", "general")
    # 分析类
    if any(w in t_text for w in ["analyze","analysis","stock","投资","股票",
                                  "trend","report","分析数据","分析","报告"]):
        return ("analysis", "general")
    # 设计类
    if any(w in t_text for w in ["design","architecture","system","方案","设计","架构"]):
        return ("design", "general")
    # 兜底聊天
    return ("chat", "general")


def print_header(ver_id, agent):
    v = VERSIONS[ver_id]
    name = v["name_zh"] if LANG == "zh" else v["name_en"]
    print()
    print(f"  {c('b','╔' + '═'*58 + '╗')}")
    print(f"  {c('b','║')}  {c('c','乾 Qian')} {c('b','—')} {c('g',name)}   {c('b','║')}")
    fp = agent.fp_db.get_stats()
    nfp = fp.get('total_fingerprints', fp.get('total', 0))
    sr = fp.get('avg_success_rate', fp.get('success_rate', 0))
    info = f"  {nfp} fingerprints  |  {sr*100:.0f}% success"
    print(f"  {c('b','║')}  {c('d',info)}  {c('b','║')}")
    if hasattr(agent, 'template_db'):
        ts = agent.template_db.get_stats()
        tt = ts['total']; th = ts['total_hits']
        print(f"  {c('b','║')}  {c('d',f'{tt} templates  |  {th} hits')}  {c('b','║')}")
    if hasattr(agent, 'personality'):
        md = mood_detail(agent.personality.snapshot())
        if md:
            print(f"  {c('b','║')}  {md}  {c('b','║')}")
    if hasattr(agent, 'soul'):
        ss = agent.soul.snapshot()
        ess = ss.get('essence', '')
        mil = ss.get('milestones', 0)
        print(f"  {c('b','║')}  {c('m','魂')} {c('d',ess)}  |  {c('d',f'里程碑: {mil}')}  {c('b','║')}")
    print(f"  {c('b','╚' + '═'*58 + '╝')}")
    print()


def run_chat(ver_id):
    global T, DATA_MODE
    path = VERSIONS[ver_id]["path"]
    base = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(base, path))

    if ver_id == "v1":
        from agent import QianAgentV1 as Agent
    else:
        from agent import QianAgent as Agent

    agent = Agent()
    print_header(ver_id, agent)

    # API status
    if API_KEY:
        print(f"  {c('g','●')} {t('api_ok')}")
    else:
        print(f"  {c('R','○')} {t('api_no')}")
        print(f"  {c('d',t('api_help'))}")
    print(f"  {c('d',t('commands'))}")
    mode_label = c('g', t('data_on')) if DATA_MODE else c('d', t('data_off'))
    print(f"  {c('d',t('data_toggle') + '  |  ' + mode_label)}")
    print()

    while True:
        try:
            user = input(f"  {c('c', t('you'))} > ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {c('d', t('bye'))}")
            break

        if not user: continue
        if user in ("/quit", "/q"):
            print(f"  {c('d', t('bye'))}"); break
        if user in ("/lang", "/language"):
            global LANG
            LANG = "en" if LANG == "zh" else "zh"
            T = T_EN if LANG == "en" else T_ZH
            print(f"  {c('g','->')} {'English' if LANG == 'en' else '中文'}")
            continue
        if user in ("/data", "/mode"):
            DATA_MODE = not DATA_MODE
            label = c('g', t('data_on')) if DATA_MODE else c('d', t('data_off'))
            print(f"  {c('g','->')} {label}")
            continue
        if user in ("/status", "/stats"):
            st = agent.get_status()
            print(f"  fingerprints: {st['fingerprints'].get('total',0)}")
            print(f"  executions: {st['execution_count']}")
            if 'tools' in st:
                print(f"  tools: {st['tools'].get('total_calls',0)} calls")
            if 'kg' in st:
                print(f"  knowledge graph: {st['kg'].get('total_nodes',0)} nodes")
            if 'budget' in st:
                print(f"  budget: {st['budget'].get('remaining_pct',0)}% remaining")
            if 'pitfalls' in st:
                print(f"  pitfalls: {st['pitfalls'].get('total',0)} total")
            continue
        if user in ("/soul", "/魂"):
            if hasattr(agent, 'soul'):
                print(f"  {agent.soul.describe()}")
            else:
                print(f"  {c('d',t('soul_no'))}")
            continue
        if user == "/history":
            for h in agent.execution_history[-5:]:
                print(f"  [{h['task'][:40]}...] {h['result'].get('actual_steps','?')} {t('step')}")
            continue

        # ── Execute ──
        tt, dom = guess_type(user)
        print(f"  {c('d','[' + tt + ']')}")

        bp = agent.predict(user, tt, dom)
        ml = bp.get("match_level", "cold")
        icon = {"template": "🟡", "exact": "🟢", "fuzzy": "🟡", "cold": "🔵"}.get(ml, "⚪")
        if ml == "cold":
            print(f"  {icon} {t('cold')}")
        else:
            print(f"  {icon} {c('b',ml)}  {t('pred')}:~{bp['expected_steps']}{t('step')}  {t('conf')}={bp['confidence']:.0%}")
        pits = bp.get("pitfall_list", [])
        if pits:
            names = ", ".join(p.get("name", str(p)[:20]) for p in pits[:3])
            print(f"  {c('y',t('pitfalls')+':')} {names}")
        note = bp.get("note", "")
        if note and ml != "cold":
            print(f"  {c('d',note)}")

        # Execute with spinner
        llm = call_llm if API_KEY else lambda p, **_: f"[simulate] {p[:40]}..."
        import threading
        running = True
        def spin():
            sp = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
            i = 0; start = time.time()
            while running:
                e = time.time() - start
                thk = t('thinking')
                sys.stdout.write(f"\r  {c('c',sp[i%10])} {c('d',f'{e:.1f}s {thk}')}")
                sys.stdout.flush(); i += 1; time.sleep(0.1)
            sys.stdout.write("\r" + " " * 50 + "\r"); sys.stdout.flush()
        timer = threading.Thread(target=spin, daemon=True)
        timer.start()
        result = agent.execute(user, bp, llm_call=llm)
        running = False; timer.join(timeout=0.3)

        steps = result["actual_steps"]; tok = result["actual_tokens"]
        ts_elapsed = result.get("elapsed_seconds", 0)
        corr = result.get("correction_count", 0)
        mid = result.get("mid_checks", 0); god = result.get("god_checks", 0)
        print(f"  {c('g',t('done'))} {steps}{t('step')} {tok}{t('tk')} {ts_elapsed:.1f}s {t('corr')}={corr}")
        if mid > 0 or god > 0:
            print(f"  {c('y',t('checks')+':')} mid={mid} god={god}")
        ad = result.get("adversarial_result", "")
        if ad:
            print(f"  {c('m',t('adversarial')+':')} {ad[:120]}")

        # Output preview
        out_steps = result.get("steps", [])
        if out_steps:
            final = str(out_steps[-1])
            if isinstance(final, tuple): final = str(final[0])
            print(f"  {c('d','─'*50)}")
            for line in final.split("\n")[:10]:
                print(f"  {line}")
            if len(final) > 500:
                print(f"  {c('d','... (' + str(len(final)) + ' chars)')}")

        # Learn
        lr = agent.learn(user, result, bp)
        nw = lr.get("new_weights", [])
        if nw:
            wstr = ",".join(f"{w:.2f}" for w in nw)
            print(f"  {c('m',t('learn')+':')} weights=[{wstr}]")
        if lr.get("personality"):
            print(f"  {mood_detail(lr['personality'])}")
        if lr.get("intensity"):
            colors = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
            print(f"  {c('d','学习强度: ' + colors.get(lr['intensity'], lr['intensity']))}")

        print()


if __name__ == "__main__":
    ver = "qy"
    for arg in sys.argv[1:]:
        cleaned = arg.lstrip("-").lstrip("v")
        if cleaned in V_ALIAS and V_ALIAS[cleaned] in VERSIONS:
            ver = V_ALIAS[cleaned]
        elif arg in ("--en", "-en"):
            LANG = "en"; T = T_EN
        elif arg in ("--zh", "-zh"):
            LANG = "zh"; T = T_ZH
        elif arg in ("--data", "-d"):
            DATA_MODE = True

    if len(sys.argv) == 1:
        ver, lang = select_all()
        if ver is None:
            print(f"  {t('bye')}")
            sys.exit(0)
        if lang: LANG = lang; T = T_EN if lang == "en" else T_ZH

    run_chat(ver)
