// Export the exact live frontier of the canonical strong-induction sieve.
//
// This is the same closure logic as collatz_strong_sieve_scout.cpp:
//   A) inherited closure from a lower binary prefix,
//   B) exact affine coalescence with a smaller residue,
//   C) exact universal descent after k shortcut steps.
//
// For the requested final depth K it writes every unresolved odd residue
//
//   b mod 2^K,  c=#odd steps in first K steps,  d=T^K(b)
//
// as "b c d".  These affine states are inputs to constructor-composition
// experiments; exporting them does not add a new mathematical assumption.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <string>
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
  if(d>=(UINT64_C(1)<<56)){std::cerr<<"KEY_RANGE_OVERFLOW\n";std::exit(5);}
  return (uint64_t(c)<<56)|d;
}

int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: export K OUT\n";return 2;}
  const int K=std::stoi(argv[1]);
  const std::string outpath=argv[2];
  if(K<1||K>24){std::cerr<<"K_OUT_OF_EXPORT_RANGE\n";return 2;}

  std::vector<uint8_t> prev(1,1),cur;
  std::vector<uint64_t> final_live;

  for(int k=1;k<=K;++k){
    const uint64_t B=UINT64_C(1)<<k;
    const uint64_t mask_prev=(UINT64_C(1)<<(k-1))-1;
    cur.assign(B,0);
    std::unordered_set<uint64_t> seen;
    seen.reserve((size_t)(B*1.2));

    uint64_t inherited=0,coalesce=0,descent=0,live=0;
    if(k==K) final_live.reserve(B/32);

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

      const i128 l=i128(pow3u(cd.c))-i128(B);
      const i128 r=i128(b)-i128(cd.d);
      if(l<0 && l<r){
        ++descent;
        continue;
      }

      cur[b]=1;++live;
      if(k==K){
        if(!(b&1)){std::cerr<<"EVEN_FINAL_LIVE\n";return 6;}
        final_live.push_back(b);
      }
    }

    std::cout<<"STRONG_EXPORT_LEVEL"
             <<" k="<<k
             <<" inherited="<<inherited
             <<" coalesce="<<coalesce
             <<" descent="<<descent
             <<" live="<<live<<"\n";
    prev.swap(cur);
  }

  std::ofstream out(outpath);
  if(!out){std::cerr<<"OUT_OPEN_FAILED\n";return 7;}
  uint64_t controls=0;
  for(uint64_t b:final_live){
    CD cd=Tk(b,K);
    out<<b<<" "<<cd.c<<" "<<cd.d<<"\n";

    // Independent affine identity controls on a deterministic prefix and tail.
    if(controls<4096 || controls+4096>=final_live.size()){
      const u128 M=u128(1)<<K;
      for(uint64_t a:{1ULL,3ULL}){
        u128 n=u128(a)*M+b;
        u128 x=n;
        for(int t=0;t<K;++t)x=T(x);
        u128 rhs=u128(a)*pow3u(cd.c)+cd.d;
        if(x!=rhs){
          std::cerr<<"AFFINE_EXPORT_MISMATCH b="<<b<<" a="<<a<<"\n";
          return 8;
        }
      }
    }
    ++controls;
  }
  out.close();

  std::cout<<"STRONG_EXPORT_DONE K="<<K
           <<" live="<<final_live.size()
           <<" output="<<outpath<<"\n";
  std::cout<<"VERIFIED_STRONG_SIEVE_LIVE_AFFINE_EXPORT\n";
  return 0;
}
