%{
#include <stdio.h>
void yyerror(const char *s) { fprintf(stderr, "%s\n", s); }
%}

%token NUMBER
%token PLUS TIMES
%left PLUS
%left TIMES

%%
expr    : expr PLUS term   { $$ = $1 + $3; printf("%d\n", $$); }
        | term             { $$ = $1; }
        ;

term    : term TIMES factor { $$ = $1 * $3; }
        | factor            { $$ = $1; }
        ;

factor  : NUMBER            { $$ = $1; }
        ;

%%

int main() {
    yyparse();
    return 0;
}