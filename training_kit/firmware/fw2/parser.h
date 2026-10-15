#ifndef PARSER_H
#define PARSER_H
#include <stddef.h>
#include <stdint.h>
typedef struct { uint8_t bytes[6]; size_t used; } Parser;
typedef void (*Emit)(unsigned sequence, int value);
void parser_feed(Parser *p, const uint8_t *data, size_t size, Emit emit);
#endif
