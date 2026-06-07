# src/utils/parse_tree_visualizer.py
"""语法分析树可视化 (第5章加分项)

根据实验书要求：
- LL(1): 生成语法分析树的可视化
- LR: 生成完整的语法分析树并可视化

功能：
1. 解析树 → Graphviz DOT 格式 (带颜色编码)
2. 解析树 → ASCII 树形图 (控制台输出)
3. 解析树 → JSON (序列化)
4. 解析树 → HTML (可交互)
"""

import json


# ── 颜色方案 ────────────────────────────────────────────────────────
# 与 ll_parser.py / lr_parser.py 中的颜色保持一致
NODE_COLORS = {
    "nonterminal": "#E8F0FE",  # 浅蓝 — 非终结符
    "identifier":  "#FFF3CD",  # 浅黄 — 标识符
    "number":      "#D4EDDA",  # 浅绿 — 数字
    "operator":    "#F8D7DA",  # 浅红 — 运算符
    "keyword":     "#D1ECF1",  # 青色 — 关键字
    "delimiter":   "#E2E3E5",  # 浅灰 — 界符
    "other":       "#F5F5F5",  # 白色 — 其他
}

# 关键字集合
KEYWORD_SET = {
    "const", "var", "procedure", "begin", "end", "if", "then",
    "while", "do", "call", "read", "write", "odd",
}

# 运算符集合
OPERATOR_SET = {"+", "-", "*", "/", ":=", "=", "#", "<", "<=", ">", ">="}

# 界符集合
DELIMITER_SET = {"(", ")", ";", ",", "."}


def classify_node(node):
    """根据节点标签和值判断节点类型，返回颜色分类名。

    Args:
        node: ParseTreeNode 或 SyntaxTreeNode (有 .label, .value, .children)

    Returns:
        str: 颜色分类名
    """
    if hasattr(node, 'children') and node.children:
        return "nonterminal"

    label = getattr(node, 'label', '')
    value = getattr(node, 'value', None)

    if label in ('id', 'identifier') or value in KEYWORD_SET:
        if value in KEYWORD_SET:
            return "keyword"
        return "identifier"
    if label in ('num', 'number') or (isinstance(value, (int, float))):
        return "number"
    if value in OPERATOR_SET or label in ('+', '-', '*', '/', ':=', '=', '#', '<', '<=', '>', '>=', 'odd', 'RelOp'):
        return "operator"
    if value in DELIMITER_SET or label in ('(', ')', ';', ',', '.'):
        return "delimiter"
    if label in KEYWORD_SET:
        return "keyword"

    return "other"


class ParseTreeVisualizer:
    """统一的语法分析树可视化器，支持 LL 和 LR 两种树结构。

    两种树节点接口相同：
    - .label   : str
    - .value   : str/int/None
    - .children: list
    - .token   : Token or None (optional)
    """

    def __init__(self, tree, title="ParseTree"):
        """
        Args:
            tree: ParseTreeNode (LL) 或 SyntaxTreeNode (LR)
            title: 图标题
        """
        self.tree = tree
        self.title = title
        self._counter = 0

    # ── DOT 输出 ──────────────────────────────────────────────────

    def _reset_counter(self):
        self._counter = 0

    def _next_id(self):
        self._counter += 1
        return f"n{self._counter}"

    def to_dot(self, orientation="TB"):
        """将解析树转换为 Graphviz DOT 格式。

        Args:
            orientation: "TB" (从上到下) 或 "LR" (从左到右)

        Returns:
            str: DOT format string
        """
        self._reset_counter()
        lines = [
            f"// {self.title}",
            f"digraph {self.title.replace(' ', '_')} {{",
            f'  rankdir={orientation};',
            '  node [shape=box, style=filled, fontname="Courier New", fontsize=11];',
            '  edge [fontname="Courier New", fontsize=9];',
            '',
        ]

        def _walk(node, parent_id=None):
            nid = self._next_id()
            color_key = classify_node(node)
            fill = NODE_COLORS.get(color_key, NODE_COLORS["other"])

            label = getattr(node, 'label', '?')
            value = getattr(node, 'value', None)
            display = label
            if value is not None and str(value):
                display = f"{label}\\n{value}"

            lines.append(f'  {nid} [label="{display}", fillcolor="{fill}"];')
            if parent_id:
                lines.append(f'  {parent_id} -> {nid};')

            children = getattr(node, 'children', [])
            for child in children:
                if child is not None:
                    _walk(child, nid)

        if self.tree:
            _walk(self.tree)

        lines.append("}")
        return "\n".join(lines)

    # ── ASCII 树形图 ──────────────────────────────────────────────

    def to_ascii_tree(self):
        """生成 ASCII 树形图 (适合控制台输出)。

        Returns:
            str: Unicode 树形图
        """
        if self.tree is None:
            return "(null tree)"

        lines = []

        def _walk(node, prefix="", is_last=True, is_root=True):
            if is_root:
                connector = ""
                extension = ""
            elif is_last:
                connector = "└── "
                extension = "    "
            else:
                connector = "├── "
                extension = "│   "

            label = getattr(node, 'label', '?')
            value = getattr(node, 'value', None)
            display = label
            if value is not None and str(value):
                display = f"{label}:{value}"

            lines.append(f"{prefix}{connector}{display}")

            children = getattr(node, 'children', [])
            for i, child in enumerate(children):
                if child is not None:
                    is_last_child = (i == len(children) - 1)
                    child_prefix = prefix + extension
                    _walk(child, child_prefix, is_last_child, is_root=False)

        _walk(self.tree)
        return "\n".join(lines)

    # ── 缩进树 ────────────────────────────────────────────────────

    def to_indented_text(self):
        """生成缩进文本树 (简单风格)。

        Returns:
            str: 缩进文本
        """
        if self.tree is None:
            return "(null tree)"

        lines = []

        def _walk(node, indent=0):
            prefix = "  " * indent
            label = getattr(node, 'label', '?')
            value = getattr(node, 'value', None)
            val_str = f" [{value}]" if value is not None else ""
            lines.append(f"{prefix}{label}{val_str}")

            children = getattr(node, 'children', [])
            for child in children:
                if child is not None:
                    _walk(child, indent + 1)

        _walk(self.tree)
        return "\n".join(lines)

    # ── JSON 输出 ─────────────────────────────────────────────────

    def to_dict(self):
        """将解析树转换为嵌套字典。

        Returns:
            dict: 树结构字典
        """
        if self.tree is None:
            return None

        def _convert(node):
            result = {
                "label": getattr(node, 'label', '?'),
                "value": getattr(node, 'value', None),
                "type": classify_node(node),
            }
            children = getattr(node, 'children', [])
            if children:
                result["children"] = [_convert(c) for c in children if c is not None]
            else:
                result["children"] = []
            return result

        return _convert(self.tree)

    def to_json(self, indent=2):
        """将解析树转换为 JSON 字符串。

        Args:
            indent: 缩进空格数

        Returns:
            str: JSON 字符串
        """
        d = self.to_dict()
        return json.dumps(d, ensure_ascii=False, indent=indent)

    # ── HTML 交互式树 ─────────────────────────────────────────────

    def to_html(self):
        """生成可交互的 HTML 树形可视化 (可在浏览器中折叠/展开)。

        Returns:
            str: 完整 HTML 页面
        """
        tree_data = self.to_json()

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{self.title}</title>
<style>
  body {{ font-family: "Courier New", monospace; margin: 20px; background: #f5f5f5; }}
  h1 {{ color: #333; }}
  .tree {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
  .node {{ margin-left: 20px; border-left: 2px solid #ddd; padding-left: 10px; }}
  .node-label {{ cursor: pointer; font-weight: bold; padding: 4px 8px; border-radius: 4px; display: inline-block; }}
  .node-label:hover {{ opacity: 0.8; }}
  .node-value {{ color: #666; font-style: italic; margin-left: 8px; }}
  .children {{ display: block; }}
  .children.hidden {{ display: none; }}
  .toggle {{ cursor: pointer; margin-right: 4px; user-select: none; }}
  .nt {{ background: #E8F0FE; }} .id {{ background: #FFF3CD; }} .num {{ background: #D4EDDA; }}
  .op {{ background: #F8D7DA; }} .kw {{ background: #D1ECF1; }} .delim {{ background: #E2E3E5; }}
</style>
</head>
<body>
  <h1>📊 {self.title}</h1>
  <div class="tree" id="tree"></div>
  <script>
    const data = {tree_data};
    const colorMap = {{
      nonterminal: 'nt', identifier: 'id', number: 'num',
      operator: 'op', keyword: 'kw', delimiter: 'delim', other: ''
    }};
    function render(node) {{
      let html = '<div class="node">';
      html += '<span class="toggle" onclick="toggleNode(this)">▼</span>';
      html += `<span class="node-label ${{colorMap[node.type] || ''}}">${{node.label}}</span>`;
      if (node.value) html += `<span class="node-value">${{node.value}}</span>`;
      if (node.children && node.children.length > 0) {{
        html += '<div class="children">';
        node.children.forEach(c => html += render(c));
        html += '</div>';
      }}
      html += '</div>';
      return html;
    }}
    document.getElementById('tree').innerHTML = render(data);
    function toggleNode(el) {{
      const children = el.parentElement.querySelector('.children');
      if (children) {{
        children.classList.toggle('hidden');
        el.textContent = children.classList.contains('hidden') ? '▶' : '▼';
      }}
    }}
  </script>
</body>
</html>'''
        return html


def visualize_parse_tree(tree, output_format="ascii", title="ParseTree"):
    """便捷函数: 可视化一个解析树。

    Args:
        tree: ParseTreeNode 或 SyntaxTreeNode
        output_format: "ascii", "indent", "dot", "json", "html"
        title: 图标题

    Returns:
        str: 可视化结果
    """
    viz = ParseTreeVisualizer(tree, title)
    if output_format == "ascii":
        return viz.to_ascii_tree()
    elif output_format == "indent":
        return viz.to_indented_text()
    elif output_format == "dot":
        return viz.to_dot()
    elif output_format == "json":
        return viz.to_json()
    elif output_format == "html":
        return viz.to_html()
    else:
        return viz.to_ascii_tree()


# ── 比较 LL 和 LR 树 ────────────────────────────────────────────────

def compare_trees(ll_tree, lr_tree):
    """并排比较 LL 和 LR 解析树的 ASCII 表示。

    Args:
        ll_tree: LL(1) 解析树
        lr_tree: LR 解析树

    Returns:
        str: 并排比较文本
    """
    ll_lines = visualize_parse_tree(ll_tree, "ascii", "LL Parse Tree").split("\n")
    lr_lines = visualize_parse_tree(lr_tree, "ascii", "LR Parse Tree").split("\n")

    max_lines = max(len(ll_lines), len(lr_lines))
    max_ll_len = max((len(l) for l in ll_lines), default=0) + 4
    max_lr_len = max((len(l) for l in lr_lines), default=0)

    result = []
    result.append("=" * (max_ll_len + max_lr_len + 7))
    result.append(f"{'LL(1) Parse Tree':^{max_ll_len}s}  ||  {'LR Parse Tree':^{max_lr_len}s}")
    result.append("-" * (max_ll_len + max_lr_len + 7))

    for i in range(max_lines):
        ll_line = ll_lines[i] if i < len(ll_lines) else ""
        lr_line = lr_lines[i] if i < len(lr_lines) else ""
        result.append(f"{ll_line:<{max_ll_len}s}  ||  {lr_line}")

    result.append("=" * (max_ll_len + max_lr_len + 7))
    return "\n".join(result)


# ── 测试入口 ────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    from ..lexer.lexer import Lexer

    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            source = f.read()
    else:
        source = 'const n=10; var x; begin x:=n; write(x) end.'
        print(f"Usage: python -m src.utils.parse_tree_visualizer <source_file>")
        print(f"Using built-in test:\n---\n{source}\n---\n")

    # LL 解析
    from ..parser_ll.ll_parser import LLParser
    lexer = Lexer(source)
    parser = LLParser(lexer)
    ll_tree, errors = parser.parse()
    if errors:
        for e in errors:
            print(f"  [LL Error] {e}")

    if ll_tree:
        print("\n=== LL ASCII Tree ===")
        print(visualize_parse_tree(ll_tree, "ascii", "LL(1) Parse Tree"))

        print("\n=== LL DOT ===")
        print(visualize_parse_tree(ll_tree, "dot"))

        print("\n=== LL JSON ===")
        print(visualize_parse_tree(ll_tree, "json"))

    # LR 解析
    from ..parser_lr.lr_parser import LRParser
    lexer2 = Lexer(source)
    lr_parser = LRParser(lexer2)
    lr_tree, lr_errors = lr_parser.parse()
    if lr_errors:
        for e in lr_errors:
            print(f"  [LR Error] {e}")

    if lr_tree:
        print("\n=== LR ASCII Tree ===")
        print(visualize_parse_tree(lr_tree, "ascii", "LR Parse Tree"))

    if ll_tree and lr_tree:
        print("\n=== Comparison ===")
        print(compare_trees(ll_tree, lr_tree))
