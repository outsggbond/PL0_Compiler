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

PL0_Compiler/
│
├── docs/                                 # 课程设计报告及参考资料
│   ├── 编译原理课程设计报告.docx
│   ├── 编译原理课程设计报告.pdf
│   └── 任务要求/
│
├── flex_bison_exps/                      # 第3章 Flex/Bison 三个实验
│   ├── task1_1_freq/
│   │   ├── freq.l
│   │   ├── freq.exe                      # 编译生成
│   │   └── test_input.txt
│   ├── task1_2_token/
│   │   ├── token.l
│   │   └── token.exe
│   └── task1_3_calc/
│       ├── calc.l
│       ├── calc.y
│       └── calc.exe
│
├── src/                                  # 核心编译器源代码
│   ├── lexer/                            # 词法分析器
│   │   ├── lexer.py                      (或 .c)
│   │   └── token.py
│   ├── parser_ll/                        # 自顶向下 LL(1) 语法分析器
│   │   ├── ll_parser.py
│   │   ├── first_follow.py
│   │   └── ll_table.py
│   ├── parser_lr/                        # 自底向上 LR 语法分析器
│   │   ├── lr_parser.py
│   │   ├── lr_items.py
│   │   └── lr_table.py
│   ├── semantic_ll/                      # L-翻译模式（对应 LL）
│   │   ├── semantic_ll.py
│   │   ├── symbol_table.py
│   │   └── quad_generator.py
│   ├── semantic_lr/                      # S-翻译模式（对应 LR）
│   │   ├── semantic_lr.py
│   │   ├── symbol_table.py
│   │   └── quad_generator.py
│   └── main.py                           # 主入口，整合各模块
│
├── tests/                                # 测试用例
│   ├── correct/                          # 正确语法用例（来自文档）
│   │   ├── test1.txt
│   │   └── test2.txt
│   ├── error/                            # 错误用例
│   │   ├── lexical_error.txt
│   │   ├── syntax_error.txt
│   │   └── semantic_error.txt
│   └── output/                           # 预期输出
│
├── out/                                  # 编译或运行输出
│   ├── tokens_out.txt
│   ├── quads_ll.txt
│   └── quads_lr.txt
│
├── report/                               # 报告图表、截图等素材
│   ├── dfa.png
│   ├── ll_table.png
│   └── 等等...
│
├── README.md                             # 项目说明、编译运行方法
└── requirements.txt                      # Python 依赖

## 环境要求

- **Python 3.8+**（用于手写编译器）
- **C 编译器**：MinGW-w64（gcc）或 Visual Studio（用于编译 Flex/Bison 生成的 C 代码）

开发工具：:vscode
使用语言:python

