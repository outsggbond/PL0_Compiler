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
├── docs/ # 课程设计报告及参考资料
│ ├── Experiment_3.md
│ └── shortcut/ # 报告图表、截图等素材
│ ├── exps1_1.png
│ ├── exps1_2.png
│ └── exps1_3.png
│
├── flex_bison_exps/ # 第3章 Flex/Bison 三个实验
│ ├── task1_1_freq/
│ │ ├── freq.l
│ │ ├── lex.yy.c
│ │ ├── freq.exe # 编译生成
│ │ └── test1_1_input.txt
│ ├── task1_2_token/
│ │ ├── token.l
│ │ ├── lex.yy.c
│ │ ├── token.exe
│ │ └── test_1_2_input.txt
│ └── task1_3_calc/
│ ├── calc.l
│ ├── calc.y
│ ├── calc.tab.c
│ ├── calc.tab.h
│ ├── lex.yy.c
│ ├── calc.exe
│ └── test_1_3_input.txt
│
├── src/ # 核心编译器源代码
│ ├── lexer/ # 词法分析器
│ │ ├── lexer.py
│ │ └── token.py
│ ├── parser_ll/ # 自顶向下 LL(1) 语法分析器
│ │ ├── first_follow.py
│ │ ├── ll_parser.py
│ │ └── ll_table.py
│ ├── parser_lr/ # 自底向上 LR 语法分析器
│ │ ├── lr_items.py
│ │ ├── lr_parser.py
│ │ └── lr_table.py
│ ├── semantic_ll/ # L-翻译模式（对应 LL）
│ │ └── semantic_ll.py
│ ├── semantic_lr/ # S-翻译模式（对应 LR）
│ │ └── semantic_lr.py
│ └── utils/ # 工具模块
│ ├── quad_generator.py
│ └── symbol_table.py
│
├── input/ # 测试用例输入
│ ├── correct/ # 正确语法用例（来自文档）
│ │ ├── test1.txt
│ │ └── test2.txt
│ └── error/ # 错误用例
│ ├── lexical_error.txt
│ ├── syntax_error.txt
│ └── semantic_error.txt
│
├── output/ # 编译或运行输出
│ ├── tokens_out.txt
│ ├── quads_ll.txt
│ └── quads_lr.txt
│
├── README.md # 项目说明、编译运行方法
└── requirements.txt # Python 依赖
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

## PL0语法

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

## 翻译模式

```
// ==================== L属性翻译模式（适用于自顶向下LL(1)递归下降） ====================

// 辅助函数：
//   Getnext(token) : 读入下一个输入符号，存入全局变量 token
//   newtemp()      : 返回一个新的临时变量名
//   newlabel()     : 返回一个新的标号名（用于L模式）
//   label(L)       : 在当前指令位置放置标号 L
//   gen(code)      : 生成一条三地址指令

// 非终结符 T：
Tval T(token) {
    D: Fval, T'_inh, T'_syn;
    Fval = F(token);
    T'_inh = Fval;
    Getnext(token);
    T'_syn = T'(token, T'_inh);
    Tval = T'_syn;
    return Tval;
}

// 非终结符 T' ：返回 T'.syn
T'_syn T'(token, T'_inh) {
    D: Fval, T1'_inh, T1'_syn;
    if (token == "*") {
        Getnext(token);
        Fval = F(token);
        T1'_inh = T'_inh * Fval;
        Getnext(token);
        T1'_syn = T'(token, T1'_inh);
        T'_syn = T1'_syn;
        return T'_syn;
    }
    else if (token == "#" || token == ")" || token == "+" || token == "-") {  // FOLLOW集
        T'_syn = T'_inh;
        return T'_syn;
    }
    else error();
}

// 非终结符 F：
Fval F(token) {
    if (token == digit) return token.lexval;
    else if (token == '(') {
        Getnext(token);
        Fval = E(token);       // E 未在此定义，假设存在
        if (token != ')') error();
        Getnext(token);
        return Fval;
    }
    else error();
}

// 控制流示例（L模式，使用标号）：
// S -> if B then S1 else S2
S_code S_if(token) {
    D: B_true, B_false;
    B_true = newlabel();
    B_false = newlabel();
    // 解析 'if'，然后解析 B，传递继承属性 true/false
    B_code = B(token, B_true, B_false);
    // 关键字 then
    label(B_true);
    S1_code = S(token, S.next);  // S.next 是继承属性
    gen("goto " S.next);
    label(B_false);
    S2_code = S(token, S.next);
    return B_code + S1_code + S2_code;
}

// S -> while B do S1
S_code S_while(token, S_next) {
    D: B_begin, B_true, B_false;
    B_begin = newlabel();
    label(B_begin);
    B_true = newlabel();
    B_false = S_next;
    B_code = B(token, B_true, B_false);
    // 关键字 do
    label(B_true);
    S1_code = S(token, B_begin);
    gen("goto " B_begin);
    return B_code + S1_code;
}

// B -> E1 relop E2  （L模式，带继承属性 true/false）
B_code B_relop(token, B_true, B_false) {
    D: E1_addr, E2_addr;
    E1_addr = E(token);   // 解析 E1，返回存放结果的临时变量
    relop = token; Getnext(token);
    E2_addr = E(token);
    gen("if " E1_addr relop E2_addr " goto " B_true);
    gen("goto " B_false);
    return "";  // 或者返回代码列表
}

// B -> B1 ∨ B2
B_code B_or(token, B_true, B_false) {
    D: B1_true, B1_false, B2_true, B2_false, label1;
    B1_true = B_true;
    label1 = newlabel();
    B1_false = label1;
    B1_code = B(token, B1_true, B1_false);
    label(label1);
    B2_true = B_true;
    B2_false = B_false;
    B2_code = B(token, B2_true, B2_false);
    return B1_code + B2_code;
}


// ==================== S属性翻译模式（LR分析，使用回填技术） ====================

// 全局变量：
//   nextstm : 整数，下一条指令的索引
//   stack[] : 属性栈（每个条目包含 .val, .truelist, .falselist, .nextlist, .addr 等）

// 辅助函数：
//   makelist(i)   -> 返回只包含索引 i 的新列表
//   merge(l1,l2)  -> 合并两个列表，返回合并后的列表指针
//   backpatch(l, i) -> 将列表 l 中所有指令的目标标号填充为 i
//   gen(code)     -> 生成一条指令，nextstm 自增

// 算术表达式（S模式，栈操作）：
// 产生式 E' → E   { print(stack[top].val); }
// 产生式 E → E1 + T
semantic_action_E_plus() {
    stack[top-2].val = stack[top-2].val + stack[top].val;
    top = top - 2;
}
// 产生式 T → T1 * F
semantic_action_T_mult() {
    stack[top-2].val = stack[top-2].val * stack[top].val;
    top = top - 2;
}
// 产生式 F → ( E )
semantic_action_F_paren() {
    stack[top-2].val = stack[top-1].val;
    top = top - 2;
}
// 产生式 F → id
semantic_action_F_id() {
    stack[top].val = id.lexval;
}

// 布尔表达式（S模式，回填）：
// B → E1 relop E2
semantic_action_B_relop() {
    B.truelist = makelist(nextstm);
    B.falselist = makelist(nextstm+1);
    gen("if " E1.addr relop E2.addr " goto _");
    gen("goto _");
}
// B → true
semantic_action_B_true() {
    B.truelist = makelist(nextstm);
    gen("goto _");
}
// B → false
semantic_action_B_false() {
    B.falselist = makelist(nextstm);
    gen("goto _");
}
// B → ( B1 )
semantic_action_B_paren() {
    B.truelist = B1.truelist;
    B.falselist = B1.falselist;
}
// B → ┑ B1
semantic_action_B_not() {
    B.truelist = B1.falselist;
    B.falselist = B1.truelist;
}
// B → B1 ∨ M B2   其中 M → ε { M.gotostm = nextstm; }
semantic_action_B_or() {
    backpatch(B1.falselist, M.gotostm);
    B.truelist = merge(B1.truelist, B2.truelist);
    B.falselist = B2.falselist;
}
// M → ε
semantic_action_M() {
    M.gotostm = nextstm;
}
// B → B1 ∧ M B2
semantic_action_B_and() {
    backpatch(B1.truelist, M.gotostm);
    B.truelist = B2.truelist;
    B.falselist = merge(B1.falselist, B2.falselist);
}

// 控制语句（S模式，回填）：
// S → if E then M1 S1 N else M2 S2
semantic_action_if() {
    backpatch(E.truelist, M1.gotostm);
    backpatch(E.falselist, M2.gotostm);
    S.nextlist = merge(merge(S1.nextlist, N.nextlist), S2.nextlist);
}
// N → ε
semantic_action_N() {
    N.nextlist = makelist(nextstm);
    gen("goto _");
}
// M → ε
semantic_action_M_ctrl() {
    M.gotostm = nextstm;
}
// S → while M1 E do M2 S1
semantic_action_while() {
    backpatch(S1.nextlist, M1.gotostm);
    backpatch(E.truelist, M2.gotostm);
    S.nextlist = E.falselist;
    gen("goto " M1.gotostm);
}
// S → S1 M S2
semantic_action_seq() {
    backpatch(S1.nextlist, M.gotostm);
    S.nextlist = S2.nextlist;
}

```

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
