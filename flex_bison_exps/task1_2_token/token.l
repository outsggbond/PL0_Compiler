%{
#include <stdio.h>
%}

%option noyywrap

%%
[a-zA-Z]+       printf("%s 单词\n", yytext);
[0-9]+          printf("%s 数字\n", yytext);
[+\-*/=;,<>(){}\"]  printf("%s 符号\n", yytext);
[ \t]           ;   /* 忽略空格/Tab */
\n              ;
.               ;   /* 其他忽略 */
%%

int main() {
    yylex();
    return 0;
}