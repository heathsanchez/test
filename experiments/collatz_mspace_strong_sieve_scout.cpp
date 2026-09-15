// Exact strong-induction sieve in the residual m-coordinate.
//
// Fixed valuation slice:
//     n = 2^K m - 1,   m odd.
// Refine m = A*2^s + b. Then
//     n = A*2^(K+s) + (2^K b - 1).
//
// Let W=K+s, B=2^K b-1, c=# odd steps in first W steps, d=T^W(B).
// Exact family identity:
//     T^W(n) = A*3^c + d.
//
// Therefore a b-family is inductively dead if:
//   * a lower-s m-prefix is already dead;
//   * a smaller b' has the same (c,d), so the two m-families coalesce;
//   * A*3^c+d < A*2^W+B for every A>=1.
//
// This is the general convergence sieve applied AFTER the valuation quotient,
// so no sieve depth is wasted re-encoding the K forced trailing ones.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <unordered_set>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;

static inline u128 T(u128 n){return(n&1)?(3*n+1)/2:n/2;}

static u128 pow3(int c){
  u128 x=1;
  for(int i=0;i<c;++i)x*=3;
  return x;
}

struct Key{
  uint64_t d;
  uint8_t c;
  bool operator==(const Key&o)const{return d==o.d&&c==o.c;}
};
struct Hash{
  size_t operator()(const Key&x)const{
    uint64_t z=x.d^(uint64_t(x.c)*UINT64_C(0x9e3779b97f4a7c15));
    z^=z>>33;z*=UINT64_C(0xff51afd7ed558ccd);
    z^=z>>33;z*=UINT64_C(0xc4ceb9fe1a85ec53);
    z^=z>>33;return(size_t)z;
  }
};

struct CD{int c;uint64_t d;};
static CD Tk(u128 b,int w){
  u128 n=b;int c=0;
  for(int i=0;i<w;++i){if(n&1)++c;n=T(n);}
  if(n>u128(UINT64_MAX)){std::cerr<<"D_RANGE\n";std::exit(4);}
  return{c,(uint64_t)n};
}

int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: scout K S\n";return 2;}
  int K=std::stoi(argv[1]),S=std::stoi(argv[2]);
  if(K<1||K>31||S<1||S>24||K+S>=64){std::cerr<<"RANGE\n";return 2;}

  // Indexed by full low-s residue b. Only odd b can occur.
  std::vector<uint8_t>prev(2,0),cur;
  prev[1]=1;

  for(int s=1;s<=S;++s){
    uint64_t N=UINT64_C(1)<<s;
    cur.assign(N,0);
    std::unordered_set<Key,Hash>seen;
    seen.reserve((size_t)(N*0.7));

    uint64_t inherited=0,coalesce=0,descent=0,live=0;
    for(uint64_t b=1;b<N;b+=2){
      int W=K+s;
      u128 B=(u128(b)<<K)-1;
      CD cd=Tk(B,W);
      Key key{cd.d,(uint8_t)cd.c};
      bool dup=seen.find(key)!=seen.end();
      seen.insert(key);

      if(s>1){
        uint64_t low=b&((UINT64_C(1)<<(s-1))-1);
        if(!prev[low]){++inherited;continue;}
      }
      if(dup){++coalesce;continue;}

      i128 l=i128(pow3(cd.c))-i128(u128(1)<<W);
      i128 r=i128(B)-i128(cd.d);
      if(l<0&&l<r){++descent;continue;}

      cur[b]=1;++live;
    }

    uint64_t odd_total=UINT64_C(1)<<(s-1);
    std::cout<<"MSPACE_SIEVE_LEVEL"
             <<" K="<<K<<" s="<<s<<" W="<<(K+s)
             <<" odd_total="<<odd_total
             <<" inherited="<<inherited
             <<" coalesce="<<coalesce
             <<" descent="<<descent
             <<" live="<<live
             <<" live_fraction="<<(double(live)/double(odd_total))
             <<"\n";
    prev.swap(cur);
  }
  std::cout<<"MSPACE_SIEVE_DONE K="<<K<<" S="<<S<<"\n";
  return 0;
}
