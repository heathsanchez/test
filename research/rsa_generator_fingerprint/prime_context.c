/* Near-prime arithmetic control. Uses GMP probable-prime checks at 25 rounds.
   Source data are verified publicly factored challenge primes; this program
   NEVER factors challenge integers or claims prime-proving certificates. */
#include <gmp.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

static void previous(mpz_t out, const mpz_t x) {
  mpz_sub_ui(out,x,2);
  while (!mpz_probab_prime_p(out,25)) mpz_sub_ui(out,out,2);
}
static void following(mpz_t out, const mpz_t x) {
  mpz_add_ui(out,x,2);
  while (!mpz_probab_prime_p(out,25)) mpz_add_ui(out,out,2);
}
static unsigned long gap_any(const mpz_t x) {
  mpz_t a,d; mpz_inits(a,d,NULL); previous(a,x);
  mpz_sub(d,x,a); unsigned long g=mpz_get_ui(d);
  mpz_clears(a,d,NULL); return g;
}
static unsigned long gap_mod3(const mpz_t x) {
  mpz_t a,d,y; mpz_inits(a,d,y,NULL); mpz_set(y,x);
  do { previous(a,y); mpz_set(y,a); } while (mpz_fdiv_ui(a,3)!=2);
  mpz_sub(d,x,a); unsigned long g=mpz_get_ui(d);
  mpz_clears(a,d,y,NULL); return g;
}
int main(int argc, char **argv) {
  int radius=argc>1?atoi(argv[1]):12;
  if (radius<1 || radius>32) return 2;
  mpz_t x,a,y; mpz_inits(x,a,y,NULL);
  char input[900];
  while (scanf("%899s",input)==1) {
    if (mpz_set_str(x,input,10)!=0 || mpz_fdiv_ui(x,3)!=2 ||
        !mpz_probab_prime_p(x,25)) return 3;
    mp_exp_t exponent;
    double mantissa=mpz_get_d_2exp(&exponent,x);
    double logx=(double)exponent*log(2.0)+log(mantissa);
    printf("%lu,%lu,%.13f",gap_any(x),gap_mod3(x),logx);
    for (int direction=0;direction<2;direction++) {
      mpz_set(y,x);
      for (int k=0;k<radius;k++) {
        do {
          if (direction==0) previous(a,y); else following(a,y);
          mpz_set(y,a);
        } while (mpz_fdiv_ui(y,3)!=2);
        printf(",%lu:%lu",gap_any(y),gap_mod3(y));
      }
    }
    putchar('\n');
  }
  mpz_clears(x,a,y,NULL);
  return 0;
}
