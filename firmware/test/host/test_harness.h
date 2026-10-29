/*
 * Minimal assertion harness for host unit tests (no external dependency).
 */
#pragma once

#include <stdio.h>
#include <stdlib.h>

extern int g_failures;
extern int g_checks;

#define CHECK(cond)                                                                      \
    do {                                                                                 \
        g_checks++;                                                                      \
        if (!(cond)) {                                                                   \
            g_failures++;                                                                \
            fprintf(stderr, "  FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);            \
        }                                                                                \
    } while (0)

#define CHECK_EQ_INT(a, b)                                                               \
    do {                                                                                 \
        long long _va = (long long)(a), _vb = (long long)(b);                            \
        g_checks++;                                                                      \
        if (_va != _vb) {                                                                \
            g_failures++;                                                                \
            fprintf(stderr, "  FAIL %s:%d: %s == %s (%lld != %lld)\n", __FILE__,         \
                    __LINE__, #a, #b, _va, _vb);                                         \
        }                                                                                \
    } while (0)

typedef void (*test_fn_t)(void);

void run_test(const char *name, test_fn_t fn);
