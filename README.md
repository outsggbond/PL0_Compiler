# PL/0 Compiler

## 项目简介

本项目是桂林电子科技大学《编译原理课程设计》的完整实现，包含：

- **第3章** Flex/Bison 三个实验（字符频率统计、词法识别、计算器）
- **第4章** 手写词法分析器（DFA 实现，支持注释、错误恢复）
- **第5章** 两种语法分析器：自顶向下 LL(1)（递归下降/表驱动） + 自底向上 LR（SLR/LR(1)）
- **第6章** 两种语义分析：L-翻译模式（对应 LL）和 S-翻译模式（对应 LR），生成四元式中间代码和符号表

各章节加分项
第4章 词法分析 发现潜在错误或改进空间，并提出优化建议。
第5章 自顶向下（LL） 1. 生成语法分析树的可视化；2. 对输入文法进行左公因子或左递归消除的编程实现；3. 在检测语法错误的同时，提供修复建议或改进策略。
第5章 自底向上（LR） 能生成完整的语法分析树并可视化。
第6章 语义分析 1. 能够将四元式执行过程可视化，包括跳转控制流和临时变量使用情况；2. 借助AI可辅助生成分析过程图，但能解释四元式生成逻辑。
以上均已经实现

项目人：outsggbond

## 项目结构

```markdown
PL0_Compiler/
│
├── docs/                                 # 课程设计报告及参考资料
│   ├── Experiment_3.md
│   └── shortcut/                         # 报告图表、截图等素材
│       ├── exps1_1.png
│       ├── exps1_2.png
│       └── exps1_3.png
│
├── flex_bison_exps/                      # 第3章 Flex/Bison 三个实验
│   ├── task1_1_freq/
│   │   ├── freq.l
│   │   ├── lex.yy.c
│   │   ├── freq.exe                      # 编译生成
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
├── src/                                  # 核心编译器源代码
│   ├── lexer/                            # 词法分析器
│   │   ├── lexer.py
│   │   └── token.py
│   ├── parser_ll/                        # 自顶向下 LL(1) 语法分析器
│   │   ├── first_follow.py
│   │   ├── ll_parser.py
│   │   └── ll_table.py
│   ├── parser_lr/                        # 自底向上 LR 语法分析器
│   │   ├── lr_items.py
│   │   ├── lr_parser.py
│   │   └── lr_table.py
│   ├── semantic_ll/                      # L-翻译模式（对应 LL）
│   │   └── semantic_ll.py
│   ├── semantic_lr/                      # S-翻译模式（对应 LR）
│   │   └── semantic_lr.py
│   └── utils/                            # 工具模块
│       ├── quad_generator.py
│       └── symbol_table.py
│
├── input/                                # 测试用例输入
│   ├── correct/                          # 正确语法用例（来自文档）
│   │   ├── test1.txt
│   │   └── test2.txt
│   └── error/                            # 错误用例
│       ├── lexical_error.txt
│       ├── syntax_error.txt
│       └── semantic_error.txt
│
├── output/                               # 编译或运行输出
│   ├── tokens_out.txt
│   ├── quads_ll.txt
│   └── quads_lr.txt
│
├── README.md                             # 项目说明、编译运行方法
└── requirements.txt                      # Python 依赖
```

## 模块说明

**词法分析器 `src/lexer/`**
- `token.py` — PL/0 词法单元定义（TokenType 枚举 + Token 数据类）
- `lexer.py` — 基于 DFA 的词法分析器，支持注释识别和错误恢复

**自顶向下语法分析器 `src/parser_ll/`**
- `first_follow.py` — 计算 PL/0 文法的 FIRST / FOLLOW 集合
- `ll_table.py` — 构建 LL(1) 预测分析表
- `ll_parser.py` — LL(1) 递归下降语法分析器，生成语法分析树

**自底向上语法分析器 `src/parser_lr/`**
- `lr_items.py` — 构建 LR(0) 项集规范族及 GOTO 函数
- `lr_table.py` — 构建 SLR(1) ACTION / GOTO 表
- `lr_parser.py` — SLR(1) 移进-归约语法分析器，生成语法分析树

**语义分析**
- `src/semantic_ll/semantic_ll.py` — L-翻译模式，遍历 LL 语法树生成四元式及符号表
- `src/semantic_lr/semantic_lr.py` — S-翻译模式，在 LR 归约时执行语义动作，生成四元式及符号表

**工具模块 `src/utils/`**
- `symbol_table.py` — 作用域符号表，支持常量/变量/过程定义与嵌套作用域查找
- `quad_generator.py` — 四元式中间代码生成器 + QuadVM 虚拟机执行器，可可视化四元式执行过程

## 快速开始

项目仅依赖 Python 3.8+ 标准库，各模块均可通过 `python -m` 独立运行：

```bash
# 词法分析 — 输出 Token 序列
python -m src.lexer.lexer input/correct/test1.txt

# LL(1) 语法分析 — 输出语法分析树
python -m src.parser_ll.ll_parser input/correct/test1.txt

# LR 语法分析 — 输出语法分析树
python -m src.parser_lr.lr_parser input/correct/test1.txt

# LL 语义分析（L-翻译）— 输出符号表和四元式
python -m src.semantic_ll.semantic_ll input/correct/test1.txt

# LR 语义分析（S-翻译）— 输出符号表和四元式
python -m src.semantic_lr.semantic_lr input/correct/test1.txt
```

> 所有命令在 `PL0_Compiler/` 目录下执行。替换 `input/correct/test1.txt` 可测试其他用例，如 `input/error/lexical_error.txt`。

## 环境要求

- **Python 3.8+**（用于手写编译器）
- **C 编译器**：MinGW-w64（gcc）或 Visual Studio（用于编译 Flex/Bison 生成的 C 代码）

开发工具：:vscode
使用语言:python

