# src/parser_ll/ll_table.py
"""Build LL(1) predictive parsing table from FIRST/FOLLOW sets."""

from .first_follow import PRODUCTIONS, NONTERMINALS, TERMINALS, _sym_name, compute_first, compute_follow


def build_ll_table(first=None, follow=None):
    """Build LL(1) parse table. Returns (table, conflicts).
    table[nonterm][terminal] = production (tuple of symbols)
    """
    if first is None:
        first = compute_first()
    if follow is None:
        follow = compute_follow(first)

    table = {}
    conflicts = []

    for nt in NONTERMINALS:
        table[nt] = {}
        for alt in PRODUCTIONS[nt]:
            # Compute FIRST(alt)
            alt_first = set()
            all_nullable = True
            for sym in alt:
                if sym is None:
                    alt_first.add(None)
                    break
                sym_first = first.get(sym, {sym})
                alt_first.update(f for f in sym_first if f is not None)
                if None not in sym_first:
                    all_nullable = False
                    break
            if all_nullable:
                alt_first.add(None)

            # For each terminal in FIRST(alt), add to table
            for t in alt_first:
                if t is None:
                    # nullable — use FOLLOW(nt)
                    for f in follow.get(nt, set()):
                        existing = table[nt].get(f)
                        if existing is not None and existing != alt:
                            conflicts.append(
                                f"LL(1) conflict: {nt} on {_sym_name(f)}: "
                                f"{_format_alt(existing)} vs {_format_alt(alt)}"
                            )
                        table[nt][f] = alt
                else:
                    existing = table[nt].get(t)
                    if existing is not None and existing != alt:
                        conflicts.append(
                            f"LL(1) conflict: {nt} on {_sym_name(t)}: "
                            f"{_format_alt(existing)} vs {_format_alt(alt)}"
                        )
                    table[nt][t] = alt

    return table, conflicts


def _format_alt(alt):
    if alt is None or alt == (None,):
        return 'ε'
    return ' '.join(_sym_name(s) for s in alt if s is not None)


def print_table(table):
    """Pretty-print the LL(1) table (only used entries)."""
    terminals_used = sorted(set(
        t for nt_entries in table.values() for t in nt_entries.keys()
    ), key=_sym_name)

    print("=" * 100)
    print("LL(1) Parse Table")
    print("-" * 80)

    for nt in sorted(NONTERMINALS, key=lambda x: (x != 'Program', x)):
        entries = table.get(nt, {})
        for t in terminals_used:
            if t in entries:
                prod = entries[t]
                print(f"  M[{nt:12s}, {_sym_name(t):6s}] = {nt} → {_format_alt(prod)}")


if __name__ == '__main__':
    from .first_follow import get_first, get_follow
    f = get_first()
    fl = get_follow()
    tbl, conf = build_ll_table(f, fl)
    if conf:
        print("Conflicts found:")
        for c in conf:
            print(f"  !! {c}")
    else:
        print("No LL(1) conflicts. Grammar is LL(1).")
    print()
    print_table(tbl)
