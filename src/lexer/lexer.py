# src/lexer/lexer.py
import re
from .token import Token, TokenType

class Lexer:
    keywords = {
        'const': TokenType.CONST, 'var': TokenType.VAR, 'procedure': TokenType.PROCEDURE,
        'begin': TokenType.BEGIN, 'end': TokenType.END, 'if': TokenType.IF,
        'then': TokenType.THEN, 'while': TokenType.WHILE, 'do': TokenType.DO,
        'call': TokenType.CALL, 'read': TokenType.READ, 'write': TokenType.WRITE,
        'odd': TokenType.ODD,
    }
    operators = {
        '+': TokenType.PLUS, '-': TokenType.MINUS, '*': TokenType.TIMES, '/': TokenType.DIV,
        '=': TokenType.EQ, '#': TokenType.NE, '<': TokenType.LT, '<=': TokenType.LE,
        '>': TokenType.GT, '>=': TokenType.GE, ':=': TokenType.ASSIGN,
    }
    delimiters = {
        '(': TokenType.LPAREN, ')': TokenType.RPAREN, ';': TokenType.SEMICOLON,
        ',': TokenType.COMMA, '.': TokenType.PERIOD,
    }

    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.length = len(source)

    def error(self, msg):
        print(f"Lexical error at line {self.line}, col {self.col}: {msg}")
        return Token(TokenType.ERROR, msg, self.line, self.col)

    def peek(self):
        if self.pos >= self.length:
            return '\0'
        return self.source[self.pos]

    def advance(self):
        ch = self.peek()
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def skip_whitespace(self):
        while self.peek() in ' \t\n\r':
            self.advance()

    def read_identifier(self):
        start = self.pos
        while self.peek().isalpha() or self.peek().isdigit() or self.peek() == '_':
            self.advance()
        ident = self.source[start:self.pos]
        # Check if it's a keyword first (keywords may exceed 8 chars)
        tok_type = self.keywords.get(ident)
        if tok_type is not None:
            return Token(tok_type, ident, self.line, self.col)
        if len(ident) > 8:
            self.error(f"Identifier '{ident}' exceeds 8 characters")
            return Token(TokenType.ERROR, ident, self.line, self.col)
        if ident[0].isdigit():
            self.error(f"Identifier cannot start with digit: '{ident}'")
            return Token(TokenType.ERROR, ident, self.line, self.col)
        return Token(TokenType.ID, ident, self.line, self.col)

    def read_number(self):
        start = self.pos
        while self.peek().isdigit():
            self.advance()
        num = self.source[start:self.pos]
        if len(num) > 8:
            self.error(f"Number '{num}' exceeds 8 digits")
        return Token(TokenType.NUMBER, int(num), self.line, self.col)

    def read_comment(self):
        # 单行注释 //
        if self.peek() == '/' and self.pos+1 < self.length and self.source[self.pos+1] == '/':
            self.advance(); self.advance()
            while self.peek() not in '\n\r\0':
                self.advance()
            return None
        # 多行注释 /*
        if self.peek() == '/' and self.pos+1 < self.length and self.source[self.pos+1] == '*':
            self.advance(); self.advance()
            while not (self.peek() == '*' and self.pos+1 < self.length and self.source[self.pos+1] == '/'):
                if self.peek() == '\0':
                    self.error("Unclosed comment")
                    return None
                self.advance()
            self.advance(); self.advance()  # skip */
            return None
        return None

    def get_next_token(self):
        while True:
            self.skip_whitespace()
            if self.pos >= self.length:
                return Token(TokenType.EOF, '', self.line, self.col)
            ch = self.peek()
            # 注释
            if ch == '/' and self.pos+1 < self.length and self.source[self.pos+1] in '/*':
                comment = self.read_comment()
                if comment is not None:
                    return comment
                continue
            # 标识符或关键字
            if ch.isalpha():
                return self.read_identifier()
            # 数字
            if ch.isdigit():
                return self.read_number()
            # 运算符/界符
            two_char = self.source[self.pos:self.pos+2]
            if two_char in ('<=', '>=', ':='):
                self.advance(); self.advance()
                return Token(self.operators[two_char], two_char, self.line, self.col)
            if ch in self.operators:
                self.advance()
                return Token(self.operators[ch], ch, self.line, self.col)
            if ch in self.delimiters:
                self.advance()
                return Token(self.delimiters[ch], ch, self.line, self.col)
            # 非法字符 -> 恐慌模式恢复
            self.error(f"Illegal character '{ch}'")
            self.advance()
            continue


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
        source = 'var x, y; begin x := 5; y := x + 1; write(y) end.'
        print(f"Usage: python -m src.lexer.lexer <source_file>")
        print(f"Using built-in test:\n---\n{source}\n---\n")
        output_path = None

    with tee_output(output_path):
        lexer = Lexer(source)
        while True:
            tok = lexer.get_next_token()
            print(tok)
            if tok.type == TokenType.EOF:
                break