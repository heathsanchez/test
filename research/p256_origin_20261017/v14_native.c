/* V14 — unmodified pinned FreeLIP v1.1 native API witness.
   Compile this small driver against 1997 lip.c/lip.h with -m32 -DSINGLE_MUL.
   This is test harness source, not a modification to the legacy library. */
#include "lip.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if NBITS != 26
#error "V14's original FreeLIP build must have NBITS=26"
#endif

int main(int argc, char **argv) {
    verylong seed = 0, prime = 0, point = 0;
    long n;
    int i;
    if (argc != 3) {
        fprintf(stderr, "usage: native SEED point|words\n");
        return 2;
    }
    n = atol(argv[1]);
    if (n <= 0) {
        fprintf(stderr, "V14 tests are explicitly restricted to positive seeds\n");
        return 3;
    }
    if (!zstrtozbas("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF",16,&prime)) {
        fprintf(stderr, "unable to parse pinned P-256 modulus\n");
        return 4;
    }
    zintoz(n, &seed);
    zrstart(seed);
    if (strcmp(argv[2],"point") == 0) {
        zrandomb(prime, &point);
        zwriteln(point);
        return 0;
    }
    if (strcmp(argv[2],"words") == 0) {
        for (i=0;i<20;i++) printf("%ld\n", zrandom(RADIX));
        return 0;
    }
    fprintf(stderr, "unknown mode\n");
    return 5;
}
