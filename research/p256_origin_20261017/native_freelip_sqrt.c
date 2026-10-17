/* Calls original 1997 FreeLIP zsqrtmod from immutable mirrored source.
   This harness adds no square-root policy. The FreeLIP source is fetched
   and compiled separately in CI under its own published license. */
#include "lip.h"
#include <stdio.h>
int main(int argc, char **argv) {
  verylong a = 0, p = 0, root = 0;
  if(argc != 3) { fprintf(stderr, "usage: native a_decimal p_decimal\n"); return 2; }
  zstrtoz(argv[1], &a);
  zstrtoz(argv[2], &p);
  zsqrtmod(a,p,&root);
  zwriteln(root);
  return 0;
}
