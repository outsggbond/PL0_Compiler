# src/parser_ll/first_follow.py
"""Compute FIRST, FOLLOW, and SELECT sets for the PL/0 grammar."""

from ..lexer.token import TokenType as TT

# ── Terminal sets for readable output ──────────────────────────────
T = TT  # shorthand

# Productions: nonterm -> list of alternatives, each alternative is a tuple
PRODUCTIONS = {
    'Program': [('Block', T.PERIOD)],
    'Block': [('ConstDecl', 'VarDecl', 'ProcDecls', 'Statement')],
    'ConstDecl': [
        (T.CONST, T.ID, T.EQ, T.NUMBER, 'ConstRest', T.SEMICOLON),
    ],
    'ConstRest': [
        (T.COMMA, T.ID, T.EQ, T.NUMBER, 'ConstRest'),
        (None,),  # ε
    ],
    'VarDecl': [
        (T.VAR, T.ID, 'VarRest', T.SEMICOLON),
        (None,),  # ε — var decl is optional
    ],
    'VarRest': [
        (T.COMMA, T.ID, 'VarRest'),
        (None,),  # ε
    ],
    'ProcDecls': [
        ('ProcDecl', 'ProcDecls'),
        (None,),  # ε
    ],
    'ProcDecl': [
        (T.PROCEDURE, T.ID, T.SEMICOLON, 'Block', T.SEMICOLON),
    ],
    'Statement': [
        (T.ID, T.ASSIGN, 'Expression'),
        (T.CALL, T.ID),
        (T.BEGIN, 'Statement', 'StmtList', T.END),
        (T.IF, 'Condition', T.THEN, 'Statement'),
        (T.WHILE, 'Condition', T.DO, 'Statement'),
        (T.READ, T.LPAREN, T.ID, T.RPAREN),
        (T.WRITE, T.LPAREN, 'Expression', T.RPAREN),
        (None,),  # ε (empty statement)
    ],
    'StmtList': [
        (T.SEMICOLON, 'Statement', 'StmtList'),
        (None,),  # ε
    ],
    'Condition': [
        (T.ODD, 'Expression'),
        ('Expression', 'RelOp', 'Expression'),
    ],
    'RelOp': [
        (T.EQ,), (T.NE,), (T.LT,), (T.LE,), (T.GT,), (T.GE,),
    ],
    'Expression': [
        ('Sign', 'Term', 'TermList'),
    ],
    'Sign': [
        (T.PLUS,), (T.MINUS,), (None,),  # ε
    ],
    'TermList': [
        (T.PLUS, 'Term', 'TermList'),
        (T.MINUS, 'Term', 'TermList'),
        (None,),  # ε
    ],
    'Term': [
        ('Factor', 'FactorList'),
    ],
    'FactorList': [
        (T.TIMES, 'Factor', 'FactorList'),
        (T.DIV, 'Factor', 'FactorList'),
        (None,),  # ε
    ],
    'Factor': [
        (T.ID,),
        (T.NUMBER,),
        (T.LPAREN, 'Expression', T.RPAREN),
    ],
}

NONTERMINALS = set(PRODUCTIONS.keys())
TERMINALS = set()
for prods in PRODUCTIONS.values():
    for alt in prods:
        for sym in alt:
            if sym is not None and sym not in NONTERMINALS:
                TERMINALS.add(sym)


# ── Token name mapping ───────────────────────────────────────────
_TNAME = {
    T.CONST: 'const', T.VAR: 'var', T.PROCEDURE: 'procedure',
    T.BEGIN: 'begin', T.END: 'end', T.IF: 'if', T.THEN: 'then',
    T.WHILE: 'while', T.DO: 'do', T.CALL: 'call', T.READ: 'read',
    T.WRITE: 'write', T.ODD: 'odd',
    T.PLUS: '+', T.MINUS: '-', T.TIMES: '*', T.DIV: '/',
    T.ASSIGN: ':=', T.EQ: '=', T.NE: '#', T.LT: '<', T.LE: '<=',
    T.GT: '>', T.GE: '>=',
    T.LPAREN: '(', T.RPAREN: ')', T.SEMICOLON: ';',
    T.COMMA: ',', T.PERIOD: '.',
    T.ID: 'id', T.NUMBER: 'num', T.EOF: '$',
}


def _sym_name(s):
    if s is None:
        return 'eps'
    if isinstance(s, str):
        return s
    return _TNAME.get(s, s.name)


# ── FIRST sets ──────────────────────────────────────────────────

def compute_first():
    """Compute FIRST sets for all non-terminals."""
    first = {nt: set() for nt in NONTERMINALS}
    for t in TERMINALS:
        first[t] = {t}

    changed = True
    while changed:
        changed = False
        for nt, alternatives in PRODUCTIONS.items():
            for alt in alternatives:
                if alt == (None,):
                    if None not in first[nt]:
                        first[nt].add(None)
                        changed = True
                    continue
                all_nullable = True
                for sym in alt:
                    if sym is None:
                        continue
                    sym_first = first.get(sym, {sym})
                    for f in sym_first:
                        if f is not None and f not in first[nt]:
                            first[nt].add(f)
                            changed = True
                    if None not in sym_first:
                        all_nullable = False
                        break
                if all_nullable:
                    if None not in first[nt]:
                        first[nt].add(None)
                        changed = True
    return first


# ── FOLLOW sets ─────────────────────────────────────────────────

def compute_follow(first):
    """Compute FOLLOW sets for all non-terminals."""
    follow = {nt: set() for nt in NONTERMINALS}
    follow['Program'].add(T.EOF)

    changed = True
    while changed:
        changed = False
        for nt, alternatives in PRODUCTIONS.items():
            for alt in alternatives:
                if alt == (None,):
                    continue
                for i, sym in enumerate(alt):
                    if sym is None or sym not in NONTERMINALS:
                        continue
                    rest = alt[i+1:]
                    if not rest:
                        for f in follow.get(nt, set()):
                            if f not in follow[sym]:
                                follow[sym].add(f)
                                changed = True
                        continue
                    all_nullable = True
                    for r in rest:
                        if r is None:
                            continue
                        r_first = first.get(r, {r})
                        for f in r_first:
                            if f is not None and f not in follow[sym]:
                                follow[sym].add(f)
                                changed = True
                        if None not in r_first:
                            all_nullable = False
                            break
                    if all_nullable:
                        for f in follow.get(nt, set()):
                            if f not in follow[sym]:
                                follow[sym].add(f)
                                changed = True
    return follow


# ── SELECT sets ─────────────────────────────────────────────────

def compute_select(first, follow):
    """Compute SELECT sets for all productions.

    SELECT(A → α):
    - If ε ∉ FIRST(α): SELECT = FIRST(α)
    - If ε ∈ FIRST(α): SELECT = (FIRST(α) - {ε}) ∪ FOLLOW(A)
    """
    select = {}
    for nt, alternatives in PRODUCTIONS.items():
        for alt in alternatives:
            first_alpha = set()
            all_nullable = True

            if alt == (None,):
                first_alpha.add(None)
            else:
                for sym in alt:
                    if sym is None:
                        first_alpha.add(None)
                        break
                    sym_first = first.get(sym, {sym})
                    for f in sym_first:
                        if f is not None:
                            first_alpha.add(f)
                    if None not in sym_first:
                        all_nullable = False
                        break
                if all_nullable:
                    first_alpha.add(None)

            if None in first_alpha:
                select_set = (first_alpha - {None}) | follow.get(nt, set())
            else:
                select_set = first_alpha.copy()

            select[(nt, alt)] = select_set

    return select


def check_ll1_condition(select):
    """Verify SELECT sets are disjoint for each nonterminal."""
    issues = []
    for nt in sorted(NONTERMINALS):
        alternatives = PRODUCTIONS[nt]
        if len(alternatives) <= 1:
            continue
        sel_sets = [select.get((nt, alt), set()) for alt in alternatives]
        for i in range(len(sel_sets)):
            for j in range(i + 1, len(sel_sets)):
                inter = sel_sets[i] & sel_sets[j]
                if inter:
                    alt_i = ' '.join(_sym_name(s) for s in alternatives[i]) if alternatives[i] != (None,) else 'eps'
                    alt_j = ' '.join(_sym_name(s) for s in alternatives[j]) if alternatives[j] != (None,) else 'eps'
                    common = ', '.join(_sym_name(s) for s in sorted(inter, key=_sym_name))
                    issues.append(
                        f"  !! {nt}: SELECT({alt_i}) / SELECT({alt_j}) "
                        f"= {{ {common} }}"
                    )
    return issues


# ── Pretty-print functions ──────────────────────────────────────

def print_sets(first, follow):
    """Print FIRST and FOLLOW sets."""
    print("=" * 60)
    print("FIRST sets:")
    print("-" * 40)
    for nt in sorted(NONTERMINALS, key=lambda x: (x != 'Program', x)):
        items = sorted(first.get(nt, []), key=lambda x: (_sym_name(x) if x is not None else 'eps'))
        items_str = ', '.join(_sym_name(f) for f in items)
        print(f"  FIRST({nt:12s}) = {{ {items_str} }}")

    print()
    print("FOLLOW sets:")
    print("-" * 40)
    for nt in sorted(NONTERMINALS, key=lambda x: (x != 'Program', x)):
        items = sorted(follow.get(nt, []), key=lambda x: _sym_name(x))
        items_str = ', '.join(_sym_name(f) for f in items)
        print(f"  FOLLOW({nt:12s}) = {{ {items_str} }}")


def print_select_sets(select):
    """Print SELECT sets for all productions."""
    print("=" * 80)
    print("SELECT sets (LL(1) prediction table):")
    print("-" * 80)

    for (nt, alt), sel_set in sorted(select.items(), key=lambda x: (x[0][0], len(x[0][1]))):
        rhs_str = ' '.join(_sym_name(s) for s in alt) if alt and alt != (None,) else 'eps'
        items = sorted(sel_set, key=lambda x: _sym_name(x))
        sel_str = '{ ' + ', '.join(_sym_name(s) for s in items) + ' }'
        print(f"  SELECT({nt:12s} → {rhs_str:40s}) = {sel_str}")

    print("=" * 80)

    # LL(1) check
    print("\nLL(1) Grammar Check:")
    print("-" * 40)
    issues = check_ll1_condition(select)
    if issues:
        for issue in issues:
            print(issue)
        print(f"\n  Result: Grammar is NOT LL(1) ({len(issues)} conflicts)")
    else:
        print("  All SELECT sets are pairwise disjoint.")
        print("  Result: Grammar IS LL(1)")
    print("-" * 40)


def print_ll1_table(select):
    """Print the LL(1) prediction table."""
    all_terminals = set()
    for sel_set in select.values():
        all_terminals |= sel_set
    all_terminals = sorted(all_terminals, key=_sym_name)
    nonterminals = sorted(NONTERMINALS)

    print("\n" + "=" * 120)
    print("LL(1) Prediction Table:")
    print("-" * 120)

    header = f"{'NT':>15s} |"
    for t in all_terminals:
        header += f" {_sym_name(t):>8s} |"
    print(header)
    print("-" * len(header))

    for nt in nonterminals:
        row = f"{nt:>15s} |"
        for t in all_terminals:
            entry = ""
            for (nt_key, alt), sel_set in select.items():
                if nt_key == nt and t in sel_set:
                    rhs_str = ' '.join(_sym_name(s) for s in alt) if alt and alt != (None,) else 'eps'
                    entry = rhs_str[:8]
                    break
            row += f" {entry:>8s} |"
        print(row)

    print("=" * 120)


# ── Cached access ───────────────────────────────────────────────

_first = None
_follow = None
_select = None


def get_first():
    global _first
    if _first is None:
        _first = compute_first()
    return _first


def get_follow():
    global _follow, _first
    if _follow is None:
        _first = get_first()
        _follow = compute_follow(_first)
    return _follow


def get_select():
    global _select
    if _select is None:
        _select = compute_select(get_first(), get_follow())
    return _select


# ── Test ────────────────────────────────────────────────────────

if __name__ == '__main__':
    f = get_first()
    fl = get_follow()
    sel = get_select()

    print_sets(f, fl)
    print()
    print_select_sets(sel)
    print()
    print_ll1_table(sel)
