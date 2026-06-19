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
│   ├── Experiment_3.md             # 第3章 Flex/Bison 实验报告
│   ├── report.md                   # 课程设计综合报告
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
│       ├── output_manager.py            # 控制台输出自动镜像保存至 output/
│       ├── word_classification_table.py # 第4章 ① 单词分类表（Markdown/ASCII/JSON）
│       ├── lexer_flowchart.py           # 第4章 ②③ 状态转换图 + 词法识别流程图
│       ├── parse_tree_visualizer.py     # 第5章 解析树可视化（DOT/ASCII/HTML + LL/LR对比）
│       ├── lr_state_graph.py            # 第5章 LR 项目集自动机 + 活前缀路径
│       └── quad_visualizer.py           # 第6章 控制流图 + 四元式执行过程 + 临时变量分析
│
├── input/ # 测试用例输入
│   ├── correct/ # 正确输入 → 编译器产生正确的输出
│   │   ├── lexer.txt            # 词法分析正确用例（含标识符、数字、运算符、注释等）
│   │   ├── parser.txt           # 语法分析正确用例（完整 PL/0 程序）
│   │   └── semantic.txt         # 语义分析正确用例
│   └── error/ # 带有错误的输入 → 编译器给出错误提示
│       ├── lexer.txt            # 词法错误（非法字符等）
│       ├── parser_1.txt         # 语法错误（缺少分号）
│       ├── parser_2.txt         # 语法错误（括号不匹配）
│       ├── parser_3.txt         # 语法错误（关键字拼写错误）
│       ├── parser_4.txt         # 语法错误（begin/end 不匹配）
│       ├── semantic_1.txt       # 语义错误（未声明变量）
│       ├── semantic_2.txt       # 语义错误（重复声明）
│       ├── semantic_3.txt       # 语义错误（类型不匹配）
│       └── semantic_4.txt       # 语义错误（未定义过程）
│
├── output/ # 编译器输出（与 input/ 结构一一对应）
│   ├── correct/ # 正确输入对应的编译输出
│   │   ├── lexer.txt
│   │   ├── parser.txt
│   │   └── semantic.txt
│   └── error/ # 错误输入对应的错误报告
│       ├── lexer.txt
│       ├── parser_1.txt
│       ├── parser_2.txt
│       ├── parser_3.txt
│       ├── parser_4.txt
│       ├── semantic_1.txt
│       ├── semantic_2.txt
│       ├── semantic_3.txt
│       └── semantic_4.txt
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
| `output_manager.py` | 控制台输出自动镜像到 output/ 目录 | 纯文本 .txt |

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

项目依赖 Python 3.8+ 标准库（Python 部分）和 Flex/Bison + GCC（C 部分），各模块均可独立运行：

### 环境准备

```bash
# 进入项目根目录
cd PL0_Compiler

# 创建 Python 虚拟环境（可选，推荐）
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖（本项目仅使用标准库，此步可选）
pip install -r requirements.txt
```

### 第3章 Flex/Bison 实验

> **前置条件**：需要安装 Flex、Bison 和 GCC（MinGW-w64 或 Visual Studio）。
> Windows 下推荐使用 [win_flex_bison](https://github.com/lexxmark/winflexbison) 或 MSYS2 安装。

```bash
# === Task 1_1: 字符频率统计 ===
cd flex_bison_exps/task1_1_freq
flex freq.l                  # 生成 lex.yy.c
gcc lex.yy.c -o freq.exe     # 编译
./freq.exe test1_1_input.txt # 运行 → 输出 A-Z 字符频率百分比
cd ../..

# === Task 1_2: 词法识别 ===
cd flex_bison_exps/task1_2_token
flex token.l                 # 生成 lex.yy.c
gcc lex.yy.c -o token.exe    # 编译
./token.exe < test_1_2_input.txt  # 运行 → 输出 <单词/数字/符号> 分类结果
cd ../..

# === Task 1_3: 计算器 ===
cd flex_bison_exps/task1_3_calc
bison -d calc.y              # 生成 calc.tab.c 和 calc.tab.h
flex calc.l                  # 生成 lex.yy.c
gcc calc.tab.c lex.yy.c -o calc.exe  # 编译
./calc.exe < test_1_3_input.txt      # 运行 → 输出表达式计算过程和结果
cd ../..
```

### 第4章 词法分析（手写 DFA）

```bash
# 正确输入 → 输出 Token 序列（自动保存至 output/correct/lexer.txt）
python -m src.lexer.lexer input/correct/lexer.txt
# 错误输入 → 输出错误提示（自动保存至 output/error/lexer.txt）
python -m src.lexer.lexer input/error/lexer.txt
```

### 自动机算法（Regex → NFA → DFA → MinDFA）

```bash
# Regex → NFA（Thompson 构造法，支持 | * + ? [a-z] \转义）
python -m src.automata.regex_to_nfa

# NFA → DFA（子集构造法），可导入任意已构建的 NFA
python -m src.automata.dfa

# DFA → MinDFA（Hopcroft 最小化算法）— 完整流水线 + 最小化测试
python -m src.automata.dfa_minimizer

# 流水线可视化（NFA/DFA/MinDFA 的 DOT + ASCII 输出）
python -m src.automata.automata_visualizer

# （可选）安装 Graphviz 后将 DOT 渲染为 PNG
# dot -Tpng nfa.dot -o docs/shortcut/nfa.png
# dot -Tpng dfa.dot -o docs/shortcut/dfa.png
# dot -Tpng mindfa.dot -o docs/shortcut/mindfa.png
```

### 第5章 LL(1) 语法分析（自顶向下）

```bash
# 计算 FIRST / FOLLOW / SELECT 集 + LL(1) 预测分析表（无输入文件，内嵌 PL/0 文法）
python -m src.parser_ll.first_follow

# 构建 LL(1) 预测分析表 + 冲突检测
python -m src.parser_ll.ll_table

# 正确输入 → 递归下降解析 + 语法分析树 + DOT 可视化（自动保存至 output/correct/parser.txt）
python -m src.parser_ll.ll_parser input/correct/parser.txt

# 所有语法错误用例 → 语法错误修复建议（自动保存至 output/error/）
python -m src.parser_ll.ll_parser input/error/parser_1.txt  # 缺少分号
python -m src.parser_ll.ll_parser input/error/parser_2.txt  # 括号不匹配
python -m src.parser_ll.ll_parser input/error/parser_3.txt  # 关键字拼写错误
python -m src.parser_ll.ll_parser input/error/parser_4.txt  # begin/end 不匹配
```

### 第5章 LR 语法分析（自底向上）

```bash
# 构建 LR(0) 项集规范族 + SLR(1) ACTION/GOTO 表
python -m src.parser_lr.lr_table

# 正确输入 → SLR(1) 移进-归约解析 + 语法树 + 步骤追踪（自动保存至 output/correct/parser.txt）
python -m src.parser_lr.lr_parser input/correct/parser.txt

# 所有语法错误用例 → 语法错误信息（自动保存至 output/error/）
python -m src.parser_lr.lr_parser input/error/parser_1.txt  # 缺少分号
python -m src.parser_lr.lr_parser input/error/parser_2.txt  # 括号不匹配
python -m src.parser_lr.lr_parser input/error/parser_3.txt  # 关键字拼写错误
python -m src.parser_lr.lr_parser input/error/parser_4.txt  # begin/end 不匹配
```

### 第6章 语义分析

```bash
# === LL 语义分析（L-翻译模式）===
# 正确输入 → 遍历 LL 语法树，生成符号表和四元式（自动保存至 output/correct/semantic.txt）
python -m src.semantic_ll.semantic_ll input/correct/semantic.txt

# 语义错误输入 → 输出错误提示
python -m src.semantic_ll.semantic_ll input/error/semantic_1.txt  # 未声明变量
python -m src.semantic_ll.semantic_ll input/error/semantic_2.txt  # 重复声明
python -m src.semantic_ll.semantic_ll input/error/semantic_3.txt  # 类型不匹配
python -m src.semantic_ll.semantic_ll input/error/semantic_4.txt  # 未定义过程

# === LR 语义分析（S-翻译模式）===
# 正确输入 → 在 LR 归约时执行语义动作，生成符号表和四元式（自动保存至 output/correct/semantic.txt）
python -m src.semantic_lr.semantic_lr input/correct/semantic.txt

# 语义错误输入 → 输出错误提示
python -m src.semantic_lr.semantic_lr input/error/semantic_1.txt  # 未声明变量
python -m src.semantic_lr.semantic_lr input/error/semantic_2.txt  # 重复声明
python -m src.semantic_lr.semantic_lr input/error/semantic_3.txt  # 类型不匹配
python -m src.semantic_lr.semantic_lr input/error/semantic_4.txt  # 未定义过程
```

### 可视化工具

```bash
# 第4章 ① 单词分类表（Markdown / ASCII / JSON）
python -m src.utils.word_classification_table

# 第4章 ②③ 状态转换图 + 词法识别流程图（DOT + ASCII）
python -m src.utils.lexer_flowchart

# 第5章 解析树可视化（LL + LR 语法树对比，DOT / ASCII / 缩进 / JSON / HTML）
python -m src.utils.parse_tree_visualizer
python -m src.utils.parse_tree_visualizer input/correct/parser.txt  # 指定输入文件

# 第5章 LR 项目集自动机 + 活前缀状态转换图（DOT / ASCII / JSON）
python -m src.utils.lr_state_graph

# 第6章 控制流图 + 四元式执行过程 + 临时变量分析（DOT CFG + 执行表格）
python -m src.utils.quad_visualizer
python -m src.utils.quad_visualizer input/correct/semantic.txt  # 指定输入文件

# === （可选）Graphviz 渲染 DOT 图为 PNG ===
# dot -Tpng parse_tree_ll.dot -o docs/shortcut/parse_tree_ll.png
# dot -Tpng parse_tree_lr.dot -o docs/shortcut/parse_tree_lr.png
# dot -Tpng lr_automaton.dot -o docs/shortcut/lr_automaton.png
# dot -Tpng cfg.dot -o docs/shortcut/control_flow_graph.png
# dot -Tpng quad_execution.dot -o docs/shortcut/quad_execution.png
```

### 一键测试脚本

```bash
# 依次运行所有正确输入用例（词法 → LL语法 → LR语法 → LL语义 → LR语义）
python -m src.lexer.lexer input/correct/lexer.txt
python -m src.parser_ll.ll_parser input/correct/parser.txt
python -m src.parser_lr.lr_parser input/correct/parser.txt
python -m src.semantic_ll.semantic_ll input/correct/semantic.txt
python -m src.semantic_lr.semantic_lr input/correct/semantic.txt

# 依次运行所有错误输入用例（验证错误检测与恢复能力）
python -m src.lexer.lexer input/error/lexer.txt
python -m src.parser_ll.ll_parser input/error/parser_1.txt
python -m src.parser_ll.ll_parser input/error/parser_2.txt
python -m src.parser_ll.ll_parser input/error/parser_3.txt
python -m src.parser_ll.ll_parser input/error/parser_4.txt
python -m src.semantic_ll.semantic_ll input/error/semantic_1.txt
python -m src.semantic_ll.semantic_ll input/error/semantic_2.txt
python -m src.semantic_ll.semantic_ll input/error/semantic_3.txt
python -m src.semantic_ll.semantic_ll input/error/semantic_4.txt
```

> **说明**：所有命令在 `PL0_Compiler/` 目录下执行。正确输入文件位于 `input/correct/`，产生正确的编译输出；错误输入文件位于 `input/error/`，产生对应的错误提示信息。**控制台输出自动镜像保存至 `output/` 目录**（结构与 `input/` 一一对应），无需手动 `>` 重定向。`lr_parser` 模块额外生成 `trace.csv`、`errors.csv` 和 `parse_tree.png`。

## 环境要求

- **Python 3.8+**（用于手写编译器）
- **Graphviz**（可选，用于渲染 DOT 输出为 PNG/SVG 图片）
- **C 编译器**：MinGW-w64（gcc）或 Visual Studio（用于编译 Flex/Bison 生成的 C 代码）

开发工具：VSCode
使用语言：Python、C
