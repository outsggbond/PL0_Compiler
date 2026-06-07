# src/automata/nfa.py
"""NFA (Nondeterministic Finite Automaton) with epsilon transitions.

Core data structure for the Regex→NFA→DFA→MinDFA pipeline.
Supports:
- Epsilon closure computation
- Move operation (single-character transition)
- DOT/ASCII visualization hooks
"""


class NFA:
    """A nondeterministic finite automaton, possibly with epsilon transitions.

    Attributes:
        states: set of state ids (int)
        alphabet: set of input symbols (str)
        transitions: dict of (state, symbol) → set of target states
                     symbol=None represents epsilon
        start: start state (int)
        accepts: set of accept states (int)
    """

    def __init__(self):
        self.states = set()
        self.alphabet = set()
        self.transitions = {}   # (state, symbol) → set of target states
        self.start = 0
        self.accepts = set()

    def add_state(self):
        """Add a new state and return its id."""
        sid = len(self.states)
        while sid in self.states:
            sid += 1
        self.states.add(sid)
        return sid

    def add_transition(self, src, symbol, dst):
        """Add a transition: src --symbol--> dst. symbol=None means epsilon."""
        if symbol is not None:
            self.alphabet.add(symbol)
        key = (src, symbol)
        if key not in self.transitions:
            self.transitions[key] = set()
        self.transitions[key].add(dst)

    def epsilon_closure(self, states):
        """Compute epsilon-closure of a set of states (or single state).

        Args:
            states: int or set of int

        Returns:
            frozenset of state ids reachable via epsilon transitions
        """
        if isinstance(states, int):
            states = {states}

        result = set(states)
        stack = list(states)

        while stack:
            s = stack.pop()
            eps_targets = self.transitions.get((s, None), set())
            for t in eps_targets:
                if t not in result:
                    result.add(t)
                    stack.append(t)

        return frozenset(result)

    def move(self, states, symbol):
        """Compute the set of states reachable from `states` on `symbol`.

        Args:
            states: set of state ids
            symbol: input character (not epsilon)

        Returns:
            frozenset of target states
        """
        result = set()
        for s in states:
            targets = self.transitions.get((s, symbol), set())
            result.update(targets)
        return frozenset(result)

    def accepts_input(self, input_string):
        """Test whether the NFA accepts an input string (simulate with epsilon-closure).

        Args:
            input_string: str

        Returns:
            bool
        """
        current = self.epsilon_closure(self.start)
        for ch in input_string:
            if ch not in self.alphabet:
                return False
            current = self.epsilon_closure(self.move(current, ch))
        return bool(current & self.accepts)

    def rename_states(self, mapping=None):
        """Rename states (in-place). Useful after construction."""
        if mapping is None:
            # Identity mapping
            return
        old_states = set(self.states)
        self.states = {mapping.get(s, s) for s in old_states}
        self.start = mapping.get(self.start, self.start)
        self.accepts = {mapping.get(s, s) for s in self.accepts}

        new_trans = {}
        for (src, sym), targets in self.transitions.items():
            new_src = mapping.get(src, src)
            new_targets = {mapping.get(t, t) for t in targets}
            new_trans[(new_src, sym)] = new_targets
        self.transitions = new_trans

    def summary(self):
        """Return a summary string."""
        return (f"NFA(states={len(self.states)}, "
                f"alphabet={len(self.alphabet)}, "
                f"transitions={sum(len(v) for v in self.transitions.values())}, "
                f"accepts={len(self.accepts)})")

    def __repr__(self):
        return self.summary()


# ── Thompson Construction: basic building blocks ─────────────────────

def build_nfa_single_char(char):
    """Build NFA for a single character: a.

    Returns: NFA with states 0(start)→a→1(accept)
    """
    nfa = NFA()
    s0 = nfa.add_state()
    s1 = nfa.add_state()
    nfa.start = s0
    nfa.accepts = {s1}
    nfa.add_transition(s0, char, s1)
    return nfa


def build_nfa_epsilon():
    """Build NFA for epsilon (empty string).

    Returns: NFA with states 0(start/accept)
    """
    nfa = NFA()
    s0 = nfa.add_state()
    nfa.start = s0
    nfa.accepts = {s0}
    return nfa


def build_nfa_concat(nfa1, nfa2):
    """Concatenate two NFAs: nfa1 . nfa2.

    Merges nfa1's accept states with nfa2's start via epsilon transitions.
    """
    nfa = NFA()
    offset1 = 0                       # nfa1 starts at 0
    offset2 = len(nfa1.states)         # nfa2 starts after nfa1

    for s in nfa1.states:
        nfa.states.add(s + offset1)
    for s in nfa2.states:
        nfa.states.add(s + offset2)

    # Copy transitions
    for (src, sym), targets in nfa1.transitions.items():
        for t in targets:
            nfa.add_transition(src + offset1, sym, t + offset1)
    for (src, sym), targets in nfa2.transitions.items():
        for t in targets:
            nfa.add_transition(src + offset2, sym, t + offset2)

    nfa.start = nfa1.start + offset1
    nfa.accepts = {s + offset2 for s in nfa2.accepts}

    # Epsilon from nfa1 accepts to nfa2 start
    for a in nfa1.accepts:
        nfa.add_transition(a + offset1, None, nfa2.start + offset2)

    return nfa


def build_nfa_union(nfa1, nfa2):
    """Union of two NFAs: nfa1 | nfa2.

    Creates new start with epsilon transitions to both nfa1.start and nfa2.start.
    """
    nfa = NFA()
    offset1 = 1                       # new start is 0, nfa1 starts at 1
    offset2 = offset1 + len(nfa1.states)  # nfa2 starts after nfa1

    s0 = nfa.add_state()  # new start, id = 0
    nfa.start = s0

    for s in nfa1.states:
        nfa.states.add(s + offset1)
    for s in nfa2.states:
        nfa.states.add(s + offset2)

    # Copy transitions
    for (src, sym), targets in nfa1.transitions.items():
        for t in targets:
            nfa.add_transition(src + offset1, sym, t + offset1)
    for (src, sym), targets in nfa2.transitions.items():
        for t in targets:
            nfa.add_transition(src + offset2, sym, t + offset2)

    # Epsilon from new start to both old starts
    nfa.add_transition(s0, None, nfa1.start + offset1)
    nfa.add_transition(s0, None, nfa2.start + offset2)

    # Union of accept states
    nfa.accepts = {s + offset1 for s in nfa1.accepts} | {s + offset2 for s in nfa2.accepts}

    return nfa


def build_nfa_kleene_star(nfa_in):
    """Kleene star: nfa_in*.

    Creates new start (also accept) with epsilon to old start,
    and epsilon from old accepts back to old start.
    """
    nfa = NFA()
    offset = 1  # new start is 0, old states start at 1

    s0 = nfa.add_state()  # new start, id = 0
    nfa.start = s0
    nfa.accepts.add(s0)   # new start is also accept (zero repetitions)

    for s in nfa_in.states:
        nfa.states.add(s + offset)

    for (src, sym), targets in nfa_in.transitions.items():
        for t in targets:
            nfa.add_transition(src + offset, sym, t + offset)

    # Epsilon from new start to old start
    nfa.add_transition(s0, None, nfa_in.start + offset)

    # Epsilon from old accepts back to old start (loop)
    for a in nfa_in.accepts:
        nfa.add_transition(a + offset, None, nfa_in.start + offset)

    # Old accepts remain as accepts
    for a in nfa_in.accepts:
        nfa.accepts.add(a + offset)

    return nfa


def build_nfa_plus(nfa_in):
    """One or more: nfa_in+ (equivalent to nfa_in · nfa_in*).

    Returns: NFA
    """
    return build_nfa_concat(nfa_in, build_nfa_kleene_star(nfa_in))
