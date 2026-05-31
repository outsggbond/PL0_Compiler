%{
#include <stdio.h>
#include <ctype.h>

int count[26] = {0};
int total = 0;

%}

%option noyywrap

%%
[a-zA-Z]    {
                char c = toupper(yytext[0]);
                count[c - 'A']++;
                total++;
            }
.           ;   /* 其他字符忽略 */
\n          ;
%%

int main(int argc, char **argv) {
    yylex();

    if (total == 0) return 0;

    for (int i = 0; i < 26; i++) {
        if (count[i] > 0) {
            printf("%c:%d%%", 'A' + i, (count[i] * 100) / total);
            if (i < 25) printf(", ");
        }
    }
    printf("\n");
    return 0;
}