#include "parser.h"
#include <stdio.h>
#include <string.h>

static int first = 1;
static void emit(unsigned sequence, int value) {
    printf("%s{\"sequence\":%u,\"value\":%d}", first ? "" : ",", sequence, value);
    first = 0;
}
static int digit(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
int main(int argc, char **argv) {
    for (int a = 1; a < argc; ++a) {
        size_t n = strlen(argv[a]);
        if (n % 2 || n > 8192) { fputs("invalid chunk length\n", stderr); return 2; }
        for (size_t i = 0; i < n; ++i)
            if (digit(argv[a][i]) < 0) { fputs("invalid hex\n", stderr); return 2; }
    }
    Parser parser = {{0}, 0};
    putchar('[');
    for (int a = 1; a < argc; ++a) {
        uint8_t bytes[4096];
        size_t n = strlen(argv[a]) / 2;
        for (size_t i = 0; i < n; ++i)
            bytes[i] = (uint8_t)((digit(argv[a][2*i]) << 4) | digit(argv[a][2*i+1]));
        parser_feed(&parser, bytes, n, emit);
    }
    puts("]");
    return 0;
}
