# src/utils/lexer_flowchart.py
"""词法分析流程图 (必做可视化)

根据实验书第4章要求：
- 绘制状态转换图 (标识符DFA, 数字DFA)
- 设计词法识别流程图
- 输出分析结果

生成：
1. 词法识别流程图 (DOT/ASCII)
2. 标识符 DFA 状态转换图
3. 数字 DFA 状态转换图
4. 运算符识别状态转换图 (:=, <=, >= 等双字符运算符)
"""

# ── 状态转换图定义 ─────────────────────────────────────────────────

# 标识符 DFA
# S0 --letter--> S1
# S1 --letter/digit--> S1   (loop)
IDENT_DFA = {
    "name": "标识符 DFA",
    "states": ["S0", "S1"],
    "start": "S0",
    "accept": ["S1"],
    "transitions": [
        ("S0", "letter", "S1"),
        ("S1", "letter/digit", "S1"),
    ],
}

# 数字 DFA
# S0 --digit--> S2
# S2 --digit--> S2   (loop)
NUMBER_DFA = {
    "name": "无符号整数 DFA",
    "states": ["S0", "S2"],
    "start": "S0",
    "accept": ["S2"],
    "transitions": [
        ("S0", "digit", "S2"),
        ("S2", "digit", "S2"),
    ],
}

# 完整词法分析 DFA (简化合并视图)
FULL_LEXER_DFA = {
    "name": "PL/0 词法分析完整 DFA",
    "states": ["S0", "S1", "S2", "S3", "S4", "S5", "S6"],
    "start": "S0",
    "accept": {
        "S1": "标识符/保留字",
        "S2": "无符号整数",
        "S3": "单字符运算符/界符",
        "S4": ":=",
        "S5": "<=",
        "S6": ">=",
    },
    "transitions": [
        # 标识符
        ("S0", "letter", "S1"),
        ("S1", "letter/digit", "S1"),
        # 数字
        ("S0", "digit", "S2"),
        ("S2", "digit", "S2"),
        # 单字符运算符
        ("S0", "+", "S3"), ("S0", "-", "S3"),
        ("S0", "*", "S3"), ("S0", "/", "S3"),
        ("S0", "=", "S3"), ("S0", "#", "S3"),
        # 双字符运算符第一部分
        ("S0", ":", "S4"),   # → := 所需
        ("S0", "<", "S5"),   # → <= 所需
        ("S0", ">", "S6"),   # → >= 所需
        # 双字符运算符第二部分
        ("S4", "=", "S3"),   # := 完成
        ("S5", "=", "S3"),   # <= 完成
        ("S6", "=", "S3"),   # >= 完成
        # 界符
        ("S0", "(", "S3"), ("S0", ")", "S3"),
        ("S0", ";", "S3"), ("S0", ",", "S3"),
        ("S0", ".", "S3"),
    ],
}


def dfa_to_dot(dfa_def, label_prefix="DFA"):
    """将 DFA 定义转换为 Graphviz DOT 格式。

    Args:
        dfa_def: dict with name, states, start, accept, transitions
        label_prefix: prefix for node labels (区分多个DFA图)

    Returns:
        str: DOT format string
    """
    lines = [
        f"// {dfa_def['name']}",
        f'digraph {label_prefix} {{',
        '  rankdir=LR;',
        '  node [shape=circle, style=filled, fontname="Courier New", fontsize=11];',
        '  edge [fontname="Courier New", fontsize=9];',
        '',
        '  // Start arrow',
        f'  __start [shape=point];',
        f'  __start -> {dfa_def["start"]};',
        '',
    ]

    accept = dfa_def.get("accept", [])
    if isinstance(accept, dict):
        accept_states = set(accept.keys())
    else:
        accept_states = set(accept)

    for state in dfa_def["states"]:
        if state in accept_states:
            fill = "#D4EDDA"  # green for accept
            shape = "doublecircle"
        elif state == dfa_def["start"]:
            fill = "#E8F0FE"  # blue for start
            shape = "circle"
        else:
            fill = "#FFFFFF"
            shape = "circle"

        label = state
        if isinstance(accept, dict) and state in accept:
            label = f"{state}\\n({accept[state]})"
        lines.append(f'  {state} [shape={shape}, fillcolor="{fill}", label="{label}"];')

    lines.append("")

    # Transitions (merge same from→to with different labels)
    edge_labels = {}
    for src, label, dst in dfa_def["transitions"]:
        key = (src, dst)
        if key not in edge_labels:
            edge_labels[key] = []
        edge_labels[key].append(label)

    for (src, dst), labels in edge_labels.items():
        label_str = ", ".join(labels)
        lines.append(f'  {src} -> {dst} [label="{label_str}"];')

    lines.append("}")
    return "\n".join(lines)


def dfa_to_ascii(dfa_def):
    """将 DFA 定义转换为 ASCII 文本形式。

    Returns:
        str: ASCII art representation
    """
    lines = []
    lines.append("=" * 60)
    lines.append(f"  {dfa_def['name']}")
    lines.append("-" * 40)
    lines.append(f"  起始状态: {dfa_def['start']}")

    accept = dfa_def.get("accept", [])
    if isinstance(accept, dict):
        accept_str = ", ".join(f"{s}({v})" for s, v in accept.items())
    else:
        accept_str = ", ".join(accept)
    lines.append(f"  接受状态: {accept_str}")
    lines.append("-" * 40)
    lines.append(f"  {'从':>6s}  --{'输入':>12s}-->  {'到':<6s}")
    lines.append("  " + "-" * 34)

    for src, label, dst in dfa_def["transitions"]:
        lines.append(f"  {src:>6s}  --{label:>12s}-->  {dst:<6s}")

    lines.append("=" * 60)
    return "\n".join(lines)


# ── 词法识别流程图 (ASCII) ─────────────────────────────────────────

def generate_lexer_flowchart_ascii():
    """生成词法分析过程的 ASCII 流程图。

    Returns:
        str: 流程图
    """
    lines = []
    lines.append("═══ PL/0 词法分析流程图 ═══")
    lines.append("")
    lines.append("              ┌──────────┐")
    lines.append("              │   开始    │")
    lines.append("              └────┬─────┘")
    lines.append("                   │")
    lines.append("                   ▼")
    lines.append("         ┌─────────────────┐")
    lines.append("         │   跳过空白字符    │")
    lines.append("         │ (空格/制表/换行)  │")
    lines.append("         └────────┬────────┘")
    lines.append("                  │")
    lines.append("                  ▼")
    lines.append("         ┌─────────────────┐")
    lines.append("         │   读取当前字符    │")
    lines.append("         └────────┬────────┘")
    lines.append("                  │")
    lines.append("                  ▼")
    lines.append("       ┌──────────────────────┐")
    lines.append("       │  文件结束 (EOF) ?     │")
    lines.append("       └────┬──────────┬──────┘")
    lines.append("            │ 是       │ 否")
    lines.append("            ▼          ▼")
    lines.append("    ┌──────────┐  ┌─────────────────┐")
    lines.append("    │ 返回 EOF  │  │  是注释 // 或 /* ? │")
    lines.append("    └──────────┘  └───┬──────────┬───┘")
    lines.append("                      │ 是       │ 否")
    lines.append("                      ▼          ▼")
    lines.append("              ┌──────────┐  ┌──────────────┐")
    lines.append("              │ 跳过注释   │  │  是字母 ?     │")
    lines.append("              │ 回到开头   │  └──┬───────┬───┘")
    lines.append("              └──────────┘     │ 是    │ 否")
    lines.append("                               ▼       ▼")
    lines.append("                      ┌──────────┐ ┌──────────────┐")
    lines.append("                      │识别标识符  │ │  是数字 ?     │")
    lines.append("                      │/保留字    │ └──┬───────┬───┘")
    lines.append("                      │(字母/数字)│    │ 是    │ 否")
    lines.append("                      └──────────┘    ▼       ▼")
    lines.append("                               ┌──────────┐ ┌──────────────┐")
    lines.append("                               │ 识别数字   │ │ 双字符运算符? │")
    lines.append("                               │ (digit+)  │ │ := <= >=    │")
    lines.append("                               └──────────┘ └──┬───────┬───┘")
    lines.append("                                               │ 是    │ 否")
    lines.append("                                               ▼       ▼")
    lines.append("                                        ┌──────────┐ ┌──────────────┐")
    lines.append("                                        │ 匹配双字符 │ │ 单字符运算符?  │")
    lines.append("                                        │ 运算符    │ │ + - * / = #  │")
    lines.append("                                        └──────────┘ └──┬───────┬───┘")
    lines.append("                                                        │ 是    │ 否")
    lines.append("                                                        ▼       ▼")
    lines.append("                                                 ┌──────────┐ ┌──────────────┐")
    lines.append("                                                 │ 返回运算符 │ │  是界符 ?    │")
    lines.append("                                                 │ Token    │ │ ( ) ; , .   │")
    lines.append("                                                 └──────────┘ └──┬───────┬───┘")
    lines.append("                                                                 │ 是    │ 否")
    lines.append("                                                                 ▼       ▼")
    lines.append("                                                          ┌──────────┐ ┌──────────┐")
    lines.append("                                                          │ 返回界符  │ │ 非法字符  │")
    lines.append("                                                          │ Token    │ │ 报错+跳过 │")
    lines.append("                                                          └──────────┘ └──────────┘")
    lines.append("")
    return "\n".join(lines)


def generate_lexer_flowchart_dot():
    """生成词法分析流程图的 Graphviz DOT 格式。

    Returns:
        str: DOT format string
    """
    dot = """digraph LexerFlowchart {
  rankdir=TB;
  node [shape=box, style=filled, fontname="Courier New", fontsize=11];
  edge [fontname="Courier New", fontsize=9];

  start [label="开始", shape=ellipse, fillcolor="#E8F0FE"];
  skip_ws [label="跳过空白字符\\n(空格/制表/换行)"];
  read_ch [label="读取当前字符"];
  check_eof [label="文件结束?", shape=diamond, fillcolor="#FFF3CD"];
  return_eof [label="返回 EOF Token", fillcolor="#D4EDDA"];
  check_comment [label="是注释 // 或 /* ?", shape=diamond, fillcolor="#FFF3CD"];
  skip_comment [label="跳过注释\\n回到开头"];
  check_letter [label="是字母?", shape=diamond, fillcolor="#FFF3CD"];
  ident [label="识别标识符/保留字\\n(字母/数字)*", fillcolor="#E8F0FE"];
  check_digit [label="是数字?", shape=diamond, fillcolor="#FFF3CD"];
  number [label="识别无符号整数\\n(digit)+", fillcolor="#E8F0FE"];
  check_twochar [label="双字符运算符?\\n:= <= >=", shape=diamond, fillcolor="#FFF3CD"];
  twochar_op [label="匹配双字符运算符", fillcolor="#E8F0FE"];
  check_op [label="单字符运算符?\\n+ - * / = #", shape=diamond, fillcolor="#FFF3CD"];
  single_op [label="返回运算符 Token", fillcolor="#D4EDDA"];
  check_delim [label="界符?\\n( ) ; , .", shape=diamond, fillcolor="#FFF3CD"];
  delim [label="返回界符 Token", fillcolor="#D4EDDA"];
  illegal [label="非法字符\\n报错 + 跳过", fillcolor="#F8D7DA"];

  start -> skip_ws;
  skip_ws -> read_ch;
  read_ch -> check_eof;
  check_eof -> return_eof [label="是"];
  check_eof -> check_comment [label="否"];
  check_comment -> skip_comment [label="是"];
  skip_comment -> skip_ws;
  check_comment -> check_letter [label="否"];
  check_letter -> ident [label="是"];
  check_letter -> check_digit [label="否"];
  check_digit -> number [label="是"];
  check_digit -> check_twochar [label="否"];
  check_twochar -> twochar_op [label="是"];
  check_twochar -> check_op [label="否"];
  check_op -> single_op [label="是"];
  check_op -> check_delim [label="否"];
  check_delim -> delim [label="是"];
  check_delim -> illegal [label="否"];
  // 所有返回后回到调用处
}
"""
    return dot


# ── 状态转换图批量生成 ──────────────────────────────────────────────

def generate_all_dfa_dots():
    """生成所有 DFA 状态转换图的 DOT 格式。

    Returns:
        dict: name -> DOT string
    """
    return {
        "ident_dfa": dfa_to_dot(IDENT_DFA, "IdentDFA"),
        "number_dfa": dfa_to_dot(NUMBER_DFA, "NumberDFA"),
        "full_lexer_dfa": dfa_to_dot(FULL_LEXER_DFA, "LexerDFA"),
    }


def generate_all_dfa_ascii():
    """生成所有 DFA 状态转换图的 ASCII 格式。

    Returns:
        str: 所有图的 ASCII 文本
    """
    parts = []
    parts.append(dfa_to_ascii(IDENT_DFA))
    parts.append("")
    parts.append(dfa_to_ascii(NUMBER_DFA))
    parts.append("")
    parts.append(dfa_to_ascii(FULL_LEXER_DFA))
    return "\n".join(parts)


# ── 正规式→NFA→DFA→最小DFA 展示辅助 ──────────────────────────────

def regex_to_min_dfa_summary():
    """生成正规式→NFA→DFA→最小DFA 转换过程摘要 (用于报告)。

    Returns:
        str: 摘要文本
    """
    return """
═══════════════════════════════════════════════════════════
  正规式 → NFA → DFA → DFA最小化  过程展示
═══════════════════════════════════════════════════════════

【标识符】
  正规式:  letter (letter | digit)*

  NFA:
       ε          letter         letter/digit
    → S0 ──→ S0' ────→ S1 ──→ S2 ←──┐
                              │       │
                              └───ε───┘
  DFA:
       letter
    S0 ────→ S1
              ↑│
              ││ letter/digit
              └┘

【无符号整数】
  正规式:  digit+

  NFA:
       ε         digit         digit
    → S0 ──→ S0' ────→ S1 ──→ S2 ←──┐
                              │       │
                              └───ε───┘
  DFA:
       digit
    S0 ────→ S2
              ↑│
              ││ digit
              └┘

【运算符 :=】
  正规式:  : =
  NFA:
       :         =
    → S0 ──→ S1 ──→ S2(accept)
  DFA: 同上 (已最小)

═══════════════════════════════════════════════════════════
"""


# ── 测试入口 ────────────────────────────────────────────────────────
if __name__ == '__main__':
    # 输出词法分析流程图
    print(generate_lexer_flowchart_ascii())
    print()

    # 输出标识符 DFA
    print(dfa_to_ascii(IDENT_DFA))
    print()

    # 输出数字 DFA
    print(dfa_to_ascii(NUMBER_DFA))
    print()

    # 输出 DOT 格式 (可保存为 .dot 文件用 Graphviz 渲染)
    print("=== DOT 格式 (标识符 DFA) ===")
    print(dfa_to_dot(IDENT_DFA))
    print()
    print("=== DOT 格式 (数字 DFA) ===")
    print(dfa_to_dot(NUMBER_DFA))
    print()
    print("=== 词法分析流程图 DOT ===")
    print(generate_lexer_flowchart_dot())
    print()
    print(regex_to_min_dfa_summary())
