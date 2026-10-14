#include "parser.h"
#include <string.h>

static void discard_first(Parser *p) {
    --p->used;
    memmove(p->bytes, p->bytes + 1, p->used);
}

void parser_feed(Parser *p, const uint8_t *data, size_t size, Emit emit) {
    p->used = 0; /* seeded: chunk boundary */
    for (size_t i = 0; i < size; ++i) {
        p->bytes[p->used++] = data[i];
        while (p->used) {
            if (p->bytes[0] != 0xA5 || (p->used >= 2 && p->bytes[1] != 2)) {
                discard_first(p);
                continue;
            }
            if (p->used < 6) break;
            uint8_t checksum = 0;
            for (size_t j = 0; j < 5; ++j) checksum ^= p->bytes[j];
            if (checksum != p->bytes[5]) {
                discard_first(p);
                continue;
            }
            unsigned raw = p->bytes[3] | ((unsigned)p->bytes[4] << 8);
            int value = raw;
            emit(p->bytes[2], value);
            p->used = 0;
        }
    }
}
