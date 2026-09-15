// Recursive strong-induction sieve with compiled reverse-predecessor bridges.
//
// Baseline closure is exactly collatz_strong_sieve_scout.cpp:
//   A) inherited lower binary prefix,
//   B) affine coalescence with a smaller residue,
//   C) universal descent after k shortcut steps.
//
// New constructor D composes an unresolved forward affine family
//
//   n(a)=a*2^k+b,     T^k(n(a))=a*3^c+d
//
// with a retained reverse certificate
//
//   m == r (mod 3^o),
//   p=(2^s*m-C)/3^o,  T^s(p)=m.
//
// When c>=o, applicability is independent of a.  Substitution gives
//
//   p(a)=a*2^s*3^(c-o) + (2^s*d-C)/3^o.
//
// If p(a)<n(a) for every a>=1, the whole binary residue class is closed by
// strong induction.  Crucially, this closure is written into the live mask,
// so all descendants inherit it at later binary depths.
//
// The reverse bank is generated independently by
// collatz_reverse_predecessor_sparse.py and supplied as text rows:
//
//   o steps C residue
//
// This program verifies every accepted bridge concretely at a=1 and a=3 in
// addition to the exact affine inequality used for the universal claim.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <unordered_map>
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

static u128 iterate(u128 n,int steps){
  for(int i=0;i<steps;++i)n=T(n);
  return n;
}

static uint64_t pack_key(int c,uint64_t d){
  if(d>=(UINT64_C(1)<<56)){std::cerr<<"KEY_RANGE_OVERFLOW\n";std::exit(5);}
  return (uint64_t(c)<<56)|d;
}

struct RevCert{
  int o;
  int steps;
  uint64_t C;
  uint64_t residue;
};

static std::vector<std::unordered_map<uint64_t,RevCert>>
load_bank(const std::string& path,int& max_o){
  std::ifstream in(path);
  if(!in){std::cerr<<"BANK_OPEN_FAILED\n";std::exit(6);}
  std::vector<RevCert> all;
  max_o=0;
  std::string line;
  while(std::getline(in,line)){
    if(line.empty())continue;
    std::istringstream ss(line);
    RevCert z{};
    if(!(ss>>z.o>>z.steps>>z.C>>z.residue)){
      std::cerr<<"BANK_PARSE_FAILED "<<line<<"\n";std::exit(7);
    }
    max_o=std::max(max_o,z.o);
    all.push_back(z);
  }
  std::vector<std::unordered_map<uint64_t,RevCert>> bank(max_o+1);
  for(const auto& z:all){
    auto [it,ok]=bank[z.o].emplace(z.residue,z);
    if(!ok){std::cerr<<"BANK_DUPLICATE_RESIDUE\n";std::exit(8);}
  }
  std::cout<<"RECURSIVE_BANK certificates="<<all.size()
           <<" max_o="<<max_o<<"\n";
  return bank;
}

static bool bridge_closes(
    uint64_t b,const CD& cd,int k,
    const std::vector<std::unordered_map<uint64_t,RevCert>>& bank,
    int max_o,RevCert& used,
    i128& out_coef,i128& out_const){
  const int top=std::min(cd.c,max_o);
  uint64_t mod=1;
  for(int o=1;o<=top;++o){
    mod*=3;
    auto it=bank[o].find(cd.d%mod);
    if(it==bank[o].end())continue;
    const RevCert& z=it->second;

    const i128 den=i128(mod);
    const i128 num_const=(i128(1)<<z.steps)*i128(cd.d)-i128(z.C);
    if(num_const%den!=0){
      std::cerr<<"BRIDGE_DIVISIBILITY_FAILED\n";std::exit(9);
    }
    const i128 pconst=num_const/den;
    const i128 pcoef=(i128(1)<<z.steps)*i128(pow3u(cd.c-z.o));
    const i128 L=pcoef-(i128(1)<<k);
    const i128 R=i128(b)-pconst;
    if(L<0 && L<R && pcoef+pconst>0){
      used=z;out_coef=pcoef;out_const=pconst;return true;
    }
    // Retained reverse cylinders are prefix-free, so a matched coarser
    // certificate excludes a retained finer one on the same integer.
    return false;
  }
  return false;
}

int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: recursive K BANK\n";return 2;}
  const int K=std::stoi(argv[1]);
  const std::string bankpath=argv[2];
  if(K<1||K>24){std::cerr<<"K_OUT_OF_RANGE\n";return 2;}

  int max_o=0;
  const auto bank=load_bank(bankpath,max_o);

  std::vector<uint8_t> prev(1,1),cur;
  uint64_t total_bridge=0,total_bridge_controls=0;

  for(int k=1;k<=K;++k){
    const uint64_t B=UINT64_C(1)<<k;
    const uint64_t mask_prev=(UINT64_C(1)<<(k-1))-1;
    cur.assign(B,0);
    std::unordered_set<uint64_t> seen;
    seen.reserve((size_t)(B*1.2));

    uint64_t inherited=0,coalesce=0,descent=0,bridge=0,live=0;

    for(uint64_t b=0;b<B;++b){
      CD cd=Tk(b,k);
      const uint64_t key=pack_key(cd.c,cd.d);
      const bool duplicate=seen.find(key)!=seen.end();
      seen.insert(key);

      if(k>1 && !prev[b&mask_prev]){
        ++inherited;continue;
      }
      if(duplicate){
        ++coalesce;continue;
      }

      const i128 l=i128(pow3u(cd.c))-i128(B);
      const i128 r=i128(b)-i128(cd.d);
      if(l<0 && l<r){
        ++descent;continue;
      }

      RevCert cert{};
      i128 pcoef=0,pconst=0;
      if(bridge_closes(b,cd,k,bank,max_o,cert,pcoef,pconst)){
        ++bridge;++total_bridge;

        // Independent concrete replay for every accepted bridge at two affine
        // parameters.  This is a control; universal validity comes from the
        // exact affine derivation and inequalities above.
        for(uint64_t a:{1ULL,3ULL}){
          const u128 n=u128(a)*B+b;
          const u128 m=u128(a)*pow3u(cd.c)+cd.d;
          const i128 ps=i128(a)*pcoef+pconst;
          if(ps<=0 || u128(ps)>=n){
            std::cerr<<"BRIDGE_LOWER_CONTROL_FAILED k="<<k<<" b="<<b<<"\n";
            return 10;
          }
          const u128 p=u128(ps);
          if(iterate(n,k)!=m || iterate(p,cert.steps)!=m){
            std::cerr<<"BRIDGE_REPLAY_FAILED k="<<k<<" b="<<b<<"\n";
            return 11;
          }
          ++total_bridge_controls;
        }
        continue;
      }

      cur[b]=1;++live;
    }

    std::cout<<"RECURSIVE_CONSTRUCTOR_LEVEL"
             <<" k="<<k
             <<" inherited="<<inherited
             <<" coalesce="<<coalesce
             <<" descent="<<descent
             <<" bridge="<<bridge
             <<" live="<<live
             <<" odd_live_fraction="<<(double(live)/double(B/2))
             <<"\n";
    prev.swap(cur);
  }

  uint64_t final_live=0;
  for(uint8_t x:prev)final_live+=x;
  std::cout<<"RECURSIVE_CONSTRUCTOR_DONE K="<<K
           <<" final_live="<<final_live
           <<" total_bridge="<<total_bridge
           <<" bridge_controls="<<total_bridge_controls<<"\n";
  std::cout<<"VERIFIED_RECURSIVE_COMPILED_CONSTRUCTOR_SIEVE\n";
  return 0;
}
