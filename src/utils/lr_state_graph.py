# src/utils/lr_state_graph.py
"""LR项目集及识别活前缀的状态转换图 (第5章 LR 加分项)

根据实验书要求：
- 实现 LR 类项目集
- 识别活前缀的状态转换图

功能：
1. LR(0) 项目集规范族 → DOT 状态转换图
2. 每个状态显示包含的 LR(0) 项目
3. 状态间的 GOTO 转移边
4. 标注移进/规约动作 (基于 SLR 表)
"""

from ..lexer.token import TokenType as TT
from ..parser_lr.lr_items import (
    PRODUCTIONS_LR, build_canonical_collection, NONTERMINALS_LR, _tok_name_lr,
)


# ── 符号名称映射 ──────────────────────────────────────────────────

def _sym_name(sym):
    """Grammar symbol → human-readable name."""
    return _tok_name_lr(sym)


def _item_str(item, ascii_safe=False):
    """LRItem → human-readable string (e.g. 'E → E + • T').

    Args:
        item: LRItem object
        ascii_safe: if True, replace bullet with '.' for Windows GBK compatibility
    """
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
    """LR(0) 项目集状态转换图可视化。

    生成：
    - DOT 格式 (Graphviz 渲染)
    - ASCII 格式 (控制台输出)
    - JSON 格式 (结构化数据)
    """

    def __init__(self):
        """构建 LR(0) 规范族和转移表。"""
        self.C, self.transitions = build_canonical_collection()

        # 索引转移关系: state_idx -> [(symbol, target_state_idx)]
        self.state_edges = {}
        for (src, sym), dst in self.transitions.items():
            self.state_edges.setdefault(src, []).append((sym, dst))

        # 构建 SLR 表以获取动作信息
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
        """生成 Graphviz DOT 格式的状态转换图。

        Returns:
            str: DOT format string
        """
        lines = [
            f"// {title}",
            f"digraph LR_States {{",
            '  rankdir=TB;',
            '  node [shape=record, style=filled, fontname="Courier New", fontsize=10];',
            '  edge [fontname="Courier New", fontsize=9];',
            '',
        ]

        for i, state in enumerate(self.C):
            # 构建状态标签 (HTML-like label for record shape)
            item_lines = []
            for item in sorted(state, key=lambda x: (x.prod_idx, x.dot)):
                rhs = list(item.rhs)
                rhs.insert(item.dot, '•')
                symbols = ' '.join(_sym_name(s) for s in rhs)
                item_lines.append(f"  {item.lhs} → {symbols}")

            # 标记 accept 状态
            is_accept = any(
                item.prod_idx == 0 and item.is_reduce() for item in state
            )
            fill = "#D4EDDA" if is_accept else "#E8F0FE"

            label = f"I{i}\\n" + "\\n".join(item_lines[:12])  # 限制最多显示12个项目
            if len(item_lines) > 12:
                label += f"\\n  ... (+{len(item_lines) - 12} more)"

            # 添加动作摘要
            actions_str = self._state_actions_summary(i)
            if actions_str:
                label += f"\\n---\\n{actions_str}"

            lines.append(f'  S{i} [label="{label}", fillcolor="{fill}"];')

        lines.append("")

        # 转移边
        for (src, sym), dst in self.transitions.items():
            sym_label = _sym_name(sym)
            # 区分终结符和非终结符
            if sym in NONTERMINALS_LR:
                style = 'style="dashed" color="#6666CC"'
            else:
                style = 'style="solid" color="#333333"'
            lines.append(f'  S{src} -> S{dst} [{style}, label="{sym_label}"];')

        lines.append("}")
        return "\n".join(lines)

    def _state_actions_summary(self, state_idx):
        """返回状态的移进/规约动作摘要 (用于 label 显示)。"""
        actions = self.action.get(state_idx, {})
        if not actions:
            return ""

        parts = []
        for sym, (act, *args) in actions.items():
            if act == 'shift':
                parts.append(f"  S{args[0]} on {_sym_name(sym)}")
            elif act == 'reduce':
                parts.append(f"  r{args[0]} on {_sym_name(sym)}")
            elif act == 'accept':
                parts.append("  ACCEPT")

        return "\\n".join(parts[:6])

    # ── ASCII 输出 ────────────────────────────────────────────────

    def to_ascii(self):
        """生成 ASCII 文本格式的状态转换图。

        Returns:
            str: ASCII art
        """
        lines = []
        lines.append("=" * 70)
        lines.append("  LR(0) 项目集规范族 与 状态转换图")
        lines.append("=" * 70)
        lines.append(f"  状态总数: {self.num_states}")
        lines.append(f"  转移边数: {len(self.transitions)}")
        lines.append("-" * 70)

        for i, state in enumerate(self.C):
            lines.append(f"\n  状态 I{i}:")
            # Items
            for item in sorted(state, key=lambda x: (x.prod_idx, x.dot)):
                lines.append(f"    {_item_str(item, ascii_safe=True)}")

            # GOTO 出边
            edges = self.state_edges.get(i, [])
            if edges:
                for sym, dst in sorted(edges, key=lambda x: str(x[0])):
                    lines.append(f"    --{_sym_name(sym):>8s}--> I{dst}")

            # Actions
            actions = self.action.get(i, {})
            if actions:
                lines.append(f"    Actions:")
                for sym, (act, *args) in sorted(actions.items(), key=lambda x: str(x[0])):
                    if act == 'shift':
                        lines.append(f"      {_sym_name(sym):>8s} : shift → S{args[0]}")
                    elif act == 'reduce':
                        lines.append(f"      {_sym_name(sym):>8s} : reduce {_prod_str(args[0])}")
                    elif act == 'accept':
                        lines.append(f"      {_sym_name(sym):>8s} : ACCEPT")

        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)

    # ── 活前缀路径输出 ────────────────────────────────────────────

    def find_viable_prefix_path(self, target_state):
        """找到从状态0到达目标状态的一条路径 (活前缀路径)。

        Args:
            target_state: int, 目标状态编号

        Returns:
            list of (from_state, symbol, to_state) or None
        """
        # BFS from state 0
        from collections import deque
        queue = deque()
        queue.append((0, []))  # (state, path)
        visited = {0}

        while queue:
            state, path = queue.popleft()
            if state == target_state:
                return path

            for sym, dst in self.state_edges.get(state, []):
                if dst not in visited:
                    visited.add(dst)
                    queue.append((dst, path + [(state, sym, dst)]))

        return None

    def print_viable_prefix(self, target_state):
        """打印到达目标状态的活前缀。

        Args:
            target_state: int

        Returns:
            str: 活前缀路径文本
        """
        path = self.find_viable_prefix_path(target_state)
        if path is None:
            return f"No path to state I{target_state}"

        symbols = [_sym_name(sym) for _, sym, _ in path]
        lines = []
        lines.append(f"活前缀路径 (I0 → I{target_state}):")
        lines.append(f"  I0 -- {' '.join(symbols)} --> I{target_state}")
        return "\n".join(lines)

    # ── JSON 输出 ─────────────────────────────────────────────────

    def to_dict(self):
        """导出为结构化字典。

        Returns:
            dict
        """
        states = []
        for i, state in enumerate(self.C):
            items = []
            for item in sorted(state, key=lambda x: (x.prod_idx, x.dot)):
                items.append({
                    "production_id": item.prod_idx,
                    "lhs": item.lhs,
                    "rhs": list(item.rhs),
                    "dot": item.dot,
                    "str": _item_str(item),
                })

            edges_out = []
            for sym, dst in self.state_edges.get(i, []):
                edges_out.append({
                    "symbol": _sym_name(sym),
                    "target": dst,
                })

            actions = {}
            for sym, (act, *args) in self.action.get(i, {}).items():
                if act == 'shift':
                    actions[_sym_name(sym)] = f"shift S{args[0]}"
                elif act == 'reduce':
                    actions[_sym_name(sym)] = f"reduce {_prod_str(args[0])}"
                elif act == 'accept':
                    actions[_sym_name(sym)] = "ACCEPT"

            states.append({
                "id": i,
                "items": items,
                "edges_out": edges_out,
                "actions": actions,
            })

        return {
            "num_states": self.num_states,
            "num_transitions": len(self.transitions),
            "states": states,
            "conflicts": self.conflicts,
        }

    def to_json(self, indent=2):
        """导出为 JSON 字符串。"""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    # ── 简化状态转换图 (仅显示编号，不显示项目) ─────────────────

    def to_simple_dot(self, title="LR State Transition (Simplified)"):
        """生成简化的状态转换图 DOT (仅状态编号)。

        Returns:
            str: DOT format
        """
        lines = [
            f"// {title}",
            f"digraph LR_Simple {{",
            '  rankdir=TB;',
            '  node [shape=circle, style=filled, fontname="Courier New", fontsize=12];',
            '  edge [fontname="Courier New", fontsize=9];',
            '',
        ]

        for i, state in enumerate(self.C):
            is_accept = any(
                item.prod_idx == 0 and item.is_reduce() for item in state
            )
            fill = "#D4EDDA" if is_accept else "#E8F0FE"
            shape = "doublecircle" if is_accept else "circle"
            lines.append(f'  S{i} [label="I{i}", shape={shape}, fillcolor="{fill}"];')

        lines.append("")
        for (src, sym), dst in self.transitions.items():
            sym_label = _sym_name(sym)
            if sym in NONTERMINALS_LR:
                style = 'style="dashed" color="#6666CC"'
            else:
                style = 'style="solid"'
            lines.append(f'  S{src} -> S{dst} [{style}, label="{sym_label}"];')

        lines.append("}")
        return "\n".join(lines)

    # ── 项目集自动机图 (实验书要求) ───────────────────────────────

    def print_automaton(self):
        """打印完整的 LR(0) 项目集自动机 (类似实验书格式)。

        Returns:
            str: 文本格式
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"{'LR(0) 项目集自动机 (Canonical LR(0) Automaton)':^76s}")
        lines.append("=" * 80)

        for i, edges in sorted(self.state_edges.items()):
            if edges:
                for sym, dst in sorted(edges, key=lambda x: str(x[0])):
                    sym_name = _sym_name(sym)
                    lines.append(f"  I{i:3d}  --{sym_name:>12s}-->  I{dst}")

        lines.append("=" * 80)
        return "\n".join(lines)


# ── 便捷函数 ──────────────────────────────────────────────────────

def generate_lr_state_graph(output_format="ascii"):
    """生成 LR 状态图的便捷入口。

    Args:
        output_format: "ascii", "dot", "simple_dot", "json", "automaton"

    Returns:
        str: 可视化结果
    """
    graph = LRStateGraph()
    if output_format == "ascii":
        return graph.to_ascii()
    elif output_format == "dot":
        return graph.to_dot()
    elif output_format == "simple_dot":
        return graph.to_simple_dot()
    elif output_format == "json":
        return graph.to_json()
    elif output_format == "automaton":
        return graph.print_automaton()
    else:
        return graph.to_ascii()


# ── 测试入口 ────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    # Ensure UTF-8 output on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    graph = LRStateGraph()

    # ASCII 格式
    print(graph.to_ascii())

    # 简化自动机
    print("\n\n" + graph.print_automaton())

    # DOT 格式
    print("\n\n=== DOT (简化版) ===")
    print(graph.to_simple_dot())

    # 特定状态的活前缀
    if graph.num_states > 5:
        print("\n\n" + graph.print_viable_prefix(5))
