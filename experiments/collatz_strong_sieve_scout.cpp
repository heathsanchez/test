// Exact strong-induction convergence-sieve scout.
//
// For every residue b mod 2^k, the first k shortcut-Collatz parities depend
// only on b. If c is the number of odd steps and d=T^k(b), then for every a:
//     T^k(a*2^k+b) = a*3^c + d.                         (1)
//
// A residue family is dead if any of these exact conditions holds:
//  A) inherited: a lower-bit prefix already has a certificate;
//  B) coalescence: some b'<b has the same (c,d), so the two whole affine
//     families meet after k steps. Strong induction on n closes the larger;
//  C) immediate descent: for all a>=1,
//        a*3^c+d < a*2^k+b.
//     Writing l=3^c-2^k and r=b-d, it suffices exactly that l<0 and l<r.
//
// This is an independent compact implementation of the convergence-sieve idea.
// It emits only census/fingerprint data; no external sieve file is trusted.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <unordered_set>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;

static inline u128 T(u128 n){return (n&1)?(3*n+1)/2:n/2;}

static uint64_t pow3u(int c){
  uint64_t x=1;
  for(int i=0;i<c;++i){
    if(x>UINT64_MAX/3){std::cerr<<"POW3_U64_OVERFLOW\n";std::exit(3);}
    x*=3;
  }
  return x;
}

struct CD{int c;uint64_t d;};

static CD Tk(uint64_t b,int k){
  u128 n=b;int c=0;
  for(int i=0;i<k;++i){
    if(n&1)++c;
    n=T(n);
  }
  if(n>UINT64_MAX){std::cerr<<"D_U64_OVERFLOW\n";std::exit(4);}
  return {c,(uint64_t)n};
}

static uint64_t pack_key(int c,uint64_t d){
  // Scout is intentionally capped so d fits in 56 bits.
  if(d>=(UINT64_C(1)<<56)){std::cerr<<"KEY_RANGE_OVERFLOW\n";std::exit(5);}
  return (uint64_t(c)<<56)|d;
}

int main(int argc,char**argv){
  if(argc!=2){std::cerr<<"usage: scout K\n";return 2;}
  const int K=std::stoi(argv[1]);
  if(K<1||K>24){std::cerr<<"K_OUT_OF_SCOUT_RANGE\n";return 2;}

  std::vector<uint8_t> prev(1,1),cur;
  for(int k=1;k<=K;++k){
    const uint64_t B=UINT64_C(1)<<k;
    const uint64_t mask_prev=(UINT64_C(1)<<(k-1))-1;
    cur.assign(B,0);
    std::unordered_set<uint64_t> seen;
    seen.reserve((size_t)(B*1.2));

    uint64_t inherited=0,coalesce=0,descent=0,live=0;
    uint64_t odd_live=0;
    for(uint64_t b=0;b<B;++b){
      CD cd=Tk(b,k);
      const uint64_t key=pack_key(cd.c,cd.d);
      const bool duplicate=seen.find(key)!=seen.end();
      seen.insert(key);

      if(k>1 && !prev[b&mask_prev]){
        ++inherited;
        continue;
      }
      if(duplicate){
        ++coalesce;
        continue;
      }

      const i128 l=i128(pow3u(cd.c))-i128(UINT64_C(1)<<k);
      const i128 r=i128(b)-i128(cd.d);
      if(l<0 && l<r){
        ++descent;
        continue;
      }

      cur[b]=1;++live;
      if(b&1)++odd_live;
    }

    std::cout<<"STRONG_SIEVE_LEVEL"
             <<" k="<<k
             <<" total="<<B
             <<" inherited="<<inherited
             <<" coalesce="<<coalesce
             <<" descent="<<descent
             <<" live="<<live
             <<" odd_live="<<odd_live
             <<" live_fraction="<<(double(live)/double(B))
             <<" odd_live_fraction="<<(double(odd_live)/double(B/2))
             <<"\n";
    prev.swap(cur);
  }
  std::cout<<"STRONG_SIEVE_DONE k="<<K<<"\n";
  return 0;
}
