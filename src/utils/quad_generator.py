# src/semantic_ll/quad_generator.py
"""Quadruple (three-address code) generator for PL/0.

Quad format: (op, arg1, arg2, result)
- op: operation name string
- arg1, arg2: operands (None if unused)
- result: destination
"""


class Quad:
    """A single quadruple."""
    def __init__(self, op, arg1=None, arg2=None, result=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result

    def __repr__(self):
        a1 = str(self.arg1) if self.arg1 is not None else '_'
        a2 = str(self.arg2) if self.arg2 is not None else '_'
        r = str(self.result) if self.result is not None else '_'
        return f"({self.op:8s}, {a1:>6s}, {a2:>6s}, {r:>6s})"


class QuadGenerator:
    """Generates and manages quadruples."""

    def __init__(self):
        self.quads = []
        self.next_temp = 0
        self.next_label = 0

    def new_temp(self):
        """Generate a new temporary variable name."""
        t = f"T{self.next_temp}"
        self.next_temp += 1
        return t

    def new_label(self):
        """Generate a new label."""
        l = f"L{self.next_label}"
        self.next_label += 1
        return l

    def emit(self, op, arg1=None, arg2=None, result=None):
        """Emit a quad and return its index."""
        q = Quad(op, arg1, arg2, result)
        self.quads.append(q)
        return len(self.quads) - 1

    def backpatch(self, quad_indices, label):
        """Fill in label as the result operand for a list of quads."""
        if not isinstance(quad_indices, list):
            quad_indices = [quad_indices]
        for idx in quad_indices:
            self.quads[idx].result = label

    def merge_lists(self, *lists):
        """Merge multiple backpatch lists."""
        result = []
        for lst in lists:
            if lst:
                result.extend(lst)
        return result

    def get_next_quad_index(self):
        """Return the index of the next quad to be emitted."""
        return len(self.quads)

    def display(self):
        """Pretty-print all quads."""
        print("\n" + "=" * 70)
        print("QUADRUPLE CODE (Three-Address Code)")
        print("-" * 50)
        if not self.quads:
            print("  (empty)")
        for i, q in enumerate(self.quads):
            print(f"  {i:3d}: {q}")
        print("=" * 70)

    def to_lines(self):
        """Return list of string representations (for file output)."""
        return [f"{i:3d}: {q}" for i, q in enumerate(self.quads)]


# ── Quad execution (virtual machine) for visualization ─────────────
class QuadVM:
    """Simple VM to visualize quad execution, including control flow and temps."""

    def __init__(self, quads, input_values=None):
        self.quads = quads
        self.input_values = input_values or []
        self.input_idx = 0
        self.vars = {}
        self.pc = 0
        self.trace = []  # (pc, quad, vars_snapshot)

    def run(self, max_steps=200):
        """Execute quads with tracing. Returns trace."""
        steps = 0
        while self.pc < len(self.quads) and steps < max_steps:
            q = self.quads[self.pc]
            self.trace.append((self.pc, q, dict(self.vars)))
            steps += 1

            op = q.op
            if op == 'const':
                self.vars[q.result] = q.arg1
                self.pc += 1
            elif op == 'assign':
                val = self._get_val(q.arg1)
                self.vars[q.result] = val
                self.pc += 1
            elif op in ('+', '-', '*', '/'):
                a1 = self._get_val(q.arg1)
                a2 = self._get_val(q.arg2)
                if op == '+':
                    self.vars[q.result] = a1 + a2
                elif op == '-':
                    self.vars[q.result] = a1 - a2
                elif op == '*':
                    self.vars[q.result] = a1 * a2
                elif op == '/':
                    self.vars[q.result] = a1 // a2 if a2 != 0 else 0
                self.pc += 1
            elif op in ('neg',):
                a1 = self._get_val(q.arg1)
                self.vars[q.result] = -a1
                self.pc += 1
            elif op == 'odd':
                a1 = self._get_val(q.arg1)
                self.vars[q.result] = 1 if a1 % 2 != 0 else 0
                self.pc += 1
            elif op in ('j=', 'j#', 'j<', 'j<=', 'j>', 'j>=', 'j!='):
                a1 = self._get_val(q.arg1)
                a2 = self._get_val(q.arg2)
                cond = False
                if op == 'j=':
                    cond = a1 == a2
                elif op == 'j#':
                    cond = a1 != a2
                elif op == 'j<':
                    cond = a1 < a2
                elif op == 'j<=':
                    cond = a1 <= a2
                elif op == 'j>':
                    cond = a1 > a2
                elif op == 'j>=':
                    cond = a1 >= a2
                elif op == 'j!=':
                    cond = a1 != a2
                if cond:
                    self.pc = self._find_label(q.result)
                else:
                    self.pc += 1
            elif op == 'jump':
                self.pc = self._find_label(q.result)
            elif op == 'label':
                self.pc += 1  # no-op
            elif op == 'read':
                if self.input_idx < len(self.input_values):
                    self.vars[q.result] = self.input_values[self.input_idx]
                    self.input_idx += 1
                else:
                    self.vars[q.result] = 0
                self.pc += 1
            elif op == 'write':
                val = self._get_val(q.result)
                self.pc += 1
                # Actual writes are accumulated in trace
            elif op == 'call':
                # For simplicity, just pass
                self.pc += 1
            elif op == 'ret':
                self.pc += 1  # handled externally
            else:
                self.pc += 1

        return self.trace

    def _get_val(self, arg):
        if arg is None:
            return 0
        if isinstance(arg, (int, float)):
            return arg
        return self.vars.get(arg, 0)

    def _find_label(self, label):
        for i, q in enumerate(self.quads):
            if q.op == 'label' and q.result == label:
                return i
        return self.pc + 1

    def trace_to_text(self):
        """Return human-readable trace."""
        lines = []
        for pc, q, vars_snap in self.trace:
            lines.append(f"  [{pc:3d}] {q}   // vars={dict(vars_snap)}")
        return lines
