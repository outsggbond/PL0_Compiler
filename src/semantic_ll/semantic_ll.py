# src/semantic_ll/semantic_ll.py
"""L-attributed semantic analysis for PL/0 using the LL parse tree.

Walks the LL(1) parse tree, performing:
- Symbol table management (const, var, procedure declarations)
- Type checking
- Quadruple (three-address code) generation
- Error reporting
"""

from ..utils.symbol_table import SymbolTable, Symbol, SymKind
from ..utils.quad_generator import QuadGenerator, QuadVM


class SemanticLL:
    """L-attributed semantic analyzer walking the LL parse tree."""

    def __init__(self):
        self.symtab = SymbolTable()
        self.quadgen = QuadGenerator()
        self.errors = []
        self.warnings = []

    def analyze(self, parse_tree):
        """Walk the parse tree and perform semantic analysis. Returns (quads, errors)."""
        self.symtab = SymbolTable()
        self.quadgen = QuadGenerator()
        self.errors = []
        self.warnings = []
        try:
            self._visit(parse_tree)
        except Exception as e:
            self.errors.append(f"Semantic error: {e}")
        return self.quadgen, self.errors

    def _error(self, msg):
        self.errors.append(msg)

    def _warn(self, msg):
        self.warnings.append(msg)

    # ── Visitor dispatcher ─────────────────────────────────────────
    def _visit(self, node):
        if node is None:
            return None
        method = getattr(self, f'_visit_{node.label}', None)
        if method:
            return method(node)
        else:
            # Generic: visit children and return last result
            result = None
            for child in node.children:
                result = self._visit(child)
            return result

    # ── Program ────────────────────────────────────────────────────
    def _visit_Program(self, node):
        for child in node.children:
            self._visit(child)
        self.quadgen.emit('halt')

    # ── Block ──────────────────────────────────────────────────────
    def _visit_Block(self, node):
        for child in node.children:
            self._visit(child)

    # ── Const Declaration ──────────────────────────────────────────
    def _visit_ConstDecl(self, node):
        """Process const name = value pairs."""
        # Children alternate: ConstDef, comma, ConstDef, comma, ..., semicolon
        for child in node.children:
            if child.label == 'ConstDef':
                self._visit_ConstDef(child)

    def _visit_ConstDef(self, node):
        name = None
        value = None
        for child in node.children:
            if child.label == 'id' and child.value:
                name = child.value
            elif child.label == 'num' and child.value is not None:
                value = int(child.value)
        if name and value is not None:
            sym = Symbol(name, SymKind.CONST, level=self.symtab.current_level(), value=value)
            if not self.symtab.insert(sym):
                self._error(f"Duplicate constant '{name}'")
            else:
                self.quadgen.emit('const', value, None, name)

    # ── Var Declaration ────────────────────────────────────────────
    def _visit_VarDecl(self, node):
        for child in node.children:
            if child.label == 'id' and child.value:
                name = child.value
                sym = Symbol(name, SymKind.VAR, level=self.symtab.current_level())
                if not self.symtab.insert(sym):
                    self._error(f"Duplicate variable '{name}'")

    # ── Procedure Declaration ──────────────────────────────────────
    def _visit_ProcDecl(self, node):
        proc_name = None
        for child in node.children:
            if child.label == 'id' and child.value:
                proc_name = child.value
                break

        if proc_name:
            sym = Symbol(proc_name, SymKind.PROC, level=self.symtab.current_level())
            if not self.symtab.insert(sym):
                self._error(f"Duplicate procedure '{proc_name}'")

        # Emit jump over procedure body (target to be patched)
        skip_quad_idx = self.quadgen.emit('jump', None, None, 'PATCH')

        # Proc body label
        body_label = self.quadgen.new_label()
        self.quadgen.emit('label', None, None, body_label)

        # Enter new scope
        self.symtab.enter_scope(proc_name)

        # Process block (find Block child)
        for child in node.children:
            if child.label == 'Block':
                self._visit(child)
                break

        self.quadgen.emit('ret')

        # Exit scope
        self.symtab.exit_scope()

        # Patch the skip jump: jump to the next quad (after ret)
        after_idx = len(self.quadgen.quads)
        skip_target = f"L{after_idx}"
        self.quadgen.quads[skip_quad_idx].result = skip_target

    # ── Statement ──────────────────────────────────────────────────
    def _visit_Statement(self, node):
        if not node.children:
            return  # ε

        first = node.children[0]

        if first.label == 'id':
            # Assignment: ident := Expression
            name = first.value
            sym = self.symtab.lookup(name)
            if sym is None:
                self._error(f"Undefined identifier '{name}'")
            elif sym.kind == SymKind.CONST:
                self._error(f"Cannot assign to constant '{name}'")
            elif sym.kind == SymKind.PROC:
                self._error(f"Cannot assign to procedure '{name}'")

            # Visit expression (children[2] after ':=')
            result_place = None
            for child in node.children:
                if child.label == 'Expression':
                    result_place = self._visit(child)
                    break
            if name and result_place:
                self.quadgen.emit('assign', result_place, None, name)

        elif first.label == 'call':
            # call ident
            for child in node.children:
                if child.label == 'id' and child.value:
                    name = child.value
                    sym = self.symtab.lookup(name)
                    if sym is None:
                        self._error(f"Undefined procedure '{name}'")
                    elif sym.kind != SymKind.PROC:
                        self._error(f"'{name}' is not a procedure")
                    self.quadgen.emit('call', None, None, name)
                    break

        elif first.label == 'begin':
            # Compound statement — find all Statement children
            for child in node.children:
                if child.label == 'Statement':
                    self._visit(child)

        elif first.label == 'if':
            # if Condition then Statement
            # Pattern: if Cond then Stmt
            cond_labels = self._visit_condition_of_if(node)
            if not cond_labels:
                return
            true_label, false_label = cond_labels

            # Emit true label
            self.quadgen.emit('label', None, None, true_label)
            # Find and visit the Statement (after 'then')
            found_then = False
            for child in node.children:
                if found_then and child.label == 'Statement':
                    self._visit(child)
                    break
                if child.label == 'then':
                    found_then = True

            # Emit false label
            self.quadgen.emit('label', None, None, false_label)

        elif first.label == 'while':
            # while Condition do Statement
            loop_label = self.quadgen.new_label()
            test_label = self.quadgen.new_label()
            end_label = self.quadgen.new_label()

            # Loop entry label
            self.quadgen.emit('label', None, None, loop_label)

            # Condition — find it
            cond_result = None
            cond_node = None
            for child in node.children:
                if child.label == 'Condition':
                    cond_node = child
                    break
            if cond_node:
                cond_result = self._translate_condition(cond_node, test_label, end_label)

            # True label
            self.quadgen.emit('label', None, None, test_label)
            # Statement (after 'do')
            found_do = False
            for child in node.children:
                if found_do and child.label == 'Statement':
                    self._visit(child)
                    break
                if child.label == 'do':
                    found_do = True

            self.quadgen.emit('jump', None, None, loop_label)
            self.quadgen.emit('label', None, None, end_label)

        elif first.label == 'read':
            for child in node.children:
                if child.label == 'id' and child.value:
                    name = child.value
                    sym = self.symtab.lookup(name)
                    if sym is None:
                        self._error(f"Undefined variable '{name}' in read")
                    elif sym.kind == SymKind.CONST:
                        self._error(f"Cannot read into constant '{name}'")
                    elif sym.kind == SymKind.PROC:
                        self._error(f"Cannot read into procedure '{name}'")
                    self.quadgen.emit('read', None, None, name)
                    break

        elif first.label == 'write':
            for child in node.children:
                if child.label == 'Expression':
                    result_place = self._visit(child)
                    if result_place is not None:
                        self.quadgen.emit('write', result_place, None, None)
                    break

    # ── Condition ──────────────────────────────────────────────────
    def _visit_Condition(self, node):
        """Condition → odd Expression | Expression RelOp Expression"""
        return self._translate_condition(node)

    def _visit_condition_of_if(self, node):
        """For if-then: returns (true_label, false_label)"""
        for child in node.children:
            if child.label == 'Condition':
                true_l = self.quadgen.new_label()
                false_l = self.quadgen.new_label()
                self._translate_condition(child, true_l, false_l)
                return (true_l, false_l)
        return None

    def _translate_condition(self, cond_node, true_label=None, false_label=None):
        """Translate a condition node."""
        if not cond_node or not cond_node.children:
            return None

        if true_label is None:
            true_label = self.quadgen.new_label()
        if false_label is None:
            false_label = self.quadgen.new_label()

        first = cond_node.children[0]

        if first.label == 'odd':
            # odd Expression
            expr_node = None
            for child in cond_node.children:
                if child.label == 'Expression':
                    expr_node = child
                    break
            if expr_node:
                result = self._visit(expr_node)
                if result is not None:
                    self.quadgen.emit('odd', result, None, f"T{self.quadgen.next_temp}")
                    self.quadgen.next_temp += 1
                    temp = f"T{self.quadgen.next_temp - 1}"
                    self.quadgen.emit('j#', temp, 0, true_label)  # jump if odd (non-zero)
                    self.quadgen.emit('jump', None, None, false_label)
                    return temp
        else:
            # Expression RelOp Expression
            # Children: Expression, RelOp, Expression
            children = cond_node.children
            if len(children) >= 3:
                left = self._visit(children[0]) if children[0].label == 'Expression' else None
                relop = children[1].children[0].value if children[1].children else None
                right = None
                for child in children:
                    if child.label == 'Expression' and child != children[0]:
                        right = self._visit(child)
                        break

                if left is not None and right is not None and relop is not None:
                    relop_map = {
                        '=': 'j=', '#': 'j#', '<': 'j<', '<=': 'j<=',
                        '>': 'j>', '>=': 'j>=',
                    }
                    jop = relop_map.get(relop, 'j=')
                    self.quadgen.emit(jop, left, right, true_label)
                    self.quadgen.emit('jump', None, None, false_label)
                    return 'cond'

        return None

    # ── Expression ─────────────────────────────────────────────────
    def _visit_Expression(self, node):
        """Expression → ['+' | '-'] Term {('+' | '-') Term}

        Returns the name of the variable/temp holding the result.
        """
        if not node.children:
            return None

        children = node.children
        idx = 0

        # Optional sign
        negate = False
        if children[idx].label in ('+', '-'):
            if children[idx].value == '-':
                negate = True
            idx += 1

        # First term
        if idx < len(children):
            result = self._visit(children[idx])
            idx += 1
        else:
            return None

        if result is None:
            return None

        if negate:
            temp = self.quadgen.new_temp()
            self.quadgen.emit('neg', result, None, temp)
            result = temp

        # Rest: {('+' | '-') Term}
        while idx < len(children):
            if children[idx].label in ('+', '-'):
                op = children[idx].value
                idx += 1
                if idx < len(children):
                    right = self._visit(children[idx])
                    idx += 1
                    if right is not None:
                        temp = self.quadgen.new_temp()
                        self.quadgen.emit(op, result, right, temp)
                        result = temp
            else:
                idx += 1

        return result

    # ── Term ───────────────────────────────────────────────────────
    def _visit_Term(self, node):
        """Term → Factor {('*' | '/') Factor}

        Returns the name of the variable/temp holding the result.
        """
        if not node.children:
            return None

        result = self._visit(node.children[0])
        if result is None:
            return None

        idx = 1
        while idx < len(node.children):
            if node.children[idx].label in ('*', '/'):
                op = node.children[idx].value
                idx += 1
                if idx < len(node.children):
                    right = self._visit(node.children[idx])
                    idx += 1
                    if right is not None:
                        temp = self.quadgen.new_temp()
                        self.quadgen.emit(op, result, right, temp)
                        result = temp
            else:
                idx += 1

        return result

    # ── Factor ─────────────────────────────────────────────────────
    def _visit_Factor(self, node):
        """Factor → ident | number | '(' Expression ')'

        Returns the name of the variable/temp holding the result.
        """
        if not node.children:
            return None

        first = node.children[0]

        if first.label == 'id':
            name = first.value
            sym = self.symtab.lookup(name)
            if sym is None:
                self._error(f"Undefined identifier '{name}'")
            elif sym.kind == SymKind.PROC:
                self._error(f"Cannot use procedure '{name}' in expression")
            elif sym.kind == SymKind.CONST:
                # Constants have their value — emit const load into temp
                temp = self.quadgen.new_temp()
                self.quadgen.emit('const', sym.value, None, temp)
                return temp
            return name  # variable: return its name

        elif first.label == 'num':
            temp = self.quadgen.new_temp()
            self.quadgen.emit('const', int(first.value), None, temp)
            return temp

        elif first.label == '(':
            # Find Expression child
            for child in node.children:
                if child.label == 'Expression':
                    return self._visit(child)

        return None


# ── Helper to visualize quad execution ─────────────────────────────
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
        print(f"Usage: python -m src.semantic_ll.semantic_ll <source_file>")
        print(f"Using built-in test:\n---\n{source}\n---\n")

    from ..lexer.lexer import Lexer
    from ..parser_ll.ll_parser import LLParser

    lexer = Lexer(source)
    parser = LLParser(lexer)
    tree, parse_errors = parser.parse()
    if parse_errors:
        for e in parse_errors:
            print(f"  [PARSE ERROR] {e}")

    sem = SemanticLL()
    quads, sem_errors = sem.analyze(tree)

    sem.symtab.display()
    quads.display()
    if sem_errors:
        for e in sem_errors:
            print(f"  [SEMANTIC ERROR] {e}")
