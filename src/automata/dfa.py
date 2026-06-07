# src/automata/dfa.py
"""DFA (Deterministic Finite Automaton) and NFA→DFA subset construction.

Implements:
- Subset construction algorithm: NFA → DFA
- DFA class with transition table
- Input acceptance testing
- DOT/ASCII output
"""

from collections import deque

from .nfa import NFA


class DFA:
    """A deterministic finite automaton.

    Attributes:
        states: set of state ids (int)
        alphabet: set of input symbols (str)
        transitions: dict of (state, symbol) → target state (deterministic!)
        start: start state (int)
        accepts: set of accept states (int)
        state_map: mapping from DFA state id → frozenset of NFA states (for traceability)
    """

    def __init__(self):
        self.states = set()
        self.alphabet = set()
        self.transitions = {}   # (state, symbol) → state (single target)
        self.start = 0
        self.accepts = set()
        self.state_map = {}     # DFA state → frozenset of NFA states

    def add_state(self, nfa_states=None):
        """Add a new state. Returns state id."""
        sid = len(self.states)
        while sid in self.states:
            sid += 1
        self.states.add(sid)
        if nfa_states is not None:
            self.state_map[sid] = nfa_states
        return sid

    def add_transition(self, src, symbol, dst):
        """Add a deterministic transition."""
        if symbol is not None:
            self.alphabet.add(symbol)
        self.transitions[(src, symbol)] = dst

    def accepts_input(self, input_string):
        """Test whether the DFA accepts an input string.

        Args:
            input_string: str

        Returns:
            bool
        """
        current = self.start
        for ch in input_string:
            target = self.transitions.get((current, ch))
            if target is None:
                return False
            current = target
        return current in self.accepts

    def get_dead_states(self):
        """Find all dead states (non-accepting states with no path to accept)."""
        # Reverse graph from accept states
        reachable_to_accept = set(self.accepts)
        changed = True
        while changed:
            changed = False
            for (src, sym), dst in self.transitions.items():
                if dst in reachable_to_accept and src not in reachable_to_accept:
                    reachable_to_accept.add(src)
                    changed = True
        return self.states - reachable_to_accept

    def summary(self):
        return (f"DFA(states={len(self.states)}, "
                f"alphabet={len(self.alphabet)}, "
                f"transitions={len(self.transitions)}, "
                f"accepts={len(self.accepts)})")

    def __repr__(self):
        return self.summary()


def subset_construction(nfa):
    """NFA → DFA via subset construction.

    Args:
        nfa: NFA object

    Returns:
        DFA object
    """
    dfa = DFA()
    dfa.alphabet = set(nfa.alphabet)  # copy alphabet (no epsilon)

    # DFA state 0 = epsilon-closure of NFA start
    start_set = nfa.epsilon_closure(nfa.start)
    dfa.add_state(start_set)

    # State set → DFA state id mapping
    state_to_id = {start_set: 0}
    worklist = deque([start_set])

    while worklist:
        current_set = worklist.popleft()
        current_id = state_to_id[current_set]

        # Check if this DFA state contains any NFA accept state
        if current_set & nfa.accepts:
            dfa.accepts.add(current_id)

        # For each symbol in the alphabet
        for sym in sorted(dfa.alphabet):
            # move + epsilon_closure
            moved = nfa.move(current_set, sym)
            if not moved:
                continue
            target_set = nfa.epsilon_closure(moved)
            if not target_set:
                continue

            if target_set not in state_to_id:
                new_id = dfa.add_state(target_set)
                state_to_id[target_set] = new_id
                worklist.append(target_set)

            target_id = state_to_id[target_set]
            dfa.add_transition(current_id, sym, target_id)

    return dfa


def dfa_to_dot(dfa, title="DFA"):
    """Convert DFA to Graphviz DOT format.

    Args:
        dfa: DFA object
        title: graph title

    Returns:
        str: DOT format string
    """
    lines = [
        f"// {title}",
        f"digraph DFA {{",
        '  rankdir=LR;',
        '  node [shape=circle, style=filled, fontname="Courier New", fontsize=11];',
        '  edge [fontname="Courier New", fontsize=9];',
        '',
        f'  __start [shape=point];',
        f'  __start -> {dfa.start};',
        '',
    ]

    for state in sorted(dfa.states):
        if state in dfa.accepts:
            fill = "#D4EDDA"
            shape = "doublecircle"
        elif state == dfa.start:
            fill = "#E8F0FE"
            shape = "circle"
        else:
            fill = "#FFFFFF"
            shape = "circle"

        # Show NFA state info in label
        nfa_info = ""
        if state in dfa.state_map:
            nfa_states = sorted(dfa.state_map[state])
            nfa_info = f"\\n{{{', '.join(map(str, nfa_states))}}}"

        lines.append(f'  S{state} [shape={shape}, fillcolor="{fill}", '
                     f'label="S{state}{nfa_info}"];')

    lines.append("")

    # Group transitions by (src, dst) for cleaner edges
    edge_labels = {}
    for (src, sym), dst in dfa.transitions.items():
        key = (src, dst)
        if key not in edge_labels:
            edge_labels[key] = []
        edge_labels[key].append(sym)

    for (src, dst), symbols in edge_labels.items():
        label_str = ", ".join(symbols)
        lines.append(f'  S{src} -> S{dst} [label="{label_str}"];')

    lines.append("}")
    return "\n".join(lines)


def dfa_to_ascii(dfa, title="DFA"):
    """Convert DFA to ASCII text representation.

    Args:
        dfa: DFA object
        title: table title

    Returns:
        str: ASCII formatted text
    """
    lines = []
    sep = "=" * 70
    lines.append(sep)
    lines.append(f"  {title}: {dfa.summary()}")
    lines.append("-" * 70)

    for state in sorted(dfa.states):
        marker = ""
        if state == dfa.start and state in dfa.accepts:
            marker = " (start, accept)"
        elif state == dfa.start:
            marker = " (start)"
        elif state in dfa.accepts:
            marker = " (accept)"

        nfa_info = ""
        if state in dfa.state_map:
            nfa_states = sorted(dfa.state_map[state])
            nfa_info = f"  NFA states: {{{', '.join(map(str, nfa_states))}}}"

        lines.append(f"\n  State {state}{marker}{nfa_info}")

        # Transitions from this state
        for sym in sorted(dfa.alphabet):
            target = dfa.transitions.get((state, sym))
            if target is not None:
                lines.append(f"    --'{sym}'--> S{target}")

    lines.append("")
    lines.append(sep)
    return "\n".join(lines)


# ── Test ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    from .regex_to_nfa import regex_to_nfa, build_pl0_lexer_nfas

    print("=== NFA → DFA: Subset Construction Test ===\n")

    # Test 1: a*
    pat = "a*"
    nfa = regex_to_nfa(pat)
    dfa = subset_construction(nfa)
    print(f"  regex '{pat:15s}' → {nfa.summary()} → {dfa.summary()}")
    print(f"  accepts '': {dfa.accepts_input('')}, "
          f"'a': {dfa.accepts_input('a')}, "
          f"'aaa': {dfa.accepts_input('aaa')}, "
          f"'b': {dfa.accepts_input('b')}")

    # Test 2: a(b|c)*
    pat = "a(b|c)*"
    nfa = regex_to_nfa(pat)
    dfa = subset_construction(nfa)
    print(f"\n  regex '{pat:15s}' → {nfa.summary()} → {dfa.summary()}")
    print(f"  accepts 'a': {dfa.accepts_input('a')}, "
          f"'abcbc': {dfa.accepts_input('abcbc')}, "
          f"'abx': {dfa.accepts_input('abx')}")

    # Test 3: identifier [a-z][a-z0-9]*
    print("\n  === Identifier [a-z][a-z0-9]* ===")
    pat = "[a-z][a-z0-9]*"
    nfa = regex_to_nfa(pat)
    dfa = subset_construction(nfa)
    print(f"  regex '{pat:15s}' → {nfa.summary()} → {dfa.summary()}")
    print(f"  accepts 'x': {dfa.accepts_input('x')}, "
          f"'abc': {dfa.accepts_input('abc')}, "
          f"'x1': {dfa.accepts_input('x1')}, "
          f"'1x': {dfa.accepts_input('1x')}")

    # Test 4: number [0-9]+
    print("\n  === Number [0-9]+ ===")
    pat = "[0-9]+"
    nfa = regex_to_nfa(pat)
    dfa = subset_construction(nfa)
    print(f"  regex '{pat:15s}' → {nfa.summary()} → {dfa.summary()}")
    print(f"  accepts '123': {dfa.accepts_input('123')}, "
          f"'0': {dfa.accepts_input('0')}, "
          f"'': {dfa.accepts_input('')}, "
          f"'abc': {dfa.accepts_input('abc')}")

    # DOT output for identifier DFA
    print("\n=== DOT output (identifier DFA) ===")
    nfa_id = regex_to_nfa("[a-z][a-z0-9]*")
    dfa_id = subset_construction(nfa_id)
    print(dfa_to_dot(dfa_id, "Identifier DFA"))
