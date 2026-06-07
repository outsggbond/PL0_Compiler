# src/lexer/token.py
from enum import Enum, auto

class TokenType(Enum):
    # 关键字
    CONST = auto()
    VAR = auto()
    PROCEDURE = auto()
    BEGIN = auto()
    END = auto()
    IF = auto()
    THEN = auto()
    WHILE = auto()
    DO = auto()
    CALL = auto()
    READ = auto()
    WRITE = auto()
    ODD = auto()
    # 运算符
    PLUS = auto()    # +
    MINUS = auto()   # -
    TIMES = auto()   # *
    DIV = auto()     # /
    ASSIGN = auto()  # :=
    EQ = auto()      # =
    NE = auto()      # #
    LT = auto()      # <
    LE = auto()      # <=
    GT = auto()      # >
    GE = auto()      # >=
    # 界符
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    SEMICOLON = auto() # ;
    COMMA = auto()   # ,
    PERIOD = auto()  # .
    # 其他
    ID = auto()
    NUMBER = auto()
    # 特殊
    EOF = auto()
    ERROR = auto()

class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}', line={self.line})"