# src/automata/automata_visualizer.py
"""自动机可视化工具

根据实验书第4章加分项要求：
- NFA图
- DFA图
- 最小DFA图

生成 DOT 格式输出供 Graphviz 渲染，以及 ASCII 控制台输出。
"""

from .nfa import NFA
from .dfa import DFA, subset_construction, dfa_to_dot, dfa_to_ascii
from .dfa_minimizer import hopcroft_minimize
from .regex_to_nfa import regex_to_nfa


# ── NFA 可视化 ───────────────────────────────────────────────────────

def nfa_to_dot(nfa, title="NFA"):
    """Convert NFA to Graphviz DOT format.

    Args:
        nfa: NFA object
        title: graph title

    Returns:
        str: DOT format string
    """
    lines = [
        f"// {title}",
        f"digraph NFA {{",
        '  rankdir=LR;',
        '  node [shape=circle, style=filled, fontname="Courier New", fontsize=11];',
        '  edge [fontname="Courier New", fontsize=9];',
        '',
        f'  __start [shape=point];',
        f'  __start -> S{nfa.start};',
        '',
    ]

    for state in sorted(nfa.states):
        if state in nfa.accepts and state == nfa.start:
            fill = "#C3E6CB"  # start + accept
            shape = "doublecircle"
        elif state in nfa.accepts:
            fill = "#D4EDDA"
            shape = "doublecircle"
        elif state == nfa.start:
            fill = "#E8F0FE"
            shape = "circle"
        else:
            fill = "#FFFFFF"
            shape = "circle"

        lines.append(f'  S{state} [shape={shape}, fillcolor="{fill}", label="S{state}"];')

    lines.append("")

    # Group transitions
    edge_labels = {}
    for (src, sym), targets in nfa.transitions.items():
        for dst in targets:
            key = (src, dst)
            if key not in edge_labels:
                edge_labels[key] = []
            label = "ε" if sym is None else str(sym)
            edge_labels[key].append(label)

    for (src, dst), labels in edge_labels.items():
        label_str = ", ".join(labels)
        style = 'style="dashed"' if any(l == "ε" for l in labels) else ''
        lines.append(f'  S{src} -> S{dst} [{style} label="{label_str}"];')

    lines.append("}")
    return "\n".join(lines)


def nfa_to_ascii(nfa, title="NFA"):
    """Convert NFA to ASCII text representation.

    Args:
        nfa: NFA object
        title: table title

    Returns:
        str: ASCII text
    """
    lines = []
    sep = "=" * 70
    lines.append(sep)
    lines.append(f"  {title}: {nfa.summary()}")
    lines.append("-" * 70)
    lines.append(f"  Start:   S{nfa.start}")
    lines.append(f"  Accepts: {{{', '.join(f'S{s}' for s in sorted(nfa.accepts))}}}")
    lines.append(f"  Alphabet: {{{', '.join(sorted(nfa.alphabet))}}}")
    lines.append("-" * 70)

    for state in sorted(nfa.states):
        marker = ""
        if state == nfa.start and state in nfa.accepts:
            marker = " (start+accept)"
        elif state == nfa.start:
            marker = " (start)"
        elif state in nfa.accepts:
            marker = " (accept)"

        lines.append(f"\n  S{state}{marker}:")
        for (src, sym), targets in nfa.transitions.items():
            if src != state:
                continue
            for dst in sorted(targets):
                sym_str = "ε" if sym is None else f"'{sym}'"
                lines.append(f"    --{sym_str}--> S{dst}")

    lines.append("")
    lines.append(sep)
    return "\n".join(lines)


# ── 完整流水线可视化 ──────────────────────────────────────────────

class AutomataPipelineVisualizer:
    """Regex → NFA → DFA → MinDFA 完整流水线可视化。"""

    def __init__(self, pattern):
        """
        Args:
            pattern: regex string
        """
        self.pattern = pattern
        self.nfa = None
        self.dfa = None
        self.min_dfa = None
        self._build()

    def _build(self):
        self.nfa = regex_to_nfa(self.pattern)
        self.dfa = subset_construction(self.nfa)
        self.min_dfa = hopcroft_minimize(self.dfa)

    def summary(self):
        """Return a text summary of the pipeline."""
        return (f"Regex '{self.pattern}': "
                f"NFA {len(self.nfa.states)} states → "
                f"DFA {len(self.dfa.states)} states → "
                f"MinDFA {len(self.min_dfa.states)} states "
                f"(-{len(self.dfa.states) - len(self.min_dfa.states)})")

    def all_dots(self):
        """Return DOT strings for NFA, DFA, and MinDFA.

        Returns:
            dict: {"nfa": str, "dfa": str, "min_dfa": str}
        """
        return {
            "nfa": nfa_to_dot(self.nfa, f"NFA for '{self.pattern}'"),
            "dfa": dfa_to_dot(self.dfa, f"DFA for '{self.pattern}'"),
            "min_dfa": dfa_to_dot(self.min_dfa, f"MinDFA for '{self.pattern}'"),
        }

    def all_ascii(self):
        """Return ASCII representations for NFA, DFA, and MinDFA.

        Returns:
            dict: {"nfa": str, "dfa": str, "min_dfa": str}
        """
        return {
            "nfa": nfa_to_ascii(self.nfa, f"NFA for '{self.pattern}'"),
            "dfa": dfa_to_ascii(self.dfa, f"DFA for '{self.pattern}'"),
            "min_dfa": dfa_to_ascii(self.min_dfa, f"MinDFA for '{self.pattern}'"),
        }

    def display(self):
        """Print all three automata."""
        print(f"\n{'='*70}")
        print(f"  Regex → NFA → DFA → MinDFA Pipeline: '{self.pattern}'")
        print(f"{'='*70}")
        for name, text in self.all_ascii().items():
            print(f"\n  === {name.upper()} ===")
            print(text)


# ── PL/0 所有词法规则的可视化 ──────────────────────────────────────

def visualize_all_pl0_tokens():
    """为 PL/0 所有词法规则生成可视化。

    Returns:
        dict: token_name → {"nfa_dot": str, "dfa_dot": str, "min_dfa_dot": str}
    """
    from .regex_to_nfa import PL0_REGEX_MAP, build_pl0_lexer_nfas

    results = {}
    for name, pattern in PL0_REGEX_MAP.items():
        try:
            viz = AutomataPipelineVisualizer(pattern)
            results[name] = {
                "pattern": pattern,
                "summary": viz.summary(),
                "dots": viz.all_dots(),
            }
        except Exception as e:
            results[name] = {"pattern": pattern, "error": str(e)}

    return results


# ── 测试入口 ────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    # 测试标识符
    print("=== 标识符: [a-zA-Z][a-zA-Z0-9]* ===")
    viz = AutomataPipelineVisualizer("[a-zA-Z][a-zA-Z0-9]*")
    viz.display()

    # 测试数字
    print("\n=== 数字: [0-9]+ ===")
    viz2 = AutomataPipelineVisualizer("[0-9]+")
    viz2.display()

    # DOT 输出
    print("\n=== DOT 格式 (NFA for identifier) ===")
    print(nfa_to_dot(viz.nfa, "Identifier NFA"))

    print("\n=== DOT 格式 (MinDFA for identifier) ===")
    print(dfa_to_dot(viz.min_dfa, "Identifier MinDFA"))

    # PL/0 所有 token
    print("\n=== PL/0 所有词法规则汇总 ===")
    all_results = visualize_all_pl0_tokens()
    for name, info in all_results.items():
        if "error" in info:
            print(f"  {name:15s}: ERROR - {info['error']}")
        else:
            print(f"  {name:15s}: {info['summary']}")
