# src/parser_lr/lr_parser.py
"""SLR(1) shift-reduce parser for PL/0.

Features:
- Shift-reduce parsing using SLR(1) ACTION/GOTO tables
- Concrete syntax tree construction
- Panic-mode error recovery
- Graphviz DOT visualization (text + rendered image)
- Export trace and errors to CSV in output/correct or output/error
"""

import os
import csv

from ..lexer.token import TokenType as TT, Token
from ..lexer.lexer import Lexer
from .lr_items import (
    PRODUCTIONS_LR, build_canonical_collection, NONTERMINALS_LR, _tok_name_lr,
)
from .lr_table import build_slr_table


def _tok_name(tok_or_sym):
    """Human-readable name for a token or grammar symbol."""
    if isinstance(tok_or_sym, Token):
        return _tok_name_lr(tok_or_sym.type)
    return _tok_name_lr(tok_or_sym)


class SyntaxTreeNode:
    """Node in the LR-built syntax tree."""
    def __init__(self, label, value=None, token=None):
        self.label = label
        self.value = value
        self.token = token
        self.children = []

    def add_child(self, child):
        if child is not None:
            self.children.append(child)

    def __repr__(self):
        if self.children:
            kids = ', '.join(repr(c) for c in self.children)
            return f"{self.label}({kids})"
        return f"{self.label}:{self.value or ''}"


class LRParser:
    """SLR(1) parser."""

    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.errors = []

        # Build tables on init
        # Need FOLLOW sets — borrow from LL module
        from ..parser_ll.first_follow import compute_first, compute_follow

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

        self.C, self.transitions = build_canonical_collection()
        self.action, self.goto, self.conflicts = build_slr_table(
            self.C, self.transitions, follow
        )

    def _tokenize_all(self):
        """Tokenize all input and return tokens list (errors appended to self.errors)."""
        tokens = []
        while True:
            tok = self.lexer.get_next_token()
            if tok.type == TT.ERROR:
                self.errors.append(f"Lexical error at line {tok.line}: {tok.value}")
                continue
            tokens.append(tok)
            if tok.type == TT.EOF:
                break
        return tokens

    def parse(self):
        """Run the LR parser. Returns (tree, errors)."""
        return self._parse_impl(trace=False)

    def parse_with_trace(self):
        """Run the LR parser and return (tree, errors, trace_steps)."""
        return self._parse_impl(trace=True)

    def _parse_impl(self, trace=False):
        """Internal parse implementation with optional step tracing."""
        self.errors.clear()
        for c in self.conflicts:
            self.errors.append(f"Warning (grammar): {c}")

        stack = [0]
        sem_stack = []
        tokens = self._tokenize_all()
        pos = 0
        step_num = 0
        trace_steps = [] if trace else None

        while pos < len(tokens):
            tok = tokens[pos]
            state = stack[-1]
            action_entry = self.action.get(state, {}).get(tok.type)
            token_name = _tok_name(tok)

            if trace:
                remaining = ' '.join(_tok_name(t) for t in tokens[pos:pos + 6])
                if pos + 6 < len(tokens):
                    remaining += ' ...'
                trace_steps.append({
                    'step': step_num,
                    'stack': list(stack),
                    'input_pos': pos,
                    'input_tokens': remaining,
                    'lookahead': token_name,
                    'lookahead_value': str(tok.value),
                })

            if action_entry is None:
                if trace:
                    trace_steps[-1]['action'] = 'ERROR'
                    trace_steps[-1]['detail'] = f"No action for {token_name}"
                expected = list(self.action.get(state, {}).keys())
                expected_names = ', '.join(_tok_name_lr(e) for e in expected)
                self.errors.append(
                    f"Syntax error at line {tok.line}, col {tok.column}: "
                    f"unexpected '{token_name}' ({tok.value}), "
                    f"expected one of: {expected_names or 'EOF'}"
                )
                recovered = False
                while len(stack) > 1:
                    stack.pop()
                    if sem_stack:
                        sem_stack.pop()
                    new_state = stack[-1]
                    if tok.type in self.action.get(new_state, {}):
                        recovered = True
                        break
                if not recovered:
                    pos += 1
                step_num += 1
                continue

            action_type = action_entry[0]

            if action_type == 'shift':
                next_state = action_entry[1]
                if trace:
                    trace_steps[-1]['action'] = 'SHIFT'
                    trace_steps[-1]['detail'] = f"shift to state {next_state}"
                stack.append(next_state)
                node = SyntaxTreeNode(token_name, tok.value, tok)
                sem_stack.append(node)
                pos += 1

            elif action_type == 'reduce':
                prod_idx = action_entry[1]
                lhs, rhs = PRODUCTIONS_LR[prod_idx]
                rhs_str = ' '.join(_tok_name_lr(s) for s in rhs) if rhs else 'eps'

                if trace:
                    trace_steps[-1]['action'] = 'REDUCE'
                    trace_steps[-1]['detail'] = f"reduce by r{prod_idx}: {lhs} → {rhs_str}"

                node = SyntaxTreeNode(lhs)
                if rhs and rhs != ():
                    for _ in range(len(rhs)):
                        stack.pop()
                        if sem_stack:
                            node.children.insert(0, sem_stack.pop())

                if prod_idx == 0:
                    if trace:
                        trace_steps[-1]['action'] = 'ACCEPT'
                        trace_steps[-1]['detail'] = "accept"
                    result = sem_stack[0] if sem_stack else node.children[0] if node.children else node
                    if trace:
                        return result, self.errors, trace_steps
                    return result, self.errors

                top_state = stack[-1]
                goto_state = self.goto.get(top_state, {}).get(lhs)
                if goto_state is None:
                    self.errors.append(
                        f"Internal error: no GOTO in state {top_state} for {lhs}"
                    )
                    if trace:
                        return None, self.errors, trace_steps
                    return None, self.errors

                if trace:
                    trace_steps[-1]['detail'] += f"  → GOTO({top_state}, {lhs}) = {goto_state}"

                stack.append(goto_state)
                sem_stack.append(node)

            elif action_type == 'accept':
                if trace:
                    trace_steps[-1]['action'] = 'ACCEPT'
                    trace_steps[-1]['detail'] = "accept"
                result = sem_stack[0] if sem_stack else None
                if trace:
                    return result, self.errors, trace_steps
                return result, self.errors

            step_num += 1

        self.errors.append("Parsing ended without reaching accept state")
        result = sem_stack[0] if sem_stack else None
        if trace:
            return result, self.errors, trace_steps
        return result, self.errors


# ── LR Step Trace Formatting ─────────────────────────────────────────

def format_lr_trace(trace_steps):
    """Format LR parsing trace steps as an ASCII table."""
    lines = []
    sep = "=" * 120
    lines.append(sep)
    lines.append(f"{'LR 移进-归约 步骤输出':^116s}")
    lines.append("-" * 120)
    lines.append(f"{'Step':>5s} {'State Stack':>30s} {'Input':<35s} {'Action':>8s} {'Detail'}")
    lines.append("-" * 120)

    for step in trace_steps:
        stack_str = ' '.join(str(s) for s in step['stack'][-8:])
        if len(step['stack']) > 8:
            stack_str = '...' + stack_str[-40:]
        input_str = step['input_tokens']
        action = step.get('action', '?')
        detail = step.get('detail', '')

        lines.append(
            f"  {step['step']:3d} "
            f"[{stack_str:>28s}] "
            f"{input_str:<35s} "
            f"{action:>8s} "
            f"{detail}"
        )

    lines.append(sep)
    lines.append(f"  Total steps: {len(trace_steps)}")
    return "\n".join(lines)


def lr_trace_to_dict(trace_steps):
    """Export LR trace as a list of structured dicts (for JSON)."""
    result = []
    for step in trace_steps:
        result.append({
            'step': step['step'],
            'stack': list(step['stack']),
            'input_tokens': step['input_tokens'],
            'lookahead': step['lookahead'],
            'lookahead_value': step['lookahead_value'],
            'action': step.get('action', '?'),
            'detail': step.get('detail', ''),
        })
    return result


def lr_trace_to_json(trace_steps, indent=2):
    """Export LR trace as JSON string."""
    import json
    return json.dumps(lr_trace_to_dict(trace_steps), ensure_ascii=False, indent=indent)


# ── Graphviz DOT visualization ──────────────────────────────────────
_NODE_COUNTER = 0


def _reset_counter():
    global _NODE_COUNTER
    _NODE_COUNTER = 0


def _next_id():
    global _NODE_COUNTER
    _NODE_COUNTER += 1
    return f"n{_NODE_COUNTER}"


def tree_to_dot(tree: SyntaxTreeNode) -> str:
    """Convert LR syntax tree to Graphviz DOT format string."""
    _reset_counter()
    lines = ['digraph SyntaxTree {',
             '  rankdir=TB;',
             '  node [shape=box, style=filled, fontname="Courier New", fontsize=11];']

    def _walk(node, parent_id=None):
        nid = _next_id()
        if node.children:
            fill = '#E8F0FE'
        elif node.label in ('id',):
            fill = '#FFF3CD'
        elif node.label in ('num',):
            fill = '#D4EDDA'
        elif node.label in ('+', '-', '*', '/', ':=', '=', '#', '<', '<=', '>', '>=', 'odd'):
            fill = '#F8D7DA'
        else:
            fill = '#E2E3E5'

        label = node.label
        if node.value:
            label = f"{node.label}\\n{node.value}"
        lines.append(f'  {nid} [label="{label}", fillcolor="{fill}"];')
        if parent_id:
            lines.append(f'  {parent_id} -> {nid};')
        for child in node.children:
            _walk(child, nid)

    _walk(tree)
    lines.append('}')
    return '\n'.join(lines)


def render_tree(tree: SyntaxTreeNode, filepath="parse_tree"):
    """Render the syntax tree as a PNG image using Graphviz.

    Args:
        tree: root of the SyntaxTreeNode tree
        filepath: output file path without extension
    """
    try:
        import graphviz
        dot_source = tree_to_dot(tree)
        graph = graphviz.Source(dot_source)
        graph.render(filepath, format="png", cleanup=True)
        print(f"Syntax tree image saved as {filepath}.png")
    except ImportError:
        print("graphviz Python package not installed. Skipping tree rendering.")
    except Exception as e:
        print(f"Could not render syntax tree: {e}")


def print_tree(tree: SyntaxTreeNode, indent=0):
    """Text-based tree printer."""
    if tree is None:
        print("(null tree)")
        return
    prefix = "  " * indent
    val = f" [{tree.value}]" if tree.value else ""
    print(f"{prefix}{tree.label}{val}")
    for child in tree.children:
        print_tree(child, indent + 1)


# ── CSV export utilities ─────────────────────────────────────────────

def save_trace_csv(trace_steps, filepath, delimiter=','):
    """Save parsing trace steps to a CSV file.

    Args:
        trace_steps: list of dicts from parse_with_trace()
        filepath: output CSV path
        delimiter: column separator, default ','
    """
    dirname = os.path.dirname(filepath)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=delimiter)
        # Header
        writer.writerow(['Step', 'State Stack', 'Input', 'Action', 'Detail'])
        for step in trace_steps:
            stack_str = ' '.join(str(s) for s in step['stack'])
            writer.writerow([
                step['step'],
                stack_str,
                step['input_tokens'],
                step.get('action', '?'),
                step.get('detail', '')
            ])
    print(f"Trace steps saved as CSV: {filepath}")


def save_errors_csv(errors, filepath, delimiter=','):
    """Save error/warning list to a CSV file.

    Args:
        errors: list of error strings
        filepath: output CSV path
        delimiter: column separator, default ','
    """
    if not errors:
        return
    dirname = os.path.dirname(filepath)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(['Index', 'Message'])
        for idx, msg in enumerate(errors, 1):
            writer.writerow([idx, msg])
    print(f"Errors saved as CSV: {filepath}")


# ── Main test / demo ─────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    from ..utils.output_manager import resolve_output_path, tee_output

    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            source = f.read()
        output_path = resolve_output_path(sys.argv[1])
    else:
        source = 'const n=10; var x; begin x:=n; write(x) end.'
        print(f"Usage: python -m src.parser_lr.lr_parser <source_file>")
        print(f"Using built-in test:\n---\n{source}\n---\n")
        output_path = None

    # Parse with trace
    lexer = Lexer(source)
    parser = LRParser(lexer)
    tree, errors, trace_steps = parser.parse_with_trace()

    # Print trace (mirrored to file via tee)
    with tee_output(output_path):
        print(format_lr_trace(trace_steps))

        if errors:
            for e in errors:
                print(f"  [ERROR] {e}")

        print("\nSyntax tree:")
        print_tree(tree)

    # Determine output directory: correct/ or error/
    base_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'output')

    # Check if there are real parsing errors (excluding grammar warnings)
    real_errors = [e for e in errors if not e.startswith("Warning (grammar):")]
    subdir = 'error' if real_errors else 'correct'
    out_dir = os.path.join(base_dir, subdir)

    # Save trace CSV
    trace_csv = os.path.join(out_dir, 'trace.csv')
    save_trace_csv(trace_steps, trace_csv)

    # Save errors CSV (if any real parsing errors, excluding grammar warnings)
    if real_errors:
        errors_csv = os.path.join(out_dir, 'errors.csv')
        save_errors_csv(errors, errors_csv)

    # Save parse tree image
    if tree:
        tree_path = os.path.join(out_dir, 'parse_tree')
        render_tree(tree, tree_path)