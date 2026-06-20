# src/utils/lr_state_graph.py
"""LR项目集及识别活前缀的状态转换图 (第5章 LR 加分项)"""

import json
try:
    from graphviz import Source
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

from ..lexer.token import TokenType as TT
from ..parser_lr.lr_items import (
    PRODUCTIONS_LR, build_canonical_collection, NONTERMINALS_LR, _tok_name_lr,
)

# ── 符号名称映射 ──────────────────────────────────────────────────

def _sym_name(sym):
    """Grammar symbol → human-readable name."""
    return _tok_name_lr(sym)

def _item_str(item, ascii_safe=False):
    """LRItem → human-readable string (e.g. 'E → E + • T')."""
    s = str(item)
    if ascii_safe:
        s = s.replace('•', '.')
    return s

def _prod_str(prod_idx):
    """Production index → human-readable string."""
    lhs, rhs = PRODUCTIONS_LR[prod_idx]
    rhs_str = ' '.join(_sym_name(s) for s in rhs) if rhs else 'ε'
    return f"{lhs} → {rhs_str}"

# ── LR 状态图生成 ──────────────────────────────────────────────────

class LRStateGraph:
    """LR(0) 项目集状态转换图可视化。"""

    def __init__(self):
        self.C, self.transitions = build_canonical_collection()

        self.state_edges = {}
        for (src, sym), dst in self.transitions.items():
            self.state_edges.setdefault(src, []).append((sym, dst))

        from ..parser_ll.first_follow import compute_first, compute_follow
        from ..parser_lr.lr_table import build_slr_table

        first = compute_first()
        follow = compute_follow(first)
        follow["S'"] = {TT.EOF}
        follow['ConstRest'] = {TT.SEMICOLON}
        follow['VarRest'] = {TT.SEMICOLON}
        follow['StmtList'] = {TT.END}
        follow['Sign'] = first.get('Term', set()) - {None}
        follow['TermList'] = follow.get('Expression', set())
        follow['FactorList'] = follow['TermList'].copy()
        follow['FactorList'] |= {TT.PLUS, TT.MINUS}
        follow['Expression'] = follow.get('Expression', set()) | {TT.RPAREN, TT.SEMICOLON, TT.END, TT.THEN, TT.DO, TT.PERIOD}

        self.action, self.goto, self.conflicts = build_slr_table(
            self.C, self.transitions, follow
        )

    @property
    def num_states(self):
        return len(self.C)

    # ── DOT 输出 ─────────────────────────────────────────────────

    def to_dot(self, title="LR(0) State Transition Graph"):
        lines = [
            f"// {title}",
            f"digraph LR_States {{",
            '  rankdir=TB;',
            '  node [shape=record, style=filled, fontname="Courier New", fontsize=10];',
            '  edge [fontname="Courier New", fontsize=9];',
            '',
        ]

        for i, state in enumerate(self.C):
            item_lines = []
            for item in sorted(state, key=lambda x: (x.prod_idx, x.dot)):
                rhs = list(item.rhs)
                rhs.insert(item.dot, '•')
                symbols = ' '.join(_sym_name(s) for s in rhs)
                item_lines.append(f"  {item.lhs} → {symbols}")

            is_accept = any(item.prod_idx == 0 and item.is_reduce() for item in state)
            fill = "#D4EDDA" if is_accept else "#E8F0FE"

            label = f"I{i}\\n" + "\\n".join(item_lines[:12])
            if len(item_lines) > 12:
                label += f"\\n  ... (+{len(item_lines) - 12} more)"

            actions_str = self._state_actions_summary(i)
            if actions_str:
                label += f"\\n---\\n{actions_str}"

            lines.append(f'  S{i} [label="{label}", fillcolor="{fill}"];')

        lines.append("")
        for (src, sym), dst in self.transitions.items():
            sym_label = _sym_name(sym)
            style = 'style="dashed" color="#6666CC"' if sym in NONTERMINALS_LR else 'style="solid" color="#333333"'
            lines.append(f'  S{src} -> S{dst} [{style}, label="{sym_label}"];')

        lines.append("}")
        return "\n".join(lines)

    # ── 新增：PNG 渲染方法 ──────────────────────────────────────────
    def render_png(self, output_filename, simple=False):
        """将生成的状态图渲染为 PNG"""
        if not HAS_GRAPHVIZ:
            print("⚠️ 缺少 graphviz 库，请运行: pip install graphviz")
            return

        dot_data = self.to_simple_dot() if simple else self.to_dot()
        try:
            src = Source(dot_data)
            src.format = 'png'
            src.render(output_filename, cleanup=True)
            print(f"✅ 成功生成状态图图片: {output_filename}.png")
        except Exception as e:
            print(f"❌ 渲染失败: {e}")

    def _state_actions_summary(self, state_idx):
        actions = self.action.get(state_idx, {})
        parts = []
        for sym, (act, *args) in actions.items():
            if act == 'shift':
                parts.append(f"  S{args[0]} on {_sym_name(sym)}")
            elif act == 'reduce':
                parts.append(f"  r{args[0]} on {_sym_name(sym)}")
            elif act == 'accept':
                parts.append("  ACCEPT")
        return "\\n".join(parts[:6])

    # ── ASCII & 其他格式输出 (保持原有逻辑) ──────────────────────────

    def to_ascii(self):
        lines = ["="*70, "  LR(0) 项目集规范族 与 状态转换图", "="*70]
        lines.append(f"  状态总数: {self.num_states}")
        for i, state in enumerate(self.C):
            lines.append(f"\n  状态 I{i}:")
            for item in sorted(state, key=lambda x: (x.prod_idx, x.dot)):
                lines.append(f"    {_item_str(item, ascii_safe=True)}")
        return "\n".join(lines)

    def to_simple_dot(self, title="LR State Transition (Simplified)"):
        lines = [
            f"digraph LR_Simple {{",
            '  rankdir=TB;',
            '  node [shape=circle, style=filled, fontname="Courier New", fontsize=12];',
        ]
        for i, state in enumerate(self.C):
            is_accept = any(item.prod_idx == 0 and item.is_reduce() for item in state)
            fill = "#D4EDDA" if is_accept else "#E8F0FE"
            lines.append(f'  S{i} [label="I{i}", fillcolor="{fill}"];')
        for (src, sym), dst in self.transitions.items():
            style = 'style="dashed" color="#6666CC"' if sym in NONTERMINALS_LR else 'style="solid"'
            lines.append(f'  S{src} -> S{dst} [{style}, label="{_sym_name(sym)}"];')
        lines.append("}")
        return "\n".join(lines)

    def print_automaton(self):
        lines = ["="*80, f"{'LR(0) 项目集自动机':^76s}", "="*80]
        for i, edges in sorted(self.state_edges.items()):
            for sym, dst in sorted(edges, key=lambda x: str(x[0])):
                lines.append(f"  I{i:3d}  --{_sym_name(sym):>12s}-->  I{dst}")
        return "\n".join(lines)

# ── 入口 ────────────────────────────────────────────────────────

if __name__ == '__main__':
    graph = LRStateGraph()
    # 示例用法
    print(graph.to_ascii())
    # 渲染简单状态机图片
    graph.render_png("lr_state_graph_simple", simple=True)