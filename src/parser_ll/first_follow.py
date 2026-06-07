# src/parser_ll/first_follow.py
"""Compute FIRST and FOLLOW sets for the PL/0 grammar."""

from ..lexer.token import TokenType as TT

# ── Terminal sets for readable output ──────────────────────────────
T = TT  # shorthand

# ── Grammar: right-hand sides are tuples of tokens/non-terminals ───
# Non-terminals represented as strings: 'Program', 'Block', etc.
# ε is represented by None

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

# Identify non-terminals vs terminals
NONTERMINALS = set(PRODUCTIONS.keys())
# All terminals that can appear: token types that appear in production RHS
TERMINALS = set()
for prods in PRODUCTIONS.values():
    for alt in prods:
        for sym in alt:
            if sym is not None and sym not in NONTERMINALS:
                TERMINALS.add(sym)


def compute_first():
    """Compute FIRST sets for all non-terminals (and token-lookup for terminals)."""
    first = {nt: set() for nt in NONTERMINALS}
    # For terminals, FIRST(t) = {t}
    for t in TERMINALS:
        first[t] = {t}

    changed = True
    while changed:
        changed = False
        for nt, alternatives in PRODUCTIONS.items():
            for alt in alternatives:
                # If production is ε
                if alt == (None,):
                    if None not in first[nt]:
                        first[nt].add(None)
                        changed = True
                    continue
                # For each symbol in the production
                all_nullable = True
                for sym in alt:
                    if sym is None:
                        continue
                    sym_first = first.get(sym, {sym})
                    # Add everything except ε
                    for f in sym_first:
                        if f is not None and f not in first[nt]:
                            first[nt].add(f)
                            changed = True
                    # If this symbol is not nullable, stop
                    if None not in sym_first:
                        all_nullable = False
                        break
                # If all symbols are nullable, production is nullable
                if all_nullable:
                    if None not in first[nt]:
                        first[nt].add(None)
                        changed = True
    return first


def compute_follow(first):
    """Compute FOLLOW sets for all non-terminals."""
    follow = {nt: set() for nt in NONTERMINALS}
    # Start symbol gets EOF
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
                    # Everything after sym in this production
                    rest = alt[i+1:]
                    if not rest:
                        # A → αB: FOLLOW(B) ⊇ FOLLOW(A)
                        for f in follow.get(nt, set()):
                            if f not in follow[sym]:
                                follow[sym].add(f)
                                changed = True
                        continue
                    # look at FIRST(rest)
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
                    # If rest is nullable, add FOLLOW(A)
                    if all_nullable:
                        for f in follow.get(nt, set()):
                            if f not in follow[sym]:
                                follow[sym].add(f)
                                changed = True
    return follow


# ── Helper: pretty-print ────────────────────────────────────────────
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


def print_sets(first, follow):
    """Pretty-print FIRST and FOLLOW sets."""
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


# ── Module-level computation (cached on import) ────────────────────
_first = None
_follow = None


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


if __name__ == '__main__':
    f = get_first()
    fl = get_follow()
    print_sets(f, fl)
