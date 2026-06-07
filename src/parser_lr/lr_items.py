# src/parser_lr/lr_items.py
"""LR(0) items, closure, canonical collection, and GOTO for PL/0 SLR(1) parsing."""

from ..lexer.token import TokenType as TT

# ── Augmented grammar for PL/0 ──────────────────────────────────────
# Production index → (LHS: str, RHS: tuple of symbols)
# Production 0: S' → Program  (augmented start)
# Terminals: TokenType values
# Non-terminals: strings: 'Program', 'Block', 'Statement', etc.

PRODUCTIONS_LR = [
    # idx 0: augmented start
    ("S'", ('Program',)),
    # 1: Program → Block PERIOD
    ('Program', ('Block', TT.PERIOD)),
    # 2–6: Block variants
    ('Block', ('ConstDecl', 'VarDecl', 'ProcDecls', 'Statement')),
    ('Block', ('ConstDecl', 'ProcDecls', 'Statement')),             # no var
    ('Block', ('VarDecl', 'ProcDecls', 'Statement')),               # no const
    ('Block', ('ProcDecls', 'Statement')),                          # neither const nor var
    ('Block', ('Statement',)),                                      # just statement
    # 7: ConstDecl
    ('ConstDecl', (TT.CONST, TT.ID, TT.EQ, TT.NUMBER, 'ConstRest', TT.SEMICOLON)),
    # 8–9: ConstRest
    ('ConstRest', (TT.COMMA, TT.ID, TT.EQ, TT.NUMBER, 'ConstRest')),
    ('ConstRest', ()),  # ε
    # 10: VarDecl
    ('VarDecl', (TT.VAR, TT.ID, 'VarRest', TT.SEMICOLON)),
    # (VarDecl → ε removed — Block productions handle optionality)
    # 12–13: VarRest
    ('VarRest', (TT.COMMA, TT.ID, 'VarRest')),
    ('VarRest', ()),  # ε
    # 14–15: ProcDecls
    ('ProcDecls', ('ProcDecl', 'ProcDecls')),
    ('ProcDecls', ()),  # ε
    # 16: ProcDecl
    ('ProcDecl', (TT.PROCEDURE, TT.ID, TT.SEMICOLON, 'Block', TT.SEMICOLON)),
    # 17–24: Statement
    ('Statement', (TT.ID, TT.ASSIGN, 'Expression')),
    ('Statement', (TT.CALL, TT.ID)),
    ('Statement', (TT.BEGIN, 'StmtList', TT.END)),
    ('Statement', (TT.IF, 'Condition', TT.THEN, 'Statement')),
    ('Statement', (TT.WHILE, 'Condition', TT.DO, 'Statement')),
    ('Statement', (TT.READ, TT.LPAREN, TT.ID, TT.RPAREN)),
    ('Statement', (TT.WRITE, TT.LPAREN, 'Expression', TT.RPAREN)),
    # (Statement → ε removed — handle via StmtList instead)
    # 25–29: StmtList
    ('StmtList', ('Statement',)),  # single statement (last, no trailing ;)
    ('StmtList', ('Statement', TT.SEMICOLON, 'StmtList')),  # first statement + more
    ('StmtList', (TT.SEMICOLON, 'Statement', 'StmtList')),  # more statements after ;
    ('StmtList', (TT.SEMICOLON, 'StmtList')),  # empty statement between ; and ;
    ('StmtList', ()),  # ε
    # 27–28: Condition
    ('Condition', (TT.ODD, 'Expression')),
    ('Condition', ('Expression', 'RelOp', 'Expression')),
    # 29–34: RelOp
    ('RelOp', (TT.EQ,)),
    ('RelOp', (TT.NE,)),
    ('RelOp', (TT.LT,)),
    ('RelOp', (TT.LE,)),
    ('RelOp', (TT.GT,)),
    ('RelOp', (TT.GE,)),
    # 35: Expression
    ('Expression', ('Sign', 'Term', 'TermList')),
    # 36–38: Sign
    ('Sign', (TT.PLUS,)),
    ('Sign', (TT.MINUS,)),
    ('Sign', ()),  # ε
    # 39–41: TermList
    ('TermList', (TT.PLUS, 'Term', 'TermList')),
    ('TermList', (TT.MINUS, 'Term', 'TermList')),
    ('TermList', ()),  # ε
    # 42: Term
    ('Term', ('Factor', 'FactorList')),
    # 43–45: FactorList
    ('FactorList', (TT.TIMES, 'Factor', 'FactorList')),
    ('FactorList', (TT.DIV, 'Factor', 'FactorList')),
    ('FactorList', ()),  # ε
    # 46–48: Factor
    ('Factor', (TT.ID,)),
    ('Factor', (TT.NUMBER,)),
    ('Factor', (TT.LPAREN, 'Expression', TT.RPAREN)),
]

# Build lookup: nonterminal → list of production indices
NONTERM_PRODS = {}
for idx, (lhs, rhs) in enumerate(PRODUCTIONS_LR):
    NONTERM_PRODS.setdefault(lhs, []).append(idx)

NONTERMINALS_LR = set(NONTERM_PRODS.keys())
TERMINALS_LR = set()
for _, rhs in PRODUCTIONS_LR:
    for sym in rhs:
        if sym not in NONTERMINALS_LR:
            TERMINALS_LR.add(sym)


class LRItem:
    """An LR(0) item: production index + dot position."""
    __slots__ = ('prod_idx', 'dot')

    def __init__(self, prod_idx, dot=0):
        self.prod_idx = prod_idx
        self.dot = dot

    @property
    def lhs(self):
        return PRODUCTIONS_LR[self.prod_idx][0]

    @property
    def rhs(self):
        return PRODUCTIONS_LR[self.prod_idx][1]

    def next_sym(self):
        """Symbol after the dot, or None."""
        rhs = self.rhs
        if self.dot < len(rhs):
            return rhs[self.dot]
        return None

    def is_reduce(self):
        return self.dot >= len(self.rhs)

    def shift(self):
        return LRItem(self.prod_idx, self.dot + 1)

    def __eq__(self, other):
        return self.prod_idx == other.prod_idx and self.dot == other.dot

    def __hash__(self):
        return hash((self.prod_idx, self.dot))

    def __repr__(self):
        rhs = list(self.rhs)
        rhs.insert(self.dot, '•')
        symbols = ' '.join(str(s) for s in rhs)
        return f"{self.lhs} → {symbols}"


def closure(items):
    """Compute LR(0) closure of a set of LRItem objects."""
    result = set(items)
    changed = True
    while changed:
        changed = False
        for item in list(result):
            sym = item.next_sym()
            if sym is not None and sym not in TERMINALS_LR:
                # Non-terminal — add all its productions
                for prod_idx in NONTERM_PRODS.get(sym, []):
                    new_item = LRItem(prod_idx, 0)
                    if new_item not in result:
                        result.add(new_item)
                        changed = True
    return frozenset(result)


def goto(items, symbol):
    """Compute GOTO(items, symbol)."""
    moved = set()
    for item in items:
        if item.next_sym() == symbol:
            moved.add(item.shift())
    if not moved:
        return None
    return closure(moved)


def build_canonical_collection():
    """Build the LR(0) canonical collection of item sets."""
    start_item = LRItem(0, 0)  # S' → •Program
    C = [closure({start_item})]
    transitions = {}  # (state_idx, symbol) -> next_state_idx

    i = 0
    while i < len(C):
        state = C[i]
        # Compute GOTO for all symbols
        seen_symbols = set()
        for item in state:
            sym = item.next_sym()
            if sym is not None and sym not in seen_symbols:
                seen_symbols.add(sym)
                next_state = goto(state, sym)
                if next_state is not None:
                    if next_state not in C:
                        C.append(next_state)
                    j = C.index(next_state)
                    transitions[(i, sym)] = j
        i += 1

    return C, transitions


def _tok_name_lr(sym):
    """Convert a grammar symbol to a readable name."""
    names = {
        TT.CONST: 'const', TT.VAR: 'var', TT.PROCEDURE: 'procedure',
        TT.BEGIN: 'begin', TT.END: 'end', TT.IF: 'if', TT.THEN: 'then',
        TT.WHILE: 'while', TT.DO: 'do', TT.CALL: 'call', TT.READ: 'read',
        TT.WRITE: 'write', TT.ODD: 'odd',
        TT.PLUS: '+', TT.MINUS: '-', TT.TIMES: '*', TT.DIV: '/',
        TT.ASSIGN: ':=', TT.EQ: '=', TT.NE: '#', TT.LT: '<', TT.LE: '<=',
        TT.GT: '>', TT.GE: '>=',
        TT.LPAREN: '(', TT.RPAREN: ')', TT.SEMICOLON: ';',
        TT.COMMA: ',', TT.PERIOD: '.', TT.ID: 'id', TT.NUMBER: 'num',
        TT.EOF: '$', TT.ERROR: 'error',
    }
    return names.get(sym, str(sym))


def print_items(C):
    """Print the canonical collection for debugging."""
    for i, state in enumerate(C):
        print(f"\nState {i}:")
        for item in sorted(state, key=lambda x: (x.prod_idx, x.dot)):
            print(f"  {item}")
