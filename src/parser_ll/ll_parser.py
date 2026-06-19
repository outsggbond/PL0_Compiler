# src/parser_ll/ll_parser.py
"""LL(1) Recursive Descent Parser for PL/0.

Features:
- Recursive descent parsing (EBNF-aware, no left recursion)
- Parse tree construction
- Panic-mode error recovery with meaningful suggestions
- Graphviz DOT visualization of parse tree
- Left-recursion / left-factoring analysis
"""

from ..lexer.token import TokenType as TT
from ..lexer.lexer import Lexer

# ── Synchronisation tokens for error recovery ─────────────────────
SYNC_TOKENS = {TT.SEMICOLON, TT.END, TT.BEGIN, TT.PROCEDURE, TT.CONST,
               TT.VAR, TT.EOF, TT.THEN, TT.DO, TT.RPAREN}


class ParseError(Exception):
    def __init__(self, msg, token):
        super().__init__(f"Syntax error at line {token.line}, col {token.column}: {msg}")
        self.token = token
        self.message = msg


class ParseTreeNode:
    """A node in the concrete parse tree."""
    def __init__(self, label, value=None, token=None):
        self.label = label        # nonterminal or terminal name
        self.value = value        # actual token value (for terminals)
        self.token = token        # Token object
        self.children = []

    def add_child(self, child):
        if child is not None:
            self.children.append(child)

    def to_dict(self):
        """Convert tree to nested dict for JSON/serialisation."""
        return {
            'label': self.label,
            'value': self.value,
            'children': [c.to_dict() for c in self.children]
        }

    def __repr__(self):
        if self.children:
            kids = ', '.join(repr(c) for c in self.children)
            return f"{self.label}({kids})"
        return f"{self.label}:{self.value or ''}"


class LLParser:
    """Recursive descent parser for PL/0."""

    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.current_token = None
        self.errors = []
        self._advance()

    # ── token helpers ──────────────────────────────────────────────
    def _advance(self):
        """Get next token, skipping errors so we always make progress."""
        while True:
            self.current_token = self.lexer.get_next_token()
            if self.current_token.type != TT.ERROR:
                break
            self.errors.append(f"Lexical: {self.current_token.value}")

    def _peek_type(self):
        return self.current_token.type

    def _peek_val(self):
        return self.current_token.value

    def _eat(self, expected_type, context=""):
        """Consume a token of expected_type or report an error and recover."""
        if self._peek_type() == expected_type:
            tok = self.current_token
            self._advance()
            return tok
        msg = f"Expected '{_tok_name(expected_type)}', got '{_tok_name(self._peek_type())}'"
        if context:
            msg = f"{context}: {msg}"
        self._error(msg)
        return None

    def _error(self, msg):
        tok = self.current_token
        full_msg = f"line {tok.line}, col {tok.column}: {msg}"
        self.errors.append(full_msg)
        # Suggest fixes for common patterns
        suggestion = _suggest_fix(tok, msg)
        if suggestion:
            self.errors.append(f"  [HINT] Suggestion: {suggestion}")

    def _sync(self):
        """Panic-mode: skip tokens until a synchronisation point."""
        while self._peek_type() not in SYNC_TOKENS:
            self._advance()

    # ── Program ────────────────────────────────────────────────────
    def parse_program(self):
        """Program → Block '.'"""
        node = ParseTreeNode('Program')
        node.add_child(self._parse_block())
        if self._peek_type() == TT.PERIOD:
            tok = self.current_token
            self._advance()
            node.add_child(ParseTreeNode(_tok_name(TT.PERIOD), '.', tok))
        else:
            self._error("Expected '.' at end of program")
            # try to eat it anyway
            if self._peek_type() == TT.PERIOD:
                self._advance()
        return node

    # ── Block ──────────────────────────────────────────────────────
    def _parse_block(self):
        """Block → [ConstDecl] [VarDecl] {ProcDecl} Statement"""
        node = ParseTreeNode('Block')

        # Optional const declaration
        if self._peek_type() == TT.CONST:
            node.add_child(self._parse_const_decl())

        # Optional var declaration
        if self._peek_type() == TT.VAR:
            node.add_child(self._parse_var_decl())

        # Zero or more procedure declarations
        while self._peek_type() == TT.PROCEDURE:
            node.add_child(self._parse_proc_decl())

        # Mandatory statement
        node.add_child(self._parse_statement())
        return node

    # ── Const Declaration ──────────────────────────────────────────
    def _parse_const_decl(self):
        """ConstDecl → 'const' ident '=' number {',' ident '=' number} ';'"""
        node = ParseTreeNode('ConstDecl')
        node.add_child(ParseTreeNode(_tok_name(TT.CONST), 'const',
                                      self._eat(TT.CONST, "const declaration")))

        # At least one const definition
        node.add_child(self._parse_const_def())
        while self._peek_type() == TT.COMMA:
            node.add_child(ParseTreeNode(_tok_name(TT.COMMA), ',', self.current_token))
            self._advance()
            node.add_child(self._parse_const_def())

        node.add_child(ParseTreeNode(_tok_name(TT.SEMICOLON), ';',
                                      self._eat(TT.SEMICOLON, "after const declaration")))
        return node

    def _parse_const_def(self):
        """ident '=' number"""
        node = ParseTreeNode('ConstDef')
        id_tok = self._eat(TT.ID, "constant name")
        node.add_child(ParseTreeNode('id', id_tok.value if id_tok else '?', id_tok))
        eq_tok = self._eat(TT.EQ, "'=' after constant name")
        node.add_child(ParseTreeNode('=', '=', eq_tok))
        num_tok = self._eat(TT.NUMBER, "constant value")
        node.add_child(ParseTreeNode('num', str(num_tok.value) if num_tok else '?', num_tok))
        return node

    # ── Var Declaration ────────────────────────────────────────────
    def _parse_var_decl(self):
        """VarDecl → 'var' ident {',' ident} ';'"""
        node = ParseTreeNode('VarDecl')
        node.add_child(ParseTreeNode(_tok_name(TT.VAR), 'var',
                                      self._eat(TT.VAR, "var declaration")))

        id_tok = self._eat(TT.ID, "variable name")
        node.add_child(ParseTreeNode('id', id_tok.value if id_tok else '?', id_tok))

        while self._peek_type() == TT.COMMA:
            node.add_child(ParseTreeNode(_tok_name(TT.COMMA), ',', self.current_token))
            self._advance()
            id_tok = self._eat(TT.ID, "variable name after ','")
            node.add_child(ParseTreeNode('id', id_tok.value if id_tok else '?', id_tok))

        node.add_child(ParseTreeNode(_tok_name(TT.SEMICOLON), ';',
                                      self._eat(TT.SEMICOLON, "after var declaration")))
        return node

    # ── Procedure Declaration ──────────────────────────────────────
    def _parse_proc_decl(self):
        """ProcDecl → 'procedure' ident ';' Block ';'"""
        node = ParseTreeNode('ProcDecl')
        node.add_child(ParseTreeNode(_tok_name(TT.PROCEDURE), 'procedure',
                                      self._eat(TT.PROCEDURE, "procedure declaration")))

        id_tok = self._eat(TT.ID, "procedure name")
        node.add_child(ParseTreeNode('id', id_tok.value if id_tok else '?', id_tok))

        node.add_child(ParseTreeNode(_tok_name(TT.SEMICOLON), ';',
                                      self._eat(TT.SEMICOLON, "after procedure name")))
        node.add_child(self._parse_block())
        node.add_child(ParseTreeNode(_tok_name(TT.SEMICOLON), ';',
                                      self._eat(TT.SEMICOLON, "after procedure body")))
        return node

    # ── Statement ──────────────────────────────────────────────────
    def _parse_statement(self):
        """Statement → ident ':=' Expression
                     | 'call' ident
                     | 'begin' Statement {';' Statement} 'end'
                     | 'if' Condition 'then' Statement
                     | 'while' Condition 'do' Statement
                     | 'read' '(' ident ')'
                     | 'write' '(' Expression ')'
                     | ε
        """
        node = ParseTreeNode('Statement')
        t = self._peek_type()

        if t == TT.ID:
            tok = self.current_token
            node.add_child(ParseTreeNode('id', tok.value, tok))
            self._advance()
            ass_tok = self._eat(TT.ASSIGN, "':=' after variable name")
            node.add_child(ParseTreeNode(':=', ':=', ass_tok))
            node.add_child(self._parse_expression())
        elif t == TT.CALL:
            node.add_child(ParseTreeNode(_tok_name(TT.CALL), 'call',
                                          self._eat(TT.CALL)))
            id_tok = self._eat(TT.ID, "procedure name after 'call'")
            node.add_child(ParseTreeNode('id', id_tok.value if id_tok else '?', id_tok))
        elif t == TT.BEGIN:
            node.add_child(ParseTreeNode(_tok_name(TT.BEGIN), 'begin',
                                          self._eat(TT.BEGIN)))
            node.add_child(self._parse_statement())
            while self._peek_type() == TT.SEMICOLON:
                node.add_child(ParseTreeNode(_tok_name(TT.SEMICOLON), ';', self.current_token))
                self._advance()
                # Check for optional trailing semicolon before END
                if self._peek_type() == TT.END:
                    break
                node.add_child(self._parse_statement())
            node.add_child(ParseTreeNode(_tok_name(TT.END), 'end',
                                          self._eat(TT.END, "'end' after compound statement")))
        elif t == TT.IF:
            node.add_child(ParseTreeNode(_tok_name(TT.IF), 'if',
                                          self._eat(TT.IF)))
            node.add_child(self._parse_condition())
            node.add_child(ParseTreeNode(_tok_name(TT.THEN), 'then',
                                          self._eat(TT.THEN, "'then' after condition")))
            node.add_child(self._parse_statement())
        elif t == TT.WHILE:
            node.add_child(ParseTreeNode(_tok_name(TT.WHILE), 'while',
                                          self._eat(TT.WHILE)))
            node.add_child(self._parse_condition())
            node.add_child(ParseTreeNode(_tok_name(TT.DO), 'do',
                                          self._eat(TT.DO, "'do' after condition")))
            node.add_child(self._parse_statement())
        elif t == TT.READ:
            node.add_child(ParseTreeNode(_tok_name(TT.READ), 'read',
                                          self._eat(TT.READ)))
            node.add_child(ParseTreeNode(_tok_name(TT.LPAREN), '(',
                                          self._eat(TT.LPAREN, "'(' after 'read'")))
            id_tok = self._eat(TT.ID, "variable name after 'read('")
            node.add_child(ParseTreeNode('id', id_tok.value if id_tok else '?', id_tok))
            node.add_child(ParseTreeNode(_tok_name(TT.RPAREN), ')',
                                          self._eat(TT.RPAREN, "')' after read argument")))
        elif t == TT.WRITE:
            node.add_child(ParseTreeNode(_tok_name(TT.WRITE), 'write',
                                          self._eat(TT.WRITE)))
            node.add_child(ParseTreeNode(_tok_name(TT.LPAREN), '(',
                                          self._eat(TT.LPAREN, "'(' after 'write'")))
            node.add_child(self._parse_expression())
            node.add_child(ParseTreeNode(_tok_name(TT.RPAREN), ')',
                                          self._eat(TT.RPAREN, "')' after write argument")))
        elif t in (TT.END, TT.SEMICOLON, TT.EOF, TT.THEN, TT.DO, TT.RPAREN):
            # ε production — empty statement
            pass
        else:
            self._error(f"Unexpected token '{_tok_name(t)}' at start of statement")
            self._sync()
        return node

    # ── Condition ──────────────────────────────────────────────────
    def _parse_condition(self):
        """Condition → 'odd' Expression | Expression RelOp Expression"""
        node = ParseTreeNode('Condition')
        if self._peek_type() == TT.ODD:
            node.add_child(ParseTreeNode(_tok_name(TT.ODD), 'odd',
                                          self._eat(TT.ODD)))
            node.add_child(self._parse_expression())
        else:
            node.add_child(self._parse_expression())
            node.add_child(self._parse_rel_op())
            node.add_child(self._parse_expression())
        return node

    def _parse_rel_op(self):
        """RelOp → '=' | '#' | '<' | '<=' | '>' | '>='"""
        node = ParseTreeNode('RelOp')
        t = self._peek_type()
        if t in (TT.EQ, TT.NE, TT.LT, TT.LE, TT.GT, TT.GE):
            tok = self.current_token
            self._advance()
            node.add_child(ParseTreeNode(_tok_name(t), tok.value, tok))
        else:
            self._error(f"Expected relational operator, got '{_tok_name(t)}'")
        return node

    # ── Expression ─────────────────────────────────────────────────
    def _parse_expression(self):
        """Expression → ['+' | '-'] Term {('+' | '-') Term}"""
        node = ParseTreeNode('Expression')
        if self._peek_type() in (TT.PLUS, TT.MINUS):
            tok = self.current_token
            self._advance()
            node.add_child(ParseTreeNode(_tok_name(tok.type), tok.value, tok))
        node.add_child(self._parse_term())
        while self._peek_type() in (TT.PLUS, TT.MINUS):
            tok = self.current_token
            self._advance()
            node.add_child(ParseTreeNode(_tok_name(tok.type), tok.value, tok))
            node.add_child(self._parse_term())
        return node

    # ── Term ───────────────────────────────────────────────────────
    def _parse_term(self):
        """Term → Factor {('*' | '/') Factor}"""
        node = ParseTreeNode('Term')
        node.add_child(self._parse_factor())
        while self._peek_type() in (TT.TIMES, TT.DIV):
            tok = self.current_token
            self._advance()
            node.add_child(ParseTreeNode(_tok_name(tok.type), tok.value, tok))
            node.add_child(self._parse_factor())
        return node

    # ── Factor ─────────────────────────────────────────────────────
    def _parse_factor(self):
        """Factor → ident | number | '(' Expression ')'"""
        node = ParseTreeNode('Factor')
        t = self._peek_type()
        if t == TT.ID:
            tok = self.current_token
            self._advance()
            node.add_child(ParseTreeNode('id', tok.value, tok))
        elif t == TT.NUMBER:
            tok = self.current_token
            self._advance()
            node.add_child(ParseTreeNode('num', str(tok.value), tok))
        elif t == TT.LPAREN:
            node.add_child(ParseTreeNode(_tok_name(TT.LPAREN), '( ',
                                          self._eat(TT.LPAREN)))
            node.add_child(self._parse_expression())
            node.add_child(ParseTreeNode(_tok_name(TT.RPAREN), ')',
                                          self._eat(TT.RPAREN, "')' after expression")))
        else:
            self._error(f"Expected identifier, number, or '(', got '{_tok_name(t)}'")
        return node

    # ── Parse entry point ──────────────────────────────────────────
    def parse(self):
        """Parse the full program. Returns ParseTreeNode for Program."""
        self.errors.clear()
        try:
            tree = self.parse_program()
            return tree, self.errors
        except Exception as e:
            self.errors.append(str(e))
            return None, self.errors


# ── Helper functions ────────────────────────────────────────────────
def _tok_name(tt):
    """Convert TokenType to a human-readable name."""
    names = {
        TT.CONST: 'const', TT.VAR: 'var', TT.PROCEDURE: 'procedure',
        TT.BEGIN: 'begin', TT.END: 'end', TT.IF: 'if', TT.THEN: 'then',
        TT.WHILE: 'while', TT.DO: 'do', TT.CALL: 'call', TT.READ: 'read',
        TT.WRITE: 'write', TT.ODD: 'odd',
        TT.PLUS: '+', TT.MINUS: '-', TT.TIMES: '*', TT.DIV: '/',
        TT.ASSIGN: ':=', TT.EQ: '=', TT.NE: '#', TT.LT: '<', TT.LE: '<=',
        TT.GT: '>', TT.GE: '>=',
        TT.LPAREN: '(', TT.RPAREN: ')', TT.SEMICOLON: ';',
        TT.COMMA: ',', TT.PERIOD: '.', TT.ID: 'identifier',
        TT.NUMBER: 'number', TT.EOF: 'EOF', TT.ERROR: 'error',
    }
    return names.get(tt, str(tt))


def _suggest_fix(token, msg):
    """Provide fix suggestions for common syntax errors."""
    t = token.type
    if "Expected ';'" in msg or "Expected ';'" in msg:
        return "Insert a semicolon ';' before this token."
    if "Expected ')'" in msg:
        return "Insert a closing parenthesis ')'."
    if "Expected '('" in msg:
        return "Insert an opening parenthesis '('."
    if "Expected ':='" in msg:
        return "Use ':=' for assignment (not '=')."
    if "Expected '.'" in msg:
        return "End the program with a period '.'."
    if "Expected 'then'" in msg:
        return "Add 'then' after the if-condition."
    if "Expected 'do'" in msg:
        return "Add 'do' after the while-condition."
    if "Expected 'end'" in msg:
        return "Add 'end' to close the compound statement."
    if "Unexpected token" in msg:
        return "Check the syntax around this token."
    return None


# ── Graphviz DOT visualization ──────────────────────────────────────
_NODE_COUNTER = 0


def _reset_counter():
    global _NODE_COUNTER
    _NODE_COUNTER = 0


def _next_id():
    global _NODE_COUNTER
    _NODE_COUNTER += 1
    return f"n{_NODE_COUNTER}"


def tree_to_dot(tree: ParseTreeNode) -> str:
    """Convert parse tree to Graphviz DOT format string."""
    _reset_counter()
    lines = ['digraph ParseTree {',
             '  rankdir=TB;',
             '  node [shape=box, style=filled, fontname="Courier New", fontsize=11];',
             '  edge [fontname="Courier New", fontsize=9];']

    def _walk(node, parent_id=None):
        nid = _next_id()
        # Color-code different node types
        if node.children:
            fill = '#E8F0FE'  # light blue for nonterminals
        elif node.label == 'id':
            fill = '#FFF3CD'  # light yellow for identifiers
        elif node.label in ('num',):
            fill = '#D4EDDA'  # light green for numbers
        elif node.label in ('+', '-', '*', '/', ':=', '=', '#', '<', '<=', '>', '>=', 'odd'):
            fill = '#F8D7DA'  # light red for operators
        else:
            fill = '#E2E3E5'  # light grey for others

        label = node.label
        if node.value:
            label = f"{node.label}\\n{node.value}"
        lines.append(f'  {nid} [label="{label}", fillcolor="{fill}"];')
        if parent_id:
            lines.append(f'  {parent_id} -> {nid};')
        for child in node.children:
            _walk(child, nid)

    _walk(tree)
    lines.append('}')
    return '\n'.join(lines)


def print_tree(tree: ParseTreeNode, indent=0):
    """Text-based tree printer for console output."""
    prefix = "  " * indent
    val = f" [{tree.value}]" if tree.value else ""
    print(f"{prefix}{tree.label}{val}")
    for child in tree.children:
        print_tree(child, indent + 1)


# ── Left-recursion / left-factoring analysis ──────────────────────
def analyze_grammar():
    """Check grammar for left recursion and common prefixes (needing factoring)."""
    from .first_follow import PRODUCTIONS, NONTERMINALS

    issues = []

    # Check for direct left recursion: A → Aα
    for nt, alternatives in PRODUCTIONS.items():
        for alt in alternatives:
            if alt and alt[0] == nt:
                issues.append(
                    f"[WARN] Direct left recursion: {nt} -> {' '.join(str(s) for s in alt)}"
                )

    # Check for common prefixes among alternatives
    for nt, alternatives in PRODUCTIONS.items():
        if len(alternatives) <= 1:
            continue
        first_sym = {}
        for alt in alternatives:
            if alt:
                fs = alt[0]
                first_sym.setdefault(fs, []).append(alt)
        for sym, alts in first_sym.items():
            if len(alts) > 1 and sym is not None:
                alts_str = ' | '.join(' '.join(str(s) for s in a) for a in alts)
                issues.append(
                    f"[WARN] Common prefix in {nt}: {alts_str} -- may need left factoring"
                )

    return issues


if __name__ == '__main__':
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    from ..utils.output_manager import resolve_output_path, tee_output

    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            source = f.read()
        output_path = resolve_output_path(sys.argv[1])
    else:
        source = 'const n=10; var x; begin x:=n; write(x) end.'
        print(f"Usage: python -m src.parser_ll.ll_parser <source_file>")
        print(f"Using built-in test:\n---\n{source}\n---\n")
        output_path = None

    with tee_output(output_path):
        lexer = Lexer(source)
        parser = LLParser(lexer)
        tree, errors = parser.parse()

        if errors:
            for e in errors:
                print(f"  [ERROR] {e}")
        print()
        print("Parse tree:")
        print_tree(tree)
