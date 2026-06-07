# src/automata/regex_to_nfa.py
"""正则表达式 → NFA (Thompson 构造法)

Supports:
- Single characters: a, b, c, ...
- Concatenation (implicit): ab
- Union: a|b
- Kleene star: a*
- Plus: a+
- Optional: a?
- Character classes: [abc], [a-z], [0-9]
- Parentheses for grouping: (a|b)c

Returns an NFA object from nfa.py.
"""

from .nfa import (
    NFA,
    build_nfa_single_char,
    build_nfa_epsilon,
    build_nfa_concat,
    build_nfa_union,
    build_nfa_kleene_star,
    build_nfa_plus,
)


class RegexParser:
    """Parse a regular expression string and build the corresponding NFA."""

    def __init__(self, pattern):
        """
        Args:
            pattern: regex string
        """
        self.pattern = pattern
        self.pos = 0

    def parse(self):
        """Parse the full regex and return an NFA."""
        nfa = self._parse_union()
        if self.pos < len(self.pattern):
            raise ValueError(f"Unexpected character '{self.peek()}' at position {self.pos}")
        return nfa

    def peek(self):
        if self.pos >= len(self.pattern):
            return None
        return self.pattern[self.pos]

    def advance(self):
        ch = self.peek()
        self.pos += 1
        return ch

    def _parse_union(self):
        """Parse expr ( '|' expr )*"""
        left = self._parse_concat()
        while self.peek() == '|':
            self.advance()  # consume |
            right = self._parse_concat()
            left = build_nfa_union(left, right)
        return left

    def _parse_concat(self):
        """Parse factor+ (concatenation is implicit)"""
        nfa = self._parse_factor()
        while self.peek() is not None and self.peek() not in '|)':
            right = self._parse_factor()
            nfa = build_nfa_concat(nfa, right)
        return nfa

    def _parse_factor(self):
        """Parse atom [ '*' | '+' | '?' ]"""
        nfa = self._parse_atom()
        while True:
            ch = self.peek()
            if ch == '*':
                self.advance()
                nfa = build_nfa_kleene_star(nfa)
            elif ch == '+':
                self.advance()
                nfa = build_nfa_plus(nfa)
            elif ch == '?':
                self.advance()
                # a? ≡ a|ε
                nfa = build_nfa_union(nfa, build_nfa_epsilon())
            else:
                break
        return nfa

    def _parse_atom(self):
        """Parse: single char, escaped char, character class, or '(' expr ')'"""
        ch = self.peek()
        if ch is None:
            raise ValueError("Unexpected end of regex")

        if ch == '(':
            self.advance()  # consume '('
            nfa = self._parse_union()
            if self.peek() != ')':
                raise ValueError(f"Expected ')', got '{self.peek()}' at position {self.pos}")
            self.advance()  # consume ')'
            return nfa

        if ch == '[':
            return self._parse_char_class()

        if ch == '\\':
            self.advance()
            ch = self.advance()
            if ch is None:
                raise ValueError("Unexpected end after backslash")
            return build_nfa_single_char(ch)

        # Treat the following regex metacharacters as literal when unescaped
        # in this simple regex dialect
        # (Occurring standalone is a usage error; we handle gracefully as literal)
        if ch in '*+|?)':
            # These are postfix operators — standalone is a user error,
            # but for PL/0 token patterns we treat them as literals
            self.advance()
            return build_nfa_single_char(ch)

        self.advance()
        return build_nfa_single_char(ch)

    def _parse_char_class(self):
        """Parse [abc] or [a-z] or [0-9].

        Builds: union of all characters in the class.
        """
        self.advance()  # consume '['
        chars = []
        while self.peek() is not None and self.peek() != ']':
            ch = self.advance()
            if self.peek() == '-' and self.pos + 1 < len(self.pattern) and self.pattern[self.pos + 1] != ']':
                # Range: a-z
                self.advance()  # consume '-'
                end_ch = self.advance()
                for c in range(ord(ch), ord(end_ch) + 1):
                    chars.append(chr(c))
            else:
                chars.append(ch)

        if self.peek() != ']':
            raise ValueError(f"Unclosed character class at position {self.pos}")
        self.advance()  # consume ']'

        if not chars:
            raise ValueError("Empty character class")

        # Build union of all characters
        nfa = build_nfa_single_char(chars[0])
        for c in chars[1:]:
            nfa = build_nfa_union(nfa, build_nfa_single_char(c))
        return nfa


# ── Convenience function ───────────────────────────────────────────────

def regex_to_nfa(pattern):
    """Convert a regular expression string to an NFA.

    Args:
        pattern: regex string

    Returns:
        NFA object

    Examples:
        >>> nfa = regex_to_nfa("a(b|c)*")
        >>> nfa = regex_to_nfa("[a-z][a-z0-9]*")
        >>> nfa = regex_to_nfa("[0-9]+")
    """
    parser = RegexParser(pattern)
    return parser.parse()


# ── PL/0 specific regex → NFA constructions ─────────────────────────

PL0_REGEX_MAP = {
    "identifier": "[a-zA-Z][a-zA-Z0-9]*",
    "number": "[0-9]+",
    "plus": "\\+",
    "minus": "-",
    "times": "\\*",
    "div": "/",
    "assign": "::=",
    "eq": "=",
    "ne": "#",
    "lt": "<",
    "le": "<=",
    "gt": ">",
    "ge": ">=",
    "lparen": "\\(",
    "rparen": "\\)",
    "semicolon": ";",
    "comma": ",",
    "period": ".",
}


def build_pl0_lexer_nfas():
    """Build NFAs for all PL/0 token patterns.

    Returns:
        dict: token_name → NFA
    """
    nfas = {}
    for name, pattern in PL0_REGEX_MAP.items():
        try:
            nfas[name] = regex_to_nfa(pattern)
        except (ValueError, Exception) as e:
            print(f"Warning: could not build NFA for '{name}' ({pattern}): {e}")
    return nfas


# ── Test ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Test basic regex patterns
    test_patterns = [
        "a",
        "ab",
        "a|b",
        "a*",
        "(a|b)*",
        "a(b|c)*",
        "[a-z]",
        "[a-zA-Z][a-zA-Z0-9]*",
        "[0-9]+",
    ]

    for pat in test_patterns:
        try:
            nfa = regex_to_nfa(pat)
            print(f"  regex '{pat:25s}' → {nfa.summary()}")
        except Exception as e:
            print(f"  regex '{pat:25s}' → ERROR: {e}")

    # Test identifier NFA
    print("\n=== PL/0 Lexer NFAs ===")
    nfas = build_pl0_lexer_nfas()
    for name, nfa in nfas.items():
        print(f"  {name:12s}: {nfa.summary()}")
