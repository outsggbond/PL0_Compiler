%{
#include "calc.tab.h"
%}

%option noyywrap

%%
[0-9]+      { yylval = atoi(yytext); return NUMBER; }
"+"         return PLUS;
"*"         return TIMES;
[ \t\n]     ;
.           ;
%%