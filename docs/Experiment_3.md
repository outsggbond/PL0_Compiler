编译过程:
```PS K:\PL0_Compiler> cd .\PL0_Compiler\
PS K:\PL0_Compiler\PL0_Compiler> cd .\flex_bison_exps\
PS K:\PL0_Compiler\PL0_Compiler\flex_bison_exps> cd .\task1_1_freq\
PS K:\PL0_Compiler\PL0_Compiler\flex_bison_exps\task1_1_freq> win_flex .\freq.l
PS K:\PL0_Compiler\PL0_Compiler\flex_bison_exps\task1_1_freq> gcc lex.yy.c -o freq.exe
PS K:\PL0_Compiler\PL0_Compiler\flex_bison_exps\task1_1_freq> cd..
PS K:\PL0_Compiler\PL0_Compiler\flex_bison_exps> cd .\task1_2_token\
PS K:\PL0_Compiler\PL0_Compiler\flex_bison_exps\task1_2_token> win_flex token.l
>> gcc lex.yy.c -o token.exe
PS K:\PL0_Compiler\PL0_Compiler\flex_bison_exps\task1_2_token> cd..
PS K:\PL0_Compiler\PL0_Compiler\flex_bison_exps> cd .\task1_3_calc\
PS K:\PL0_Compiler\PL0_Compiler\flex_bison_exps\task1_3_calc> win_bison -d calc.y
>> win_flex calc.l
>> gcc calc.tab.c lex.yy.c -o calc.exe
calc.tab.c: In function 'yyparse':                                                                                 
calc.tab.c:580:16: warning: implicit declaration of function 'yylex' [-Wimplicit-function-declaration]             
  580 | # define YYLEX yylex ()                                                                                    
      |                ^~~~~                                                                                       
calc.tab.c:1240:16: note: in expansion of macro 'YYLEX'                                                            
 1240 |       yychar = YYLEX;                                                                                      
      |                ^~~~~                                                                                       
PS K:\PL0_Compiler\PL0_Compiler\flex_bison_exps\task1_3_calc> ```
最后面就是这个代码的有报错
原因是：yylex() 是 Flex 生成的词法分析器中的函数，在 lex.yy.c 里定义。

Bison 生成的语法分析器需要调用 yylex() 来获取下一个单词（token）。

但是 calc.tab.c 在编译时（单独编译时）并不知道 yylex 的声明，因为没有包含合适的头文件。

##注意这个输入结束后要 按control+Z进行结束，然后再回车拆可以出结果

然后就是输入输出测试：
1、对编译生成的freq.exe进行测试

2、对编译生成的token.exe进行测试

3、对这个calc.exe进行测试
