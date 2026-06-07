# src/semantic_ll/symbol_table.py
"""Scoped symbol table for PL/0 compiler semantic analysis."""

from enum import Enum, auto


class SymKind(Enum):
    CONST = auto()
    VAR = auto()
    PROC = auto()


class Symbol:
    """A single symbol entry."""
    def __init__(self, name, kind: SymKind, level=0, address=0, value=None):
        self.name = name
        self.kind = kind
        self.level = level      # nesting depth (0 = global)
        self.address = address  # offset within scope
        self.value = value      # for const: the constant value

    def __repr__(self):
        v = f" = {self.value}" if self.value is not None else ""
        return (f"Symbol({self.kind.name} '{self.name}'"
                f" level={self.level} addr={self.address}{v})")


class Scope:
    """One scope level in the symbol table."""
    def __init__(self, name='global', level=0):
        self.name = name
        self.level = level
        self.symbols = {}       # name → Symbol
        self.var_count = 0      # allocation counter for variables

    def insert(self, sym: Symbol):
        if sym.name in self.symbols:
            return False  # duplicate
        self.symbols[sym.name] = sym
        if sym.kind == SymKind.VAR:
            sym.address = self.var_count
            self.var_count += 1
        return True

    def lookup(self, name):
        return self.symbols.get(name)

    def __repr__(self):
        return f"Scope({self.name!r}, level={self.level}, {len(self.symbols)} symbols)"


class SymbolTable:
    """Scoped symbol table: linked list of Scope objects."""

    def __init__(self):
        self.scopes = [Scope(name='global', level=0)]

    def enter_scope(self, name='block'):
        """Push a new scope."""
        level = self.current_level() + 1
        scope = Scope(name=name, level=level)
        self.scopes.append(scope)
        return scope

    def exit_scope(self):
        """Pop the current scope."""
        if len(self.scopes) > 1:
            return self.scopes.pop()
        return None  # cannot pop global

    def current_scope(self):
        return self.scopes[-1]

    def current_level(self):
        return self.scopes[-1].level

    def insert(self, sym: Symbol):
        return self.current_scope().insert(sym)

    def lookup(self, name):
        """Search from innermost to outermost scope."""
        for scope in reversed(self.scopes):
            s = scope.lookup(name)
            if s is not None:
                return s
        return None

    def lookup_current_only(self, name):
        """Lookup only in current scope."""
        return self.current_scope().lookup(name)

    def display(self):
        """Pretty-print the entire symbol table."""
        print("\n" + "=" * 60)
        print("SYMBOL TABLE")
        print("-" * 40)
        for i, scope in enumerate(self.scopes):
            print(f"Scope[{i}]: {scope.name!r} (level {scope.level})")
            if not scope.symbols:
                print("  (empty)")
            for name, sym in scope.symbols.items():
                v = f" = {sym.value}" if sym.value is not None else ""
                print(f"  {sym.kind.name:6s} {name:12s} addr={sym.address:3d}{v}")
        print("=" * 60)
