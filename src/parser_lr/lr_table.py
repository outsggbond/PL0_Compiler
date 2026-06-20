# src/parser_lr/lr_table.py
"""SLR(1) parse table construction from LR(0) items and FOLLOW sets."""

import os
import csv

from .lr_items import (
    PRODUCTIONS_LR, build_canonical_collection, NONTERMINALS_LR, TERMINALS_LR,
    LRItem, _tok_name_lr,
)
from ..lexer.token import TokenType as TT


def _tok_name(sym):
    """Human-readable name for a grammar symbol."""
    if isinstance(sym, str):
        return sym
    return _tok_name_lr(sym)


def build_slr_table(C, transitions, follow):
    """Build SLR(1) ACTION and GOTO tables.  (代码不变，省略以节省篇幅)"""
    # 这里保持你原来的 build_slr_table 函数，一字不改
    action = {}
    goto = {}
    conflicts = []

    for i, state in enumerate(C):
        action[i] = {}
        goto[i] = {}

        for item in state:
            sym = item.next_sym()

            if sym is None:
                # Reduce item: A → α •
                if item.prod_idx == 0:
                    # Accept: S' → Program •
                    existing = action[i].get(TT.EOF)
                    if existing is not None and existing != ('accept',):
                        conflicts.append(f"State {i}: accept/reduce conflict with {existing}")
                    action[i][TT.EOF] = ('accept',)
                else:
                    # SLR(1): reduce by A → α on FOLLOW(A)
                    for f in follow.get(item.lhs, set()):
                        existing = action[i].get(f)
                        if existing is not None:
                            if existing[0] == 'shift':
                                conflicts.append(
                                    f"State {i}: shift/reduce conflict on {_tok_name(f)}: "
                                    f"shift → {existing[1]} vs reduce r{item.prod_idx}"
                                )
                            elif existing[0] == 'reduce':
                                conflicts.append(
                                    f"State {i}: reduce/reduce conflict on {_tok_name(f)}: "
                                    f"r{existing[1]} vs r{item.prod_idx}"
                                )
                            # Prefer shift for s/r conflict (standard SLR resolution)
                            if existing[0] == 'shift':
                                continue  # keep shift, skip reduce
                        action[i][f] = ('reduce', item.prod_idx)
            elif sym in TERMINALS_LR:
                # Shift item
                t = transitions.get((i, sym))
                if t is not None:
                    existing = action[i].get(sym)
                    if existing is not None and existing != ('shift', t):
                        conflicts.append(
                            f"State {i}: conflict on terminal {_tok_name(sym)}: "
                            f"{existing} vs shift to {t}"
                        )
                    action[i][sym] = ('shift', t)

        # GOTO table
        for nt in NONTERMINALS_LR:
            if nt == "S'":
                continue
            t = transitions.get((i, nt))
            if t is not None:
                goto[i][nt] = t

    return action, goto, conflicts


# ============================================================
# 原有的纯文本打印（保留）
# ============================================================
def print_slr_table(action, goto):
    """Pretty-print the SLR table (original version)."""
    all_terminals = sorted(set(
        t for state_act in action.values() for t in state_act.keys()
    ), key=_tok_name)
    all_nonterms = sorted(
        [nt for nt in NONTERMINALS_LR if nt != "S'"],
        key=lambda x: x
    )

    print("=" * 120)
    print("SLR(1) Parse Table")
    print("-" * 100)

    header = f"{'State':>5s} |"
    for t in all_terminals:
        header += f" {_tok_name(t):>10s} |"
    for nt in all_nonterms:
        header += f" {nt:>12s} |"
    print(header)
    print("-" * len(header))

    for i in sorted(action.keys()):
        row = f"{i:5d} |"
        for t in all_terminals:
            act = action.get(i, {}).get(t)
            if act is None:
                row += f" {'':>10s} |"
            elif act[0] == 'shift':
                row += f" {'s'+str(act[1]):>10s} |"
            elif act[0] == 'reduce':
                row += f" {'r'+str(act[1]):>10s} |"
            elif act[0] == 'accept':
                row += f" {'acc':>10s} |"
        for nt in all_nonterms:
            g = goto.get(i, {}).get(nt)
            if g is not None:
                row += f" {g:>12d} |"
            else:
                row += f" {'':>12s} |"
        print(row)


# ============================================================
# PrettyTable 美化打印（保留，但不影响 CSV 导出）
# ============================================================
def print_slr_table_pretty(action, goto):
    """Print a nicely formatted SLR table using PrettyTable."""
    try:
        from prettytable import PrettyTable
    except ImportError:
        print("prettytable not installed. Falling back to plain text table.")
        print_slr_table(action, goto)
        return

    all_terminals = sorted(
        set(t for state_act in action.values() for t in state_act.keys()),
        key=_tok_name,
    )
    all_nonterms = sorted(
        [nt for nt in NONTERMINALS_LR if nt != "S'"], key=lambda x: x
    )

    table = PrettyTable()
    field_names = ["State"] + [_tok_name(t) for t in all_terminals] + all_nonterms
    table.field_names = field_names

    for i in sorted(action.keys()):
        row = [str(i)]
        for t in all_terminals:
            act = action.get(i, {}).get(t)
            if act is None:
                row.append("")
            elif act[0] == "shift":
                row.append(f"s{act[1]}")
            elif act[0] == "reduce":
                row.append(f"r{act[1]}")
            elif act[0] == "accept":
                row.append("acc")
        for nt in all_nonterms:
            g = goto.get(i, {}).get(nt)
            row.append(str(g) if g is not None else "")
        table.add_row(row)

    print(table)


# ============================================================
# 新增：导出 CSV 文件
# ============================================================
def save_slr_table_csv(action, goto, filepath, delimiter=','):
    """将 SLR 解析表保存为 CSV 文件，方便用 Excel 打开。

    Args:
        action: ACTION 表
        goto: GOTO 表
        filepath: 输出文件路径（例如 'output/error/slr_table.csv'）
        delimiter: 分隔符，默认逗号，可改为 '\\t' 制表符
    """
    all_terminals = sorted(
        set(t for state_act in action.values() for t in state_act.keys()),
        key=_tok_name,
    )
    all_nonterms = sorted(
        [nt for nt in NONTERMINALS_LR if nt != "S'"], key=lambda x: x
    )
    # 列名与 PrettyTable 一致
    header = ["State"] + [_tok_name(t) for t in all_terminals] + all_nonterms

    # 创建输出目录（如果不存在）
    dirname = os.path.dirname(filepath)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(header)
        for state in sorted(action.keys()):
            row = [state]
            for t in all_terminals:
                act = action.get(state, {}).get(t)
                if act is None:
                    row.append("")
                elif act[0] == 'shift':
                    row.append(f"s{act[1]}")
                elif act[0] == 'reduce':
                    row.append(f"r{act[1]}")
                elif act[0] == 'accept':
                    row.append("acc")
            for nt in all_nonterms:
                g = goto.get(state, {}).get(nt)
                row.append(str(g) if g is not None else "")
            writer.writerow(row)

    print(f"SLR table saved as CSV: {filepath}")


# ============================================================
# 可视化部分（Graphviz / matplotlib，添加异常捕获）
# ============================================================
def visualize_lr_automaton(C, transitions, filename="lr_automaton"):
    """Draw the LR(0) automaton with Graphviz."""
    try:
        import graphviz
    except ImportError:
        print("graphviz not installed. Skipping automaton graph.")
        return

    dot = graphviz.Digraph(name="LR_Automaton", comment="LR(0) Automaton")
    dot.attr(rankdir="LR")
    dot.attr("node", shape="box", style="rounded", fontname="Courier New")

    for i, state in enumerate(C):
        label_lines = [f"State {i}"]
        for item in sorted(state, key=lambda it: (it.prod_idx, it.dot)):
            lhs = item.lhs
            rhs = item.rhs
            prod_str = lhs + " → "
            if item.dot == 0:
                prod_str += "• " + " ".join(map(_tok_name, rhs))
            else:
                before = " ".join(map(_tok_name, rhs[:item.dot]))
                after = " ".join(map(_tok_name, rhs[item.dot:]))
                prod_str += before + " • " + after
            label_lines.append(prod_str)
        label = "\n".join(label_lines)
        is_accept = any(it.prod_idx == 0 and it.next_sym() is None for it in state)
        attrs = {"label": label}
        if is_accept:
            attrs["peripheries"] = "2"
        dot.node(str(i), **attrs)

    for (from_state, sym), to_state in transitions.items():
        dot.edge(str(from_state), str(to_state), label=_tok_name(sym))

    try:
        dot.render(filename, format="png", cleanup=True)
        print(f"LR automaton saved as {filename}.png")
    except Exception as e:
        print(f"Skipping LR automaton graph: {e}")


def plot_slr_table(action, goto, filename="slr_table.png"):
    """Plot the SLR table as a coloured matrix with matplotlib."""
    try:
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap
    except ImportError:
        print("matplotlib not installed. Skipping table plot.")
        return

    all_terminals = sorted(
        set(t for state_act in action.values() for t in state_act.keys()),
        key=_tok_name,
    )
    all_nonterms = sorted(
        [nt for nt in NONTERMINALS_LR if nt != "S'"], key=lambda x: x
    )
    columns = all_terminals + all_nonterms
    rows = list(range(len(action)))

    char_matrix = []
    color_matrix = []
    for i in rows:
        row_chars = []
        row_colors = []
        for t in all_terminals:
            act = action.get(i, {}).get(t)
            if act is None:
                row_chars.append("")
                row_colors.append(0)
            elif act[0] == 'shift':
                row_chars.append(f"s{act[1]}")
                row_colors.append(1)
            elif act[0] == 'reduce':
                row_chars.append(f"r{act[1]}")
                row_colors.append(2)
            elif act[0] == 'accept':
                row_chars.append("acc")
                row_colors.append(3)
        for nt in all_nonterms:
            g = goto.get(i, {}).get(nt)
            if g is not None:
                row_chars.append(str(g))
                row_colors.append(4)
            else:
                row_chars.append("")
                row_colors.append(0)
        char_matrix.append(row_chars)
        color_matrix.append(row_colors)

    cmap = ListedColormap(["white", "lightblue", "lightcoral", "gold", "lightgreen"])
    fig, ax = plt.subplots(figsize=(max(12, len(columns)*0.8),
                                   max(6, len(rows)*0.5)))
    ax.axis("tight")
    ax.axis("off")

    table = ax.table(
        cellText=char_matrix,
        cellColours=[[cmap(c) for c in row] for row in color_matrix],
        rowLabels=[str(i) for i in rows],
        colLabels=[_tok_name(c) if c in all_terminals else c for c in columns],
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.5)

    plt.title("SLR(1) Parse Table", fontsize=14, weight="bold")
    plt.savefig(filename, dpi=150, bbox_inches="tight")
    print(f"SLR table saved as {filename}")
    plt.close()


# ============================================================
# 用来生成并输出 SLR(1) 分析表，同时根据是否存在冲突将结果保存到不同的子目录。
if __name__ == '__main__':
    import sys
    sys.path.insert(0, '..')
    from src.parser_ll.first_follow import compute_first, compute_follow

    # ② 计算 FIRST / FOLLOW 并补充 FOLLOW 集合
    first = compute_first()
    follow = compute_follow(first)
    """
    自动计算的 compute_follow 可能不包含 LR 分析需要的某些非终结符的 FOLLOW，
    或者因为文法改写（如引入 ConstRest 等辅助符号）导致其 FOLLOW 需要手动明确。

    这些赋值直接给出了这些非终结符允许跟在后面的终结符集合，
    保证 SLR 分析表构建时归约动作的前瞻判断正确。
    """
    # Add FOLLOW for LR-specific non-terminals
    follow["S'"] = {TT.EOF}
    follow['ConstRest'] = {TT.SEMICOLON}
    follow['VarRest'] = {TT.SEMICOLON}
    follow['StmtList'] = {TT.END}
    follow['Sign'] = first.get('Term', set()) - {None}
    follow['TermList'] = follow.get('Expression', set())
    follow['FactorList'] = follow['TermList'].copy()
    follow['FactorList'] |= {TT.PLUS, TT.MINUS}
    follow['Expression'] = follow.get('Expression', set()) | {TT.RPAREN, TT.SEMICOLON, TT.END, TT.THEN, TT.DO, TT.PERIOD}
    #  构建 SLR(1) 分析表
    # 构造 LR(0) 项目集规范族（所有状态）和状态间的转移
    C, transitions = build_canonical_collection()
    # 使用这些状态和上一步的 FOLLOW 集合，生成 action 表、goto 表，
    # 并记录发现的移进‑归约冲突或归约‑归约冲突。
    action, goto, conflicts = build_slr_table(C, transitions, follow)

    # 确定输出目录
    base_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'output')
    subdir = 'error' if conflicts else 'correct'
    out_dir = os.path.join(base_dir, subdir)
    os.makedirs(out_dir, exist_ok=True)
    slr_txt_path = os.path.join(out_dir, 'slr_table.txt')

    # 输出 SLR 表信息（屏幕+文件）
    from ..utils.output_manager import tee_output
    with tee_output(slr_txt_path):
        print(f"Canonical collection: {len(C)} states")
        if conflicts:
            print(f"Conflicts: {len(conflicts)}")
            for c in conflicts:
                print(f"  !! {c}")
        else:
            print("No SLR(1) conflicts.")
        print()

        # 1. 控制台仍打印美化表格（可选）
        print_slr_table_pretty(action, goto)

    # 2. 保存 CSV 文件到 output 目录
    if conflicts:
        csv_path = os.path.join(base_dir, 'error', 'slr_table.csv')
    else:
        csv_path = os.path.join(base_dir, 'correct', 'slr_table.csv')

    save_slr_table_csv(action, goto, csv_path)

    # 3. 可选的可视化输出（需要 Graphviz / matplotlib）
    visualize_lr_automaton(C, transitions, "lr_automaton")
    plot_slr_table(action, goto, "slr_table.png")