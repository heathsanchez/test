// Exact consequence-coalesced symbolic Collatz shell verifier.
//
// We prove closure only for ODD n in [2^K,2^(K+1)); even n descend in one
// shortcut step and are trivial under strong induction.
//
// At depth t (1<=t<=K), state (b,c,d) represents shell members
//
//   n = A*2^t + b,      2^(K-t) <= A <= 2^(K+1-t)-1
//
// with the exact affine identity
//
//   T^t(n) = A*3^c + d.
//
// CONSEQUENCE QUOTIENT:
// At fixed t, if two states have the same (c,d), then for every common A
// they have exactly the same future y, while the state with smaller b has
// smaller n=A*2^t+b and is therefore strictly harder to close by either
//
//   y<n
//   or [y == 2 (mod 3) and (2y-1)/3 < n].
//
// Hence all equal-(c,d) states can be replaced EXACTLY by the one with
// minimum b.  This is not heuristic hash-consing; it is a consequence
// dominance theorem.
//
// Before K all quantities fit uint64 for K<=40 because d<3^t and 3^40<2^64.
// Endpoint products use unsigned __int128.  At t=K we materialize each
// remaining concrete shell integer and continue with cpp_int for EXTRA steps.
//
// A green run with live=0 is an exact closure certificate for the odd shell.

#include <boost/multiprecision/cpp_int.hpp>
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;
using Big=boost::multiprecision::cpp_int;

struct State{
  uint64_t b;
  uint64_t d;
  uint32_t c;
};

static inline Big Tbig(Big n){
  if((n&1)!=0){n=3*n+1;n/=2;return n;}
  n/=2;return n;
}

static inline u128 pow2u(int e){
  return u128(1)<<e;
}

static bool uniform_closed(
    const State& s,int t,int K,
    const std::vector<u128>& p3){
  const u128 amin=pow2u(K-t);
  const u128 amax=pow2u(K+1-t)-1;
  const i128 M=i128(pow2u(t));
  const i128 P=i128(p3[s.c]);

  // y-n = A(P-M)+(d-b).  Linear maximum occurs at one endpoint.
  const i128 coef=P-M;
  const i128 constant=i128(s.d)-i128(s.b);
  const i128 a=(coef>=0)?i128(amax):i128(amin);
  if(coef*a+constant < 0)return true;

  // Since c>=1 for all odd-shell states after the first shortcut step,
  // y mod 3 is d mod 3 uniformly over A.
  if(s.d%3==2){
    // p<n iff 2y-1-3n<0.
    const i128 coef2=2*P-3*M;
    const i128 constant2=2*i128(s.d)-1-3*i128(s.b);
    const i128 a2=(coef2>=0)?i128(amax):i128(amin);
    if(coef2*a2+constant2 < 0)return true;
  }
  return false;
}

static State child(
    const State& s,int t,int e,
    const std::vector<u128>& p3){
  if(t>=63){std::cerr<<"RESIDUE_BIT_RANGE\n";std::exit(4);}
  const uint64_t b=s.b+(e?(UINT64_C(1)<<t):0);
  u128 y=u128(s.d)+(e?p3[s.c]:0);
  uint32_t c=s.c;
  u128 d;
  if(y&1){
    ++c;
    d=(3*y+1)/2;
  }else{
    d=y/2;
  }
  if(d>std::numeric_limits<uint64_t>::max()){
    std::cerr<<"PRE_K_D_OVERFLOW t="<<t+1<<"\n";
    std::exit(5);
  }
  return {b,uint64_t(d),c};
}

static uint64_t coalesce(std::vector<State>& v){
  const uint64_t before=v.size();
  std::sort(v.begin(),v.end(),[](const State&a,const State&b){
    if(a.c!=b.c)return a.c<b.c;
    if(a.d!=b.d)return a.d<b.d;
    return a.b<b.b;
  });
  size_t w=0;
  for(size_t i=0;i<v.size();){
    size_t j=i+1;
    // sorted b guarantees v[i] is the dominating minimum-b representative.
    while(j<v.size() && v[j].c==v[i].c && v[j].d==v[i].d)++j;
    v[w++]=v[i];
    i=j;
  }
  v.resize(w);
  return before-w;
}

struct Concrete{
  Big n;
  Big y;
};

int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: coalesced_shell K EXTRA\n";return 2;}
  const int K=std::stoi(argv[1]);
  const int EXTRA=std::stoi(argv[2]);
  if(K<2||K>40||EXTRA<0||EXTRA>8192)return 2;

  std::vector<u128> p3(K+2);
  p3[0]=1;
  for(int i=1;i<(int)p3.size();++i)p3[i]=3*p3[i-1];

  // Exact odd-shell state after one shortcut step:
  // n=2A+1 -> T(n)=3A+2.
  std::vector<State> cur,next;
  cur.push_back({1,2,1});

  uint64_t total_closed=0,total_coalesced=0;
  uint64_t peak_states=1;
  int peak_t=1;

  for(int t=1;t<=K;++t){
    // First quotient identical futures; then test the dominating representative.
    const uint64_t merged=coalesce(cur);
    total_coalesced+=merged;

    next.clear();
    next.reserve(cur.size());
    uint64_t closed_here=0;
    for(const auto&s:cur){
      if(uniform_closed(s,t,K,p3)){
        ++closed_here;++total_closed;
      }else next.push_back(s);
    }
    cur.swap(next);

    if(cur.size()>peak_states){peak_states=cur.size();peak_t=t;}

    std::cout<<"COALESCED_SYMBOLIC_LEVEL"
             <<" t="<<t
             <<" live="<<cur.size()
             <<" merged="<<merged
             <<" closed="<<closed_here
             <<" total_merged="<<total_coalesced<<"\n";

    if(cur.empty()){
      std::cout<<"COALESCED_SYMBOLIC_DONE K="<<K
               <<" extra="<<EXTRA
               <<" final_t="<<t
               <<" live=0"
               <<" peak_states="<<peak_states
               <<" peak_t="<<peak_t
               <<" total_merged="<<total_coalesced<<"\n";
      std::cout<<"VERIFIED_COALESCED_SYMBOLIC_ODD_SHELL_CLOSURE\n";
      return 0;
    }

    if(t<K){
      if(cur.size()>SIZE_MAX/2){std::cerr<<"STATE_COUNT_OVERFLOW\n";return 6;}
      next.clear();
      next.reserve(cur.size()*2);
      for(const auto&s:cur){
        next.push_back(child(s,t,0,p3));
        next.push_back(child(s,t,1,p3));
      }
      cur.swap(next);
    }
  }

  // At depth K, A=1 exactly.  Convert each dominant future state into one
  // concrete hardest shell member.  Equal futures have already been merged.
  std::vector<Concrete> concrete;
  concrete.reserve(cur.size());
  const Big shellM=Big(1)<<K;
  for(const auto&s:cur){
    const Big n=shellM+s.b;
    const Big y=Big(p3[s.c])+s.d;
    concrete.push_back({n,y});
  }

  std::cout<<"COALESCED_CONCRETE_START K="<<K
           <<" states="<<concrete.size()<<"\n";

  for(int f=1;f<=EXTRA && !concrete.empty();++f){
    size_t w=0;
    uint64_t closed_here=0;

    for(auto& z:concrete){
      z.y=Tbig(z.y);

      bool closed=(z.y<z.n);
      if(!closed && z.y%3==2){
        const Big p=(2*z.y-1)/3;
        closed=(p>0 && p<z.n);
        if(closed && Tbig(p)!=z.y){
          std::cerr<<"CONCRETE_CONE_REPLAY_FAIL\n";
          return 7;
        }
      }

      if(closed){
        ++closed_here;++total_closed;
      }else{
        concrete[w++]=std::move(z);
      }
    }
    concrete.resize(w);

    if(f<=10 || f%25==0 || concrete.empty())
      std::cout<<"COALESCED_CONCRETE_LEVEL"
               <<" f="<<f
               <<" live="<<concrete.size()
               <<" closed="<<closed_here<<"\n";
  }

  std::cout<<"COALESCED_SYMBOLIC_DONE K="<<K
           <<" extra="<<EXTRA
           <<" final_t="<<K+EXTRA
           <<" live="<<concrete.size()
           <<" peak_states="<<peak_states
           <<" peak_t="<<peak_t
           <<" total_merged="<<total_coalesced<<"\n";

  if(concrete.empty())
    std::cout<<"VERIFIED_COALESCED_SYMBOLIC_ODD_SHELL_CLOSURE\n";
  else
    std::cout<<"COALESCED_SYMBOLIC_RESIDUAL_REMAINS\n";
  return 0;
}
