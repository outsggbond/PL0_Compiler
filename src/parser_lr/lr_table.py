# src/parser_lr/lr_table.py
"""SLR(1) parse table construction from LR(0) items and FOLLOW sets."""

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
    """Build SLR(1) ACTION and GOTO tables.

    Returns (action, goto, conflicts):
      action[state][terminal] = ('shift', next_state) | ('reduce', prod_idx) | ('accept',)
      goto[state][nonterminal] = next_state
      conflicts: list of conflict descriptions
    """
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


def print_slr_table(action, goto):
    """Pretty-print the SLR table."""
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

    # Header
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


if __name__ == '__main__':
    # Compute FOLLOW sets from the LL grammar (reuse)
    import sys
    sys.path.insert(0, '..')
    from src.parser_ll.first_follow import compute_first, compute_follow, PRODUCTIONS as LL_PRODS

    first = compute_first()
    follow = compute_follow(first)

    # Add FOLLOW for LR-specific non-terminals
    follow['S\''] = {TT.EOF}
    follow['ConstRest'] = follow.get('ConstDecl', set())
    follow['VarRest'] = follow.get('VarDecl', set())
    follow['StmtList'] = follow.get('Statement', set()) | {TT.END}
    follow['Sign'] = first.get('Term', set())
    follow['TermList'] = follow.get('Expression', set())
    follow['FactorList'] = follow.get('Term', set())

    C, transitions = build_canonical_collection()
    action, goto, conflicts = build_slr_table(C, transitions, follow)

    print(f"Canonical collection: {len(C)} states")
    if conflicts:
        print(f"Conflicts: {len(conflicts)}")
        for c in conflicts:
            print(f"  !! {c}")
    else:
        print("No SLR(1) conflicts.")
    print()
    print_slr_table(action, goto)
