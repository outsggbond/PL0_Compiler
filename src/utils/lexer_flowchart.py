# src/utils/lexer_flowchart.py
"""词法分析流程图 (必做可视化)

根据实验书第4章要求：
- 绘制状态转换图 (标识符DFA, 数字DFA)
- 设计词法识别流程图
- 输出分析结果

新增功能：
- 使用 Graphviz 直接将生成的 DOT 格式渲染为 PNG 图片
"""

import os
try:
    from graphviz import Source
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

FONT = "Microsoft YaHei"
# ── 状态转换图定义 ─────────────────────────────────────────────────

# 标识符 DFA
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


# ── 渲染生成函数 ───────────────────────────────────────────────────

def dfa_to_dot(dfa_def, label_prefix="DFA"):
    lines = [
        f"// {dfa_def['name']}",
        f'digraph {label_prefix} {{',
        '  rankdir=LR;',
        f'  node [shape=circle, style=filled, fontname="{FONT}", fontsize=11];',
        f'  edge [fontname="{FONT}", fontsize=9];',
        '',
        '  __start [shape=point];',
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
    """将 DFA 定义转换为 ASCII 文本形式。"""
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


def generate_lexer_flowchart_dot():
    return f"""
digraph LexerFlowchart {{
  rankdir=TB;

  node [
      shape=box,
      style=filled,
      fontname="{FONT}",
      fontsize=11
  ];

  edge [
      fontname="{FONT}",
      fontsize=9
  ];

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
}}
"""

def render_dot_to_png(dot_string, output_filename):
    """将 DOT 格式字符串渲染并保存为 PNG 图片"""
    if not HAS_GRAPHVIZ:
        print(f"⚠️ 缺少 graphviz 库，无法渲染 {output_filename}.png。请运行: pip install graphviz")
        return

    try:
        src = Source(dot_string)
        src.format = 'png'
        # cleanup=True 意味着渲染后删除临时的 dot 源文件，只保留 png
        src.render(output_filename, cleanup=True)
        print(f"✅ 成功生成图片: {output_filename}.png")
    except Exception as e:
        print(f"❌ 渲染图片失败！")
        print(f"请确保你的系统已正确安装 Graphviz 软件，并已将其添加至系统环境变量 PATH 中。")
        print(f"错误详情: {e}")


# ── 测试入口 ────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=== 开始输出控制台文本 ===")
    print(dfa_to_ascii(IDENT_DFA))
    print(dfa_to_ascii(NUMBER_DFA))
    print("=== 控制台输出完成 ===\n")

    print("=== 开始渲染 PNG 图片 ===")
    
    # 渲染 标识符 DFA 为 out_ident_dfa.png
    ident_dot = dfa_to_dot(IDENT_DFA, "IdentDFA")
    render_dot_to_png(ident_dot, "out_ident_dfa")
    
    # 渲染 无符号整数 DFA 为 out_number_dfa.png
    number_dot = dfa_to_dot(NUMBER_DFA, "NumberDFA")
    render_dot_to_png(number_dot, "out_number_dfa")
    
    # 渲染 完整词法分析 DFA 为 out_full_lexer_dfa.png
    full_lexer_dot = dfa_to_dot(FULL_LEXER_DFA, "LexerDFA")
    render_dot_to_png(full_lexer_dot, "out_full_lexer_dfa")

    # 渲染 词法分析流程图 为 out_lexer_flowchart.png
    flowchart_dot = generate_lexer_flowchart_dot()
    render_dot_to_png(flowchart_dot, "out_lexer_flowchart")
    
    print("=== 所有任务执行完毕 ===")