# src/automata/dfa_minimizer.py
"""DFA 最小化 (Hopcroft 算法)

Implements Hopcroft's DFA minimization algorithm:
- Partition refinement based on distinguishable states
- Produces the minimal DFA equivalent to the input DFA
- Handles incomplete transition functions (dead states are removed)
"""

from collections import deque

from .dfa import DFA, subset_construction
from .nfa import NFA


def hopcroft_minimize(dfa):
    """Minimize a DFA using Hopcroft's partition refinement algorithm.

    Algorithm:
    1. Initial partition: P = {F, Q-F}  (accept states, non-accept states)
       Plus an implicit "sink" state for undefined transitions.
    2. Split blocks based on whether states in a block transition to
       different blocks on the same symbol.
    3. Repeat until no more splits possible.

    Handles incomplete transition functions (undefined transitions
    are treated as going to an implicit reject sink).

    Args:
        dfa: DFA object

    Returns:
        DFA: minimized DFA
    """
    if not dfa.states:
        return dfa

    alphabet = sorted(dfa.alphabet)
    if not alphabet:
        min_dfa = DFA()
        min_dfa.alphabet = set()
        min_dfa.start = 0
        min_dfa.accepts = {0} if dfa.start in dfa.accepts else set()
        min_dfa.states = {0}
        return min_dfa

    # Add a virtual sink state index for undefined transitions
    SINK_ID = -1  # represents the implicit dead/reject state

    # Step 1: Initial partition
    accept_states = frozenset(dfa.accepts)
    non_accept_states = frozenset(dfa.states - dfa.accepts)

    blocks = []
    state_to_block = {}

    # Only create blocks for non-empty sets
    if non_accept_states:
        blocks.append(non_accept_states)
        for s in non_accept_states:
            state_to_block[s] = len(blocks) - 1

    if accept_states:
        blocks.append(accept_states)
        for s in accept_states:
            state_to_block[s] = len(blocks) - 1

    # The sink block is implicitly handled: any undefined transition
    # maps to the same virtual sink, so all undefined transitions
    # are equivalent to each other.

    # Step 2: Iterative refinement
    # We need to consider that undefined transitions go to SINK,
    # and defined transitions go to their respective blocks.
    # Two states are distinguishable if on the same symbol,
    # one has a defined transition to block B and the other
    # has an undefined transition (which goes to SINK),
    # UNLESS B is the same as SINK behavior.

    worklist = deque()
    for i in range(len(blocks)):
        for sym in alphabet:
            worklist.append((i, sym))
    # Also add the sink "block" for undefined transitions
    for sym in alphabet:
        worklist.append((SINK_ID, sym))

    iteration = 0
    max_iterations = len(dfa.states) * len(alphabet) * 2

    while worklist and iteration < max_iterations:
        iteration += 1
        block_idx, sym = worklist.popleft()

        # Find which source blocks need splitting:
        # For each block, collect states whose transition on `sym`
        # goes into the splitter block `block_idx`.
        # States with undefined transitions go to SINK.

        if block_idx == SINK_ID:
            # Splitter is SINK: states with undefined transition on `sym`
            # are in the "affected" set; states with defined transitions are "unaffected"
            inverse_map = {}
            for s, b_idx in state_to_block.items():
                target = dfa.transitions.get((s, sym))
                if target is None:
                    # Goes to SINK
                    inverse_map.setdefault(b_idx, set()).add(s)
        else:
            # Splitter is a real block
            inverse_map = {}
            for s, b_idx in state_to_block.items():
                target = dfa.transitions.get((s, sym))
                if target is not None and target in state_to_block:
                    target_block = state_to_block[target]
                    if target_block == block_idx:
                        inverse_map.setdefault(b_idx, set()).add(s)

        # Process each source block that needs splitting
        for src_block_idx, affected_states in inverse_map.items():
            src_block = blocks[src_block_idx]
            unaffected = src_block - affected_states

            if not unaffected or not affected_states:
                # No split needed
                continue

            # Split: replace old block with two new blocks
            new_affected = frozenset(affected_states)
            new_unaffected = frozenset(unaffected)

            blocks[src_block_idx] = new_unaffected
            new_block_idx = len(blocks)
            blocks.append(new_affected)

            # Update state_to_block for affected states
            for s in new_affected:
                state_to_block[s] = new_block_idx

            # Add all (new_block, symbol) pairs to worklist
            for s in alphabet:
                worklist.append((new_block_idx, s))
            # Also re-add the original block's pairs (they might need re-splitting)
            for s in alphabet:
                worklist.append((src_block_idx, s))

    # Step 3: Build minimized DFA
    min_dfa = DFA()
    min_dfa.alphabet = set(alphabet)

    # Map original state → new minimized state
    old_to_new = {}

    for block_idx, block in enumerate(blocks):
        new_state = block_idx
        for s in block:
            old_to_new[s] = new_state
        min_dfa.states.add(new_state)

        if dfa.start in block:
            min_dfa.start = new_state

        if block & dfa.accepts:
            min_dfa.accepts.add(new_state)

    # Copy transitions (only for states that survived)
    for (src, sym), dst in dfa.transitions.items():
        if src in old_to_new and dst in old_to_new:
            new_src = old_to_new[src]
            new_dst = old_to_new[dst]
            min_dfa.transitions[(new_src, sym)] = new_dst

    # Store mapping info
    min_dfa.state_map = {}
    for block_idx, block in enumerate(blocks):
        min_dfa.state_map[block_idx] = block

    return min_dfa


def minimize_dfa(dfa):
    """Convenience wrapper for Hopcroft minimization.

    Args:
        dfa: DFA object

    Returns:
        DFA: minimized DFA
    """
    return hopcroft_minimize(dfa)


# ── Full pipeline: regex → NFA → DFA → min DFA ───────────────────

def regex_to_min_dfa(pattern):
    """Complete pipeline: regex → NFA → DFA → min DFA.

    Args:
        pattern: regex string

    Returns:
        tuple of (NFA, DFA, min_DFA)
    """
    from .regex_to_nfa import regex_to_nfa

    nfa = regex_to_nfa(pattern)
    dfa = subset_construction(nfa)
    min_dfa = hopcroft_minimize(dfa)
    return nfa, dfa, min_dfa


def print_pipeline_summary(pattern):
    """Print a summary of the full Regex → NFA → DFA → min DFA pipeline.

    Args:
        pattern: regex string

    Returns:
        str: summary text
    """
    nfa, dfa, min_dfa = regex_to_min_dfa(pattern)

    lines = []
    sep = "=" * 70
    lines.append(sep)
    lines.append(f"  Pipeline: Regex → NFA → DFA → MinDFA")
    lines.append(f"  Pattern:  {pattern}")
    lines.append("-" * 70)
    lines.append(f"  NFA:     {nfa.summary()}")
    lines.append(f"  DFA:     {dfa.summary()}")
    lines.append(f"  MinDFA:  {min_dfa.summary()}")
    lines.append(f"  Reduction: {len(dfa.states)} states → {len(min_dfa.states)} states "
                 f"({len(dfa.states) - len(min_dfa.states)} removed)")
    lines.append(sep)

    return "\n".join(lines)


# ── Test ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    from .dfa import dfa_to_ascii, dfa_to_dot

    test_patterns = [
        "a*",
        "a(b|c)*",
        "[a-z][a-z0-9]*",
        "[0-9]+",
        "(a|b)*abb",
    ]

    for pat in test_patterns:
        print(print_pipeline_summary(pat))

        # Show the min DFA in ASCII
        _, _, min_dfa = regex_to_min_dfa(pat)
        print(dfa_to_ascii(min_dfa, f"MinDFA for '{pat}'"))
        print()

        # Test acceptance
        if pat == "a*":
            tests = ["", "a", "aaa", "b"]
        elif pat == "a(b|c)*":
            tests = ["a", "abcbc", "abx", ""]
        elif pat == "[a-z][a-z0-9]*":
            tests = ["x", "abc", "x1", "1x", "a1b2"]
        elif pat == "[0-9]+":
            tests = ["123", "0", "", "12a"]
        elif pat == "(a|b)*abb":
            tests = ["abb", "aabb", "babb", "ab", "abba"]
        else:
            tests = []

        for t in tests:
            result = min_dfa.accepts_input(t)
            print(f"    '{t}' → {'ACCEPT' if result else 'REJECT'}")
        print()

    # DOT output for identifier min DFA
    print("\n=== MinDFA DOT (identifier) ===")
    _, _, min_id = regex_to_min_dfa("[a-z][a-z0-9]*")
    print(dfa_to_dot(min_id, "Minimized Identifier DFA"))
