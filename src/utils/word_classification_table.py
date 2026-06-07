# src/utils/word_classification_table.py
"""单词分类表 (必做可视化)

根据实验书第4章要求：
- 设计单词分类表
- 输出分析结果

生成 Markdown / ASCII 表格，展示词法分析器能识别的所有单词类别，
以及示例程序中出现的具体单词实例。
"""

import sys
sys.path.insert(0, '..')

from ..lexer.token import TokenType as TT


# ── 单词类别定义 ────────────────────────────────────────────────────
CATEGORY_INFO = [
    ("保留字", "keywords", [
        ("const", "const"), ("var", "var"), ("procedure", "procedure"),
        ("begin", "begin"), ("end", "end"), ("if", "if"),
        ("then", "then"), ("while", "while"), ("do", "do"),
        ("call", "call"), ("read", "read"), ("write", "write"),
        ("odd", "odd"),
    ]),
    ("运算符", "operators", [
        ("+", "PLUS"), ("-", "MINUS"), ("*", "TIMES"), ("/", "DIV"),
        (":=", "ASSIGN"), ("=", "EQ"), ("#", "NE"),
        ("<", "LT"), ("<=", "LE"), (">", "GT"), (">=", "GE"),
    ]),
    ("界符", "delimiters", [
        ("(", "LPAREN"), (")", "RPAREN"), (";", "SEMICOLON"),
        (",", "COMMA"), (".", "PERIOD"),
    ]),
    ("标识符", "identifiers", [
        ("<ident>", "ID"),
    ]),
    ("无符号整数", "numbers", [
        ("<number>", "NUMBER"),
    ]),
    ("特殊", "special", [
        ("EOF", "EOF"), ("ERROR", "ERROR"),
    ]),
]

# 正规式描述 (用于报告)
PATTERN_DESCRIPTIONS = {
    "保留字":   r"const | var | procedure | begin | end | if | then | while | do | call | read | write | odd",
    "标识符":   r"letter ( letter | digit )*   (长度 ≤ 8)",
    "无符号整数": r"digit+   (长度 ≤ 8)",
    "运算符":   r"+ | - | * | / | := | = | # | < | <= | > | >=",
    "界符":    r"( | ) | ; | , | .",
}


class WordClassificationTable:
    """单词分类表 — 将词法分析结果按类别整理输出。"""

    def __init__(self, tokens=None):
        """
        Args:
            tokens: list of Token objects (from lexer), or None for empty table
        """
        self.tokens = tokens or []
        self._classified = {}  # category -> list of (value, token_type_name)

    def classify(self, tokens=None):
        """将 token 列表按类别归类。

        Args:
            tokens: list of Token (optional, uses self.tokens)

        Returns:
            dict: category_name -> list of unique (value, type_name) tuples
        """
        if tokens is not None:
            self.tokens = tokens

        self._classified = {
            "保留字": [],
            "运算符": [],
            "界符": [],
            "标识符": [],
            "无符号整数": [],
            "特殊": [],
        }

        seen = {k: set() for k in self._classified}

        keyword_tokens = {
            TT.CONST, TT.VAR, TT.PROCEDURE, TT.BEGIN, TT.END,
            TT.IF, TT.THEN, TT.WHILE, TT.DO, TT.CALL, TT.READ, TT.WRITE, TT.ODD,
        }
        operator_tokens = {
            TT.PLUS, TT.MINUS, TT.TIMES, TT.DIV, TT.ASSIGN,
            TT.EQ, TT.NE, TT.LT, TT.LE, TT.GT, TT.GE,
        }
        delimiter_tokens = {
            TT.LPAREN, TT.RPAREN, TT.SEMICOLON, TT.COMMA, TT.PERIOD,
        }

        for tok in self.tokens:
            tt = tok.type
            val = tok.value

            if tt in keyword_tokens:
                cat = "保留字"
            elif tt in operator_tokens:
                cat = "运算符"
            elif tt in delimiter_tokens:
                cat = "界符"
            elif tt == TT.ID:
                cat = "标识符"
            elif tt == TT.NUMBER:
                cat = "无符号整数"
            elif tt == TT.EOF:
                cat = "特殊"
            elif tt == TT.ERROR:
                cat = "特殊"
            else:
                continue

            entry = (str(val), tt.name)
            if entry not in seen[cat]:
                seen[cat].add(entry)
                self._classified[cat].append(entry)

        return self._classified

    def to_markdown(self, tokens=None):
        """生成 Markdown 格式的单词分类表。

        Returns:
            str: Markdown table
        """
        if tokens is not None or not self._classified:
            self.classify(tokens)

        lines = []
        lines.append("## 单词分类表")
        lines.append("")
        lines.append("| 类别 | 单词 | 正规式 |")
        lines.append("|------|------|--------|")

        for cat_name, cat_key, _ in CATEGORY_INFO:
            words = self._classified.get(cat_name, [])
            if words:
                # Show up to 15 unique words
                word_list = [w[0] for w in words[:15]]
                if len(words) > 15:
                    word_list.append(f"...({len(words)} total)")
                word_str = ", ".join(word_list)
            else:
                word_str = "(未出现)"
            pattern = PATTERN_DESCRIPTIONS.get(cat_name, "-")
            lines.append(f"| {cat_name} | {word_str} | `{pattern}` |")

        lines.append("")
        return "\n".join(lines)

    def to_ascii_table(self, tokens=None):
        """生成 ASCII 表格 (适合控制台输出)。

        Returns:
            str: ASCII formatted table
        """
        if tokens is not None or not self._classified:
            self.classify(tokens)

        lines = []
        sep = "=" * 72
        lines.append(sep)
        lines.append(f"{'单词分类表':^68s}")
        lines.append("-" * 72)
        lines.append(f"{'类别':<12s} {'单词':<54s}")
        lines.append("-" * 72)

        for cat_name, cat_key, _ in CATEGORY_INFO:
            words = self._classified.get(cat_name, [])
            if words:
                word_list = [w[0] for w in words[:12]]
                if len(words) > 12:
                    word_list.append(f"...({len(words)})")
                word_str = ", ".join(word_list)
            else:
                word_str = "(未出现)"
            lines.append(f"{cat_name:<12s} {word_str:<54s}")

        lines.append(sep)
        return "\n".join(lines)

    def to_table_dict(self, tokens=None):
        """返回结构化的字典形式，适合 JSON 导出。

        Returns:
            list[dict]: each dict with category, words, pattern
        """
        if tokens is not None or not self._classified:
            self.classify(tokens)

        result = []
        for cat_name, _, _ in CATEGORY_INFO:
            words = self._classified.get(cat_name, [])
            result.append({
                "category": cat_name,
                "words": [{"value": w[0], "type": w[1]} for w in words],
                "pattern": PATTERN_DESCRIPTIONS.get(cat_name, ""),
            })
        return result

    def display(self, tokens=None):
        """打印单词分类表到控制台。"""
        print(self.to_ascii_table(tokens))

    # ── 静态方法：仅理论分类表 (不依赖 token 流) ──────────────────

    @staticmethod
    def theoretical_table_markdown():
        """生成纯理论的单词分类表 (所有可能的词，不含实例)。"""
        lines = []
        lines.append("## PL/0 单词分类表 (理论)")
        lines.append("")
        lines.append("| 类别 | 单词 | 正规式 |")
        lines.append("|------|------|--------|")

        for cat_name, _, entries in CATEGORY_INFO:
            words = ", ".join(e[0] for e in entries)
            pattern = PATTERN_DESCRIPTIONS.get(cat_name, "-")
            lines.append(f"| {cat_name} | {words} | `{pattern}` |")

        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def theoretical_table_ascii():
        """生成纯理论的 ASCII 单词分类表。"""
        lines = []
        sep = "=" * 72
        lines.append(sep)
        lines.append(f"{'PL/0 单词分类表 (理论)':^68s}")
        lines.append("-" * 72)
        lines.append(f"{'类别':<12s} {'单词':<54s}")
        lines.append("-" * 72)

        for cat_name, _, entries in CATEGORY_INFO:
            words = ", ".join(e[0] for e in entries)
            lines.append(f"{cat_name:<12s} {words:<54s}")

        lines.append(sep)
        return "\n".join(lines)


# ── 测试入口 ────────────────────────────────────────────────────────
if __name__ == '__main__':
    # 打印理论分类表
    print(WordClassificationTable.theoretical_table_ascii())
    print()

    # 用内置测试代码生成实例分类表
    from ..lexer.lexer import Lexer

    source = 'const n=10; var x; begin x:=n; write(x) end.'
    lexer = Lexer(source)
    tokens = []
    while True:
        tok = lexer.get_next_token()
        tokens.append(tok)
        if tok.type == TT.EOF:
            break

    table = WordClassificationTable(tokens)
    table.display()
