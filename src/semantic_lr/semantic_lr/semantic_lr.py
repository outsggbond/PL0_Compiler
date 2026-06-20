# src/semantic_lr/semantic_lr.py
"""S-attributed semantic analysis integrated with the SLR(1) parser.

Uses bottom-up attribute evaluation: semantic actions fire on each reduction.
Shares symbol_table and quad_generator from the LL semantic modules.
"""

from ..lexer.token import TokenType as TT, Token
from ..lexer.lexer import Lexer
from ..parser_lr.lr_items import (
    PRODUCTIONS_LR, build_canonical_collection, NONTERMINALS_LR, _tok_name_lr,
)
from ..parser_lr.lr_table import build_slr_table
from ..utils.symbol_table import SymbolTable, Symbol, SymKind
from ..utils.quad_generator import QuadGenerator, QuadVM


class SemanticLR:
    """LR parser with integrated S-attributed semantic analysis."""

    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.symtab = SymbolTable()
        self.quadgen = QuadGenerator()
        self.errors = []
        self.warnings = []
        self.while_context = None  # (loop_label, test_label, end_label) for current while

        # Build SLR tables
        from ..parser_ll.first_follow import compute_first, compute_follow

        first = compute_first()
        follow = compute_follow(first)
        follow["S'"] = {TT.EOF}
        # ConstRest is after ... NUMBER ConstRest ;  → followed by SEMICOLON
        follow['ConstRest'] = {TT.SEMICOLON}
        # VarRest is after ... ID VarRest ;  → followed by SEMICOLON
        follow['VarRest'] = {TT.SEMICOLON}
        # StmtList only appears in: begin StmtList end → followed by END
        follow['StmtList'] = {TT.END}
        # Sign is followed by Term → FIRST(Term)
        follow['Sign'] = first.get('Term', set()) - {None}
        # TermList → after Term {TermList} → FOLLOW(Expression)
        follow['TermList'] = follow.get('Expression', set())
        # FactorList → after Factor {FactorList} → FOLLOW(Term)
        # FOLLOW(Term) = FIRST(TermList) ∪ (if TermList nullable) FOLLOW(Expression)
        follow['FactorList'] = follow['TermList'].copy()
        follow['FactorList'] |= {TT.PLUS, TT.MINUS}  # from FIRST(TermList)
        # Expression's FOLLOW from grammar context
        follow['Expression'] = follow.get('Expression', set()) | {TT.RPAREN, TT.SEMICOLON, TT.END, TT.THEN, TT.DO, TT.PERIOD}

        self.C, self.transitions = build_canonical_collection()
        self.action, self.goto, self.conflicts = build_slr_table(
            self.C, self.transitions, follow
        )

    def parse(self):
        """LR parse with semantic actions. Returns (quads, errors)."""
        self.errors.clear()
        self.warnings.clear()

        # Add grammar warnings
        for c in self.conflicts:
            self.warnings.append(f"Grammar: {c}")

        stack = [0]       # state stack
        sem_stack = []    # semantic value stack (strings, tuples, etc.)

        # Tokenize
        tokens = []
        while True:
            tok = self.lexer.get_next_token()
            if tok.type == TT.ERROR:
                self.errors.append(f"Lexical error at line {tok.line}: {tok.value}")
                continue
            tokens.append(tok)
            if tok.type == TT.EOF:
                break

        pos = 0
        max_steps = 10000
        steps = 0
        while pos < len(tokens):
            steps += 1
            if steps > max_steps:
                self.errors.append(f"LR parser stuck after {max_steps} steps (state={stack[-1]}, token={_tok_name_lr(tokens[pos].type)})")
                break
            tok = tokens[pos]
            state = stack[-1]
            action_entry = self.action.get(state, {}).get(tok.type)

            if action_entry is None:
                expected = list(self.action.get(state, {}).keys())
                expected_names = ', '.join(_tok_name_lr(e) for e in expected)
                self.errors.append(
                    f"Syntax error at line {tok.line}: unexpected "
                    f"'{_tok_name_lr(tok.type)}', expected: {expected_names or 'EOF'}"
                )
                # Panic recovery
                while len(stack) > 1:
                    stack.pop()
                    if sem_stack:
                        sem_stack.pop()
                    if tok.type in self.action.get(stack[-1], {}):
                        break
                if not stack or tok.type not in self.action.get(stack[-1], {}):
                    pos += 1
                continue

            action_type = action_entry[0]

            if action_type == 'shift':
                next_state = action_entry[1]
                stack.append(next_state)
                # Push the token onto semantic stack
                sem_stack.append(('token', tok))
                # Set while context when seeing WHILE
                if tok.type == TT.WHILE:
                    loop_l = self.quadgen.new_label()
                    body_l = self.quadgen.new_label()
                    end_l = self.quadgen.new_label()
                    self.while_context = (loop_l, body_l, end_l)
                    # Emit: jump test_label  (jump forward to condition)
                    self.quadgen.emit('jump', None, None, loop_l)
                    # body_l will be emitted right after condition
                pos += 1

            elif action_type == 'reduce':
                prod_idx = action_entry[1]
                lhs, rhs = PRODUCTIONS_LR[prod_idx]

                # Pop |rhs| items from semantic stack
                sem_vals = []
                if rhs and rhs != ():
                    for _ in range(len(rhs)):
                        stack.pop()
                        if sem_stack:
                            sem_vals.insert(0, sem_stack.pop())

                # Execute semantic action for this production
                result = self._semantic_action(prod_idx, lhs, rhs, sem_vals)

                if prod_idx == 0:
                    # S' → Program: accept
                    self.quadgen.emit('halt')
                    return self.quadgen, self.errors

                # GOTO
                top_state = stack[-1]
                goto_state = self.goto.get(top_state, {}).get(lhs)
                if goto_state is None:
                    self.errors.append(f"Internal: no GOTO in state {top_state} for {lhs}")
                    return self.quadgen, self.errors

                stack.append(goto_state)
                sem_stack.append(result)

            elif action_type == 'accept':
                self.quadgen.emit('halt')
                return self.quadgen, self.errors

        self.quadgen.emit('halt')
        return self.quadgen, self.errors

    # ── Semantic action table ───────────────────────────────────────
    def _semantic_action(self, prod_idx, lhs, rhs, sem_vals):
        """Execute the semantic action for production `prod_idx`.

        sem_vals are the semantic values of the RHS symbols.
        Returns the semantic value for the LHS non-terminal.
        """
        # Helper to extract token values from sem_vals
        def tok_at(i):
            """Get token from sem_vals[i] where sem_vals[i] is ('token', Token)."""
            if i < len(sem_vals) and sem_vals[i] is not None:
                sv = sem_vals[i]
                if isinstance(sv, tuple) and sv[0] == 'token':
                    return sv[1]
                return sv
            return None

        def tok_val_at(i):
            """Get .value from the token at position i."""
            t = tok_at(i)
            if isinstance(t, Token):
                return t.value
            return t

        # ─── Production dispatch (matches lr_items.py PRODUCTIONS_LR) ──
        # 0: S' -> Program
        if prod_idx == 0:
            return None
        # 1: Program -> Block PERIOD
        elif prod_idx == 1:
            return None
        # 2-6: Block variants
        elif 2 <= prod_idx <= 6:
            return None
        # 7: ConstDecl -> CONST ID EQ NUMBER ConstRest SEMICOLON
        elif prod_idx == 7:
            name = tok_val_at(1)
            value = int(tok_val_at(3)) if tok_val_at(3) is not None else 0
            if name:
                sym = Symbol(name, SymKind.CONST, level=self.symtab.current_level(), value=value)
                if not self.symtab.insert(sym):
                    self.errors.append(f"Duplicate constant '{name}'")
                else:
                    self.quadgen.emit('const', value, None, name)
            return None
        # 8: ConstRest -> COMMA ID EQ NUMBER ConstRest
        elif prod_idx == 8:
            name = tok_val_at(1)
            value = int(tok_val_at(3)) if tok_val_at(3) is not None else 0
            if name:
                sym = Symbol(name, SymKind.CONST, level=self.symtab.current_level(), value=value)
                if not self.symtab.insert(sym):
                    self.errors.append(f"Duplicate constant '{name}'")
                else:
                    self.quadgen.emit('const', value, None, name)
            return None
        # 9: ConstRest -> ε
        elif prod_idx == 9:
            return None
        # 10: VarDecl -> VAR ID VarRest SEMICOLON
        elif prod_idx == 10:
            name = tok_val_at(1)
            if name:
                sym = Symbol(name, SymKind.VAR, level=self.symtab.current_level())
                if not self.symtab.insert(sym):
                    self.errors.append(f"Duplicate variable '{name}'")
            return None
        # 11: VarRest -> COMMA ID VarRest
        elif prod_idx == 11:
            name = tok_val_at(1)
            if name:
                sym = Symbol(name, SymKind.VAR, level=self.symtab.current_level())
                if not self.symtab.insert(sym):
                    self.errors.append(f"Duplicate variable '{name}'")
            return None
        # 12: VarRest -> ε
        elif prod_idx == 12:
            return None
        # 13: ProcDecls -> ProcDecl ProcDecls
        elif prod_idx == 13:
            return None
        # 14: ProcDecls -> ε
        elif prod_idx == 14:
            return None
        # 15: ProcDecl -> PROCEDURE ID SEMICOLON Block SEMICOLON
        elif prod_idx == 15:
            proc_name = tok_val_at(1)
            if proc_name:
                sym = Symbol(proc_name, SymKind.PROC, level=self.symtab.current_level())
                if not self.symtab.insert(sym):
                    self.errors.append(f"Duplicate procedure '{proc_name}'")
            return None
        # 16: Statement -> ID ASSIGN Expression
        elif prod_idx == 16:
            name = tok_val_at(0)
            expr_result = sem_vals[2] if len(sem_vals) > 2 else None
            if name:
                s = self.symtab.lookup(name)
                if s is None:
                    self.errors.append(f"Undefined identifier '{name}'")
                elif s.kind == SymKind.CONST:
                    self.errors.append(f"Cannot assign to constant '{name}'")
                elif s.kind == SymKind.PROC:
                    self.errors.append(f"Cannot assign to procedure '{name}'")
                else:
                    if expr_result:
                        self.quadgen.emit('assign', expr_result, None, name)
            return None
        # 17: Statement -> CALL ID
        elif prod_idx == 17:
            name = tok_val_at(1)
            if name:
                s = self.symtab.lookup(name)
                if s is None:
                    self.errors.append(f"Undefined procedure '{name}'")
                elif s.kind != SymKind.PROC:
                    self.errors.append(f"'{name}' is not a procedure")
                else:
                    self.quadgen.emit('call', None, None, name)
            return None
        # 18: Statement -> BEGIN StmtList END
        elif prod_idx == 18:
            return None
        # 19: Statement -> IF Condition THEN Statement
        elif prod_idx == 19:
            cond_info = sem_vals[1] if len(sem_vals) > 1 else None
            if isinstance(cond_info, tuple) and len(cond_info) == 2:
                true_l, false_l = cond_info
                self.quadgen.emit('label', None, None, true_l)
                self.quadgen.emit('label', None, None, false_l)
            return None
        # 20: Statement -> WHILE Condition DO Statement
        elif prod_idx == 20:
            if self.while_context:
                loop_l, body_l, end_l = self.while_context
                self.quadgen.emit('label', None, None, body_l)
                self.quadgen.emit('jump', None, None, loop_l)
                self.quadgen.emit('label', None, None, end_l)
                self.while_context = None
            return None
        # 21: Statement -> READ LPAREN ID RPAREN
        elif prod_idx == 21:
            name = tok_val_at(2)
            if name:
                s = self.symtab.lookup(name)
                if s is None:
                    self.errors.append(f"Undefined variable '{name}' in read")
                elif s.kind == SymKind.CONST:
                    self.errors.append(f"Cannot read into constant '{name}'")
                else:
                    self.quadgen.emit('read', None, None, name)
            return None
        # 22: Statement -> WRITE LPAREN Expression RPAREN
        elif prod_idx == 22:
            expr_result = sem_vals[2] if len(sem_vals) > 2 else None
            if expr_result:
                self.quadgen.emit('write', expr_result, None, None)
            return None
        # 23: StmtList -> Statement (last statement, no trailing ;)
        elif prod_idx == 23:
            return None
        # 24: StmtList -> Statement SEMICOLON StmtList
        elif prod_idx == 24:
            return None
        # 25: StmtList -> SEMICOLON Statement StmtList
        elif prod_idx == 25:
            return None
        # 26: StmtList -> SEMICOLON StmtList
        elif prod_idx == 26:
            return None
        # 27: StmtList -> ε
        elif prod_idx == 27:
            return None
        # 28: Condition -> ODD Expression
        elif prod_idx == 28:
            expr_result = sem_vals[1] if len(sem_vals) > 1 else None
            if expr_result:
                temp = self.quadgen.new_temp()
                self.quadgen.emit('odd', expr_result, None, temp)
                if self.while_context:
                    loop_l, body_l, end_l = self.while_context
                    self.quadgen.emit('j#', temp, 0, body_l)
                    self.quadgen.emit('jump', None, None, end_l)
                    return (body_l, end_l)
                return ('odd', temp)
            return None
        # 29: Condition -> Expression RelOp Expression
        elif prod_idx == 29:
            left = sem_vals[0] if len(sem_vals) > 0 else None
            relop = sem_vals[1] if len(sem_vals) > 1 else None
            right = sem_vals[2] if len(sem_vals) > 2 else None
            if left and relop is not None and right:
                if self.while_context:
                    loop_l, body_l, end_l = self.while_context
                else:
                    body_l = self.quadgen.new_label()
                    end_l = self.quadgen.new_label()
                relop_map = {
                    '=': 'j=', '#': 'j#', '<': 'j<', '<=': 'j<=',
                    '>': 'j>', '>=': 'j>=',
                }
                jop = relop_map.get(relop, 'j=')
                self.quadgen.emit(jop, left, right, body_l)
                self.quadgen.emit('jump', None, None, end_l)
                return (body_l, end_l)
            return None
        # 30-35: RelOp
        elif 30 <= prod_idx <= 35:
            return tok_val_at(0)
        # 36: Expression -> Sign Term TermList
        elif prod_idx == 36:
            sign = sem_vals[0] if len(sem_vals) > 0 else None
            term_result = sem_vals[1] if len(sem_vals) > 1 else None
            termlist_ops = sem_vals[2] if len(sem_vals) > 2 else []
            if term_result is None:
                return None
            result = term_result
            if sign == '-':
                temp = self.quadgen.new_temp()
                self.quadgen.emit('neg', result, None, temp)
                result = temp
            for op, operand in termlist_ops:
                temp = self.quadgen.new_temp()
                self.quadgen.emit(op, result, operand, temp)
                result = temp
            return result
        # 37-39: Sign
        elif prod_idx == 37:
            return '+'
        elif prod_idx == 38:
            return '-'
        elif prod_idx == 39:
            return None
        # 40-42: TermList
        elif prod_idx == 40:
            term_result = sem_vals[1] if len(sem_vals) > 1 else None
            rest = sem_vals[2] if len(sem_vals) > 2 else []
            return [('+', term_result)] + rest
        elif prod_idx == 41:
            term_result = sem_vals[1] if len(sem_vals) > 1 else None
            rest = sem_vals[2] if len(sem_vals) > 2 else []
            return [('-', term_result)] + rest
        elif prod_idx == 42:
            return []
        # 43: Term -> Factor FactorList
        elif prod_idx == 43:
            factor_result = sem_vals[0] if len(sem_vals) > 0 else None
            factorlist_ops = sem_vals[1] if len(sem_vals) > 1 else []
            if factor_result is None:
                return None
            result = factor_result
            for op, operand in factorlist_ops:
                temp = self.quadgen.new_temp()
                self.quadgen.emit(op, result, operand, temp)
                result = temp
            return result
        # 44-46: FactorList
        elif prod_idx == 44:
            factor_result = sem_vals[1] if len(sem_vals) > 1 else None
            rest = sem_vals[2] if len(sem_vals) > 2 else []
            return [('*', factor_result)] + rest
        elif prod_idx == 45:
            factor_result = sem_vals[1] if len(sem_vals) > 1 else None
            rest = sem_vals[2] if len(sem_vals) > 2 else []
            return [('/', factor_result)] + rest
        elif prod_idx == 46:
            return []
        # 47: Factor -> ID
        elif prod_idx == 47:
            name = tok_val_at(0)
            if name:
                s = self.symtab.lookup(name)
                if s is None:
                    self.errors.append(f"Undefined identifier '{name}'")
                    return None
                elif s.kind == SymKind.PROC:
                    self.errors.append(f"Cannot use procedure '{name}' in expression")
                    return None
                elif s.kind == SymKind.CONST:
                    temp = self.quadgen.new_temp()
                    self.quadgen.emit('const', s.value, None, temp)
                    return temp
                return name
            return None
        # 48: Factor -> NUMBER
        elif prod_idx == 48:
            val = tok_val_at(0)
            if val is not None:
                temp = self.quadgen.new_temp()
                self.quadgen.emit('const', int(val), None, temp)
                return temp
            return None
        # 49: Factor -> LPAREN Expression RPAREN
        elif prod_idx == 49:
            return sem_vals[1] if len(sem_vals) > 1 else None

        return None


# ── Visualization ───────────────────────────────────────────────────
def visualize_quad_execution(quadgen, input_values=None):
    """Run the quads on a VM and return a trace string."""
    vm = QuadVM(quadgen.quads, input_values)
    trace = vm.run()
    return vm.trace_to_text()


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            source = f.read()
    else:
        source = 'const n=10; var x; begin x:=n; write(x) end.'
        print(f"Usage: python -m src.semantic_lr.semantic_lr <source_file>")
        print(f"Using built-in test:\n---\n{source}\n---\n")

    from ..lexer.lexer import Lexer

    sem = SemanticLR(Lexer(source))
    quads, errors = sem.parse()

    sem.symtab.display()
    quads.display()
    if errors:
        for e in errors:
            print(f"  [ERROR] {e}")
