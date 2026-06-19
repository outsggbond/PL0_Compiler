# src/parser_lr/lr_items.py
"""用于 PL/0 SLR(1) 语法分析的 LR(0) 项目、闭包（Closure）、
项目集规范族（Canonical Collection）和 GOTO 函数实现。

"""

"""
这个文件干的事情就是这些：

文法
 ↓
增广文法
 ↓
LR项目
 ↓
closure()
 ↓
goto()
 ↓
项目集规范族(I0,I1...)
 ↓
状态转换图(DFA)

"""
from ..lexer.token import TokenType as TT

"""
── PL/0 的增广文法 ──────────────────────────────────────
产生式编号 → (左部LHS: 字符串, 右部RHS: 符号元组)
产生式0：S' → Program （增广开始符号）
终结符：使用 TokenType 枚举值表示
非终结符：使用字符串表示，例如 'Program'、'Block'、'Statement' 等
"""

# 第一部分：定义增广文法
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
# 第二部分：统计终结符和非终结符
"""
lhs = Left Hand Side
     = 产生式左部

rhs = Right Hand Side
     = 产生式右部
"""
# 构建查找表：非终结符 → 对应产生式编号列表
NONTERM_PRODS = {}
for idx, (lhs, rhs) in enumerate(PRODUCTIONS_LR):
    NONTERM_PRODS.setdefault(lhs, []).append(idx)

NONTERMINALS_LR = set(NONTERM_PRODS.keys())
TERMINALS_LR = set()
for _, rhs in PRODUCTIONS_LR:
    for sym in rhs:
        if sym not in NONTERMINALS_LR:
            TERMINALS_LR.add(sym)
"""

扫描整个文法，

建立：
① 非终结符 → 产生式编号表

② 非终结符集合

③ 终结符集合

供后面的 closure() 和 goto() 使用。
"""

# 第三部分：LRItem类

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

# 求closure闭包
def closure(items):
    result = set(items)
    changed = True
    while changed:
        changed = False
        for item in list(result):
            sym = item.next_sym()
            if sym is not None and sym not in TERMINALS_LR:
                for prod_idx in NONTERM_PRODS.get(sym, []):
                    new_item = LRItem(prod_idx, 0)
                    if new_item not in result:
                        result.add(new_item)
                        changed = True
    return frozenset(result)

# 第五部分：goto()
def goto(items, symbol):
    moved = set()
    for item in items:
        if item.next_sym() == symbol:
            moved.add(item.shift())
    if not moved:
        return None
    return closure(moved)

""""从初始项目 S' → •Program 开始，
不断调用 closure() 和 goto()，
生成所有 LR(0) 状态（I0、I1、I2...）以及它们之间的跳转关系（DFA）。
"""
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

# 把 TokenType 转换成人类可读的字符串。
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

# 它只是可视化输出 LR(0) 项目集规范族
def print_items(C):
    """Print the canonical collection for debugging."""
    for i, state in enumerate(C):
        print(f"\nState {i}:")
        for item in sorted(state, key=lambda x: (x.prod_idx, x.dot)):
            print(f"  {item}")
