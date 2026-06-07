# PL/0 Compiler

## 项目简介

本项目是桂林电子科技大学《编译原理课程设计》的完整实现，包含：

- **第3章** Flex/Bison 三个实验（字符频率统计、词法识别、计算器）
- **第4章** 手写词法分析器（DFA 实现，支持注释、错误恢复）
- **第5章** 两种语法分析器：自顶向下 LL(1)（递归下降/表驱动） + 自底向上 LR（SLR/LR(1)）
- **第6章** 两种语义分析：L-翻译模式（对应 LL）和 S-翻译模式（对应 LR），生成四元式中间代码和符号表

各章节加分项已全部实现：

| 章节 | 加分项 | 状态 |
|------|--------|------|
| 第4章 词法分析 | 单词分类表、状态转换图、词法识别流程图 | ✅ |
| 第4章 词法分析 | 正规式 → NFA → DFA → DFA最小化（Thompson + 子集构造 + Hopcroft） | ✅ |
| 第4章 词法分析 | 发现潜在错误或改进空间，并提出优化建议 | ✅ |
| 第5章 自顶向下（LL） | 生成语法分析树的可视化（DOT/ASCII/HTML） | ✅ |
| 第5章 自顶向下（LL） | SELECT 集计算与 LL(1) 预测分析表输出 | ✅ |
| 第5章 自顶向下（LL） | 左公因子/左递归消除的编程实现 + 语法错误修复建议 | ✅ |
| 第5章 自底向上（LR） | 生成完整的语法分析树并可视化 | ✅ |
| 第5章 自底向上（LR） | LR 项目集自动机及活前缀状态转换图 | ✅ |
| 第5章 自底向上（LR） | LR 移进-归约步骤逐步输出 | ✅ |
| 第6章 语义分析 | 四元式执行过程可视化（控制流图 + 跳转控制流 + 临时变量分析） | ✅ |

项目人：outsggbond

## 项目结构

```markdown
PL0_Compiler/
│
├── docs/ # 课程设计报告及参考资料
│   ├── Experiment_3.md
│   └── shortcut/ # 报告图表、截图等素材
│       ├── exps1_1.png
│       ├── exps1_2.png
│       └── exps1_3.png
│
├── flex_bison_exps/ # 第3章 Flex/Bison 三个实验
│   ├── task1_1_freq/
│   │   ├── freq.l
│   │   ├── lex.yy.c
│   │   ├── freq.exe
│   │   └── test1_1_input.txt
│   ├── task1_2_token/
│   │   ├── token.l
│   │   ├── lex.yy.c
│   │   ├── token.exe
│   │   └── test_1_2_input.txt
│   └── task1_3_calc/
│       ├── calc.l
│       ├── calc.y
│       ├── calc.tab.c
│       ├── calc.tab.h
│       ├── lex.yy.c
│       ├── calc.exe
│       └── test_1_3_input.txt
│
├── src/ # 核心编译器源代码
│   ├── automata/ # 自动机算法：Regex → NFA → DFA → MinDFA
│   │   ├── nfa.py                  # NFA 类 + ε闭包 + Thompson 构造辅助函数
│   │   ├── regex_to_nfa.py         # 正则表达式解析器 → NFA（支持 | * + ? [a-z] \转义）
│   │   ├── dfa.py                  # DFA 类 + 子集构造法（NFA → DFA）
│   │   ├── dfa_minimizer.py        # Hopcroft DFA 最小化算法
│   │   └── automata_visualizer.py  # NFA/DFA/MinDFA 可视化（DOT + ASCII）
│   │
│   ├── lexer/ # 词法分析器
│   │   ├── lexer.py
│   │   └── token.py
│   │
│   ├── parser_ll/ # 自顶向下 LL(1) 语法分析器
│   │   ├── first_follow.py         # FIRST / FOLLOW / SELECT 集计算 + LL(1) 预测表
│   │   ├── ll_parser.py            # 递归下降解析器 + 语法树 + DOT 可视化
│   │   └── ll_table.py             # LL(1) 预测分析表构建
│   │
│   ├── parser_lr/ # 自底向上 LR 语法分析器
│   │   ├── lr_items.py             # LR(0) 项集规范族 + GOTO 函数
│   │   ├── lr_parser.py            # SLR(1) 移进-归约解析器 + 语法树 + 步骤追踪
│   │   └── lr_table.py             # SLR(1) ACTION/GOTO 表构建
│   │
│   ├── semantic_ll/ # L-翻译模式（对应 LL）
│   │   └── semantic_ll.py          # 遍历 LL 语法树生成四元式及符号表
│   │
│   ├── semantic_lr/ # S-翻译模式（对应 LR）
│   │   └── semantic_lr.py          # 在 LR 归约时执行语义动作，生成四元式及符号表
│   │
│   └── utils/ # 工具与可视化模块
│       ├── symbol_table.py              # 作用域符号表（嵌套作用域查找）
│       ├── quad_generator.py            # 四元式生成器 + QuadVM 虚拟机
│       ├── word_classification_table.py # 第4章 ① 单词分类表（Markdown/ASCII/JSON）
│       ├── lexer_flowchart.py           # 第4章 ②③ 状态转换图 + 词法识别流程图
│       ├── parse_tree_visualizer.py     # 第5章 解析树可视化（DOT/ASCII/HTML + LL/LR对比）
│       ├── lr_state_graph.py            # 第5章 LR 项目集自动机 + 活前缀路径
│       └── quad_visualizer.py           # 第6章 控制流图 + 四元式执行过程 + 临时变量分析
│
├── input/ # 测试用例输入
│   ├── correct/ # 正确语法用例
│   │   ├── test1.txt
│   │   └── test2.txt
│   └── error/ # 错误用例
│       ├── lexical_error.txt
│       ├── syntax_error.txt
│       └── semantic_error.txt
│
├── output/ # 编译或运行输出
│   ├── tokens_out.txt
│   ├── quads_ll.txt
│   └── quads_lr.txt
│
├── README.md
└── requirements.txt
```

## 模块说明

### 自动机算法 `src/automata/`

| 文件 | 功能 | 算法 |
|------|------|------|
| `nfa.py` | NFA 类 + ε闭包 + 基本构造（单字符/连接/选择/星闭包/正闭包） | Thompson 构造法 |
| `regex_to_nfa.py` | 正则表达式解析器，支持 `\|` `*` `+` `?` `[a-z]` `\`转义 | 递归下降 |
| `dfa.py` | DFA 类 + NFA→DFA 转换 | 子集构造法 |
| `dfa_minimizer.py` | DFA 最小化 | Hopcroft 算法 |
| `automata_visualizer.py` | NFA/DFA/MinDFA 三种图的 DOT + ASCII 输出 | — |

验证示例：
- `[a-z][a-z0-9]*`（标识符） → NFA 185状态 → DFA 63状态 → **MinDFA 2状态**
- `[0-9]+`（数字） → NFA 41状态 → DFA 21状态 → **MinDFA 2状态**
- `(a\|b)*abb` → NFA 11状态 → DFA 5状态 → **MinDFA 4状态**

### 词法分析器 `src/lexer/`

- `token.py` — PL/0 词法单元定义（TokenType 枚举 + Token 数据类）
- `lexer.py` — 基于 DFA 的词法分析器，支持注释 (`//` `/* */`) 识别和恐慌模式错误恢复

### 自顶向下语法分析器 `src/parser_ll/`

- `first_follow.py` — 计算 FIRST / FOLLOW / **SELECT** 集合 + **LL(1) 预测分析表** + LL(1) 条件验证
- `ll_table.py` — 构建 LL(1) 预测分析表
- `ll_parser.py` — LL(1) 递归下降语法分析器，生成语法分析树 + **DOT 可视化** + 左递归/左公因子分析 + 语法错误修复建议

### 自底向上语法分析器 `src/parser_lr/`

- `lr_items.py` — 构建 LR(0) 项集规范族（109状态/259转移边）及 GOTO 函数
- `lr_table.py` — 构建 SLR(1) ACTION / GOTO 表
- `lr_parser.py` — SLR(1) 移进-归约语法分析器 + **步骤追踪输出** + DOT 可视化

### 语义分析

- `src/semantic_ll/semantic_ll.py` — L-翻译模式，遍历 LL 语法树生成四元式及符号表
- `src/semantic_lr/semantic_lr.py` — S-翻译模式，在 LR 归约时执行语义动作，生成四元式及符号表

### 可视化工具 `src/utils/`

| 文件 | 对应实验要求 | 输出格式 |
|------|-------------|---------|
| `word_classification_table.py` | 第4章 ① 单词分类表 | Markdown / ASCII / JSON |
| `lexer_flowchart.py` | 第4章 ②③ 状态转换图 + 词法识别流程图 | DOT + ASCII |
| `parse_tree_visualizer.py` | 第5章 LL/LR 语法树 | DOT / ASCII / 缩进 / JSON / **交互式HTML** |
| `lr_state_graph.py` | 第5章 LR 项目集自动机 + 活前缀路径 | DOT / ASCII / JSON |
| `quad_visualizer.py` | 第6章 控制流图 + 四元式执行 + 临时变量分析 | DOT CFG + 执行表格 |
| `symbol_table.py` | 符号表管理 | 控制台表格 |
| `quad_generator.py` | 四元式生成 + QuadVM 虚拟机 | 控制台 + 列表导出 |

## PL/0 语法

```
<程序>            ::= <分程序> .
<分程序>          ::= [ <常量说明部分> ] [ <变量说明部分> ] [ <过程说明部分> ] <语句>
<常量说明部分>    ::= const <常量定义> { , <常量定义> } ;
<常量定义>        ::= <标识符> = <无符号整数>
<变量说明部分>    ::= var <标识符> { , <标识符> } ;
<过程说明部分>    ::= <过程首部> <分程序> { ; <过程说明部分> } ;
<过程首部>        ::= procedure <标识符> ;
<语句>            ::= <赋值语句> | <条件语句> | <当型循环语句> | <过程调用语句> | <读语句> | <写语句> | <复合语句> | <空语句>
<赋值语句>        ::= <标识符> := <表达式>
<复合语句>        ::= begin <语句> { ; <语句> } end
<空语句>          ::= ε
<条件>            ::= <表达式> <关系运算符> <表达式> | odd <表达式>
<表达式>          ::= [ + | - ] <项> { <加减运算符> <项> }
<项>              ::= <因子> { <乘除运算符> <因子> }
<因子>            ::= <标识符> | <无符号整数> | '(' <表达式> ')'
<加减运算符>      ::= + | -
<乘除运算符>      ::= * | /
<关系运算符>      ::= = | # | < | <= | > | >=
<条件语句>        ::= if <条件> then <语句>
<过程调用语句>    ::= call <标识符>
<当型循环语句>    ::= while <条件> do <语句>
<读语句>          ::= read '(' <标识符> { , <标识符> } ')' ;
<写语句>          ::= write '(' <表达式> { , <表达式> } ')' ;
```

## 一、L翻译模式（自顶向下，LL(1)）

### 属性定义

- **综合属性**：`val`, `addr`, `code`, `type`, `width`
- **继承属性**：`true`, `false`, `next`, `offset`, `inh`

### 辅助函数

- `newtemp()`：生成新临时变量
- `newlabel()`：生成新标号
- `label(L)`：将下一条指令的标号赋给L
- `gen(code)`：生成三地址指令

### 声明语句的L翻译模式

```
P → { offset = 0 } D

D → T id ; { enter(id.lexval, T.type, offset); offset = offset + T.width } D

D → ε

T → int   { T.type = int; T.width = 4; }
T → real  { T.type = real; T.width = 8; }
```

### 赋值语句的L翻译模式

```
S → id = E ; { gen(id.lexeme '=' E.addr); }

E → E1 + T   { E.addr = newtemp(); gen(E.addr '=' E1.addr '+' T.addr); }
E → T        { E.addr = T.addr; }
T → T1 * F   { T.addr = newtemp(); gen(T.addr '=' T1.addr '*' F.addr); }
T → F        { T.addr = F.addr; }
F → ( E )    { F.addr = E.addr; }
F → id       { F.addr = id.lexeme; }
F → number   { F.addr = number.val; }
```

### 布尔表达式的L翻译模式（跳转代码）

```
B → E1 rop E2
    { gen('if ' E1.addr rop E2.addr 'goto ' B.true);
      gen('goto ' B.false); }

B → true   { gen('goto ' B.true); }
B → false  { gen('goto ' B.false); }

B → ( B1 ) { B1.true = B.true; B1.false = B.false; }

B → ┑ B1   { B1.true = B.false; B1.false = B.true; }

B → B1 ∨ B2
    { B1.true = B.true;
      B1.false = newlabel();
      B2.true = B.true;
      B2.false = B.false;
      label(B1.false); }

B → B1 ∧ B2
    { B1.true = newlabel();
      B1.false = B.false;
      B2.true = B.true;
      B2.false = B.false;
      label(B1.true); }
```

### 控制语句的L翻译模式

```
S → if B then S1 else S2
    { B.true = newlabel(); B.false = newlabel();
      label(B.true);
      S1.next = S.next;
      gen('goto ' S.next);
      label(B.false);
      S2.next = S.next; }

S → if B then S1
    { B.true = newlabel(); B.false = S.next;
      label(B.true);
      S1.next = S.next; }

S → while B do S1
    { B.begin = newlabel();
      label(B.begin);
      B.true = newlabel(); B.false = S.next;
      label(B.true);
      S1.next = B.begin;
      gen('goto ' B.begin); }

S → S1 S2
    { S1.next = newlabel();
      label(S1.next);
      S2.next = S.next; }
```

---

## 二、S翻译模式（自底向上，LR + 回填）

### 属性定义（仅综合属性）

- `E.truelist`, `E.falselist`：待回填的真假跳转指令列表
- `S.nextlist`：待回填的后继指令列表
- `M.gotostm`：标记非终结符记录的下一条指令地址

### 辅助函数

- `makelist(i)`：创建只包含指令i的列表
- `merge(l1,l2)`：合并两个列表
- `backpatch(p, i)`：将列表p中所有指令的目标标号填充为i
- `nextstm`：下一条指令的地址
- `gen(code)`：生成指令，nextstm加1

### 布尔表达式的S翻译模式（回填）

```
B → E1 rop E2
    { B.truelist = makelist(nextstm);
      B.falselist = makelist(nextstm+1);
      gen('if ' E1.addr rop E2.addr 'goto _');
      gen('goto _'); }

B → true
    { B.truelist = makelist(nextstm);
      gen('goto _'); }

B → false
    { B.falselist = makelist(nextstm);
      gen('goto _'); }

B → ( B1 )
    { B.truelist = B1.truelist; B.falselist = B1.falselist; }

B → ┑ B1
    { B.truelist = B1.falselist; B.falselist = B1.truelist; }

B → B1 ∨ M B2
    { backpatch(B1.falselist, M.gotostm);
      B.truelist = merge(B1.truelist, B2.truelist);
      B.falselist = B2.falselist; }

B → B1 ∧ M B2
    { backpatch(B1.truelist, M.gotostm);
      B.truelist = B2.truelist;
      B.falselist = merge(B1.falselist, B2.falselist); }

M → ε
    { M.gotostm = nextstm; }
```

### 控制语句的S翻译模式（回填）

```
S → if E then M1 S1 N else M2 S2
    { backpatch(E.truelist, M1.gotostm);
      backpatch(E.falselist, M2.gotostm);
      S.nextlist = merge(merge(S1.nextlist, N.nextlist), S2.nextlist); }

N → ε
    { N.nextlist = makelist(nextstm);
      gen('goto _'); }

M → ε
    { M.gotostm = nextstm; }

S → while M1 E do M2 S1
    { backpatch(S1.nextlist, M1.gotostm);
      backpatch(E.truelist, M2.gotostm);
      S.nextlist = E.falselist;
      gen('goto ' M1.gotostm); }

S → S1 M S2
    { backpatch(S1.nextlist, M.gotostm);
      S.nextlist = S2.nextlist; }
```

### 赋值语句的S翻译模式（栈操作）

```
E' → E   { print(stack[top].val); }

E → E1 + T   { stack[top-2].val = stack[top-2].val + stack[top].val; top = top-2; }

T → T1 * F   { stack[top-2].val = stack[top-2].val * stack[top].val; top = top-2; }

F → ( E )    { stack[top-2].val = stack[top-1].val; top = top-2; }

F → id       { stack[top].val = id.lexval; }
```

## 快速开始

项目仅依赖 Python 3.8+ 标准库，各模块均可通过 `python -m` 独立运行：

```bash
# === 词法分析 ===
# 输出 Token 序列
python -m src.lexer.lexer input/correct/test1.txt

# === 自动机算法 ===
# Regex → NFA → DFA → MinDFA 完整流水线
python -m src.automata.regex_to_nfa      # Regex → NFA
python -m src.automata.dfa_minimizer     # 完整流水线 + 最小化测试
python -m src.automata.automata_visualizer # 流水线可视化

# === LL(1) 语法分析 ===
# 输出 FIRST / FOLLOW / SELECT 集 + LL(1) 预测表
python -m src.parser_ll.first_follow
# 输出语法分析树 + DOT 可视化
python -m src.parser_ll.ll_parser input/correct/test1.txt

# === LR 语法分析 ===
# 输出 LR 项目集 + SLR(1) 表
python -m src.parser_lr.lr_table
# 输出语法分析树 + 移进-归约步骤追踪
python -m src.parser_lr.lr_parser input/correct/test1.txt

# === 语义分析 ===
# LL 语义分析（L-翻译）— 输出符号表和四元式
python -m src.semantic_ll.semantic_ll input/correct/test1.txt
# LR 语义分析（S-翻译）— 输出符号表和四元式
python -m src.semantic_lr.semantic_lr input/correct/test1.txt

# === 可视化工具 ===
# 单词分类表
python -m src.utils.word_classification_table
# 词法分析流程图 + DFA 状态转换图
python -m src.utils.lexer_flowchart
# 解析树可视化（LL + LR 对比）
python -m src.utils.parse_tree_visualizer
# LR 项目集自动机 + 状态转换图
python -m src.utils.lr_state_graph
# 四元式执行过程 + 控制流图 + 临时变量分析
python -m src.utils.quad_visualizer
```

> 所有命令在 `PL0_Compiler/` 目录下执行。替换 `input/correct/test1.txt` 可测试其他用例，如 `input/error/lexical_error.txt`。

## 环境要求

- **Python 3.8+**（用于手写编译器）
- **Graphviz**（可选，用于渲染 DOT 输出为 PNG/SVG 图片）
- **C 编译器**：MinGW-w64（gcc）或 Visual Studio（用于编译 Flex/Bison 生成的 C 代码）

开发工具：VSCode
使用语言：Python
