// Live-only recursive Collatz closure with compiled reverse bridges.
//
// This is a scalability scout for the exact constructor system.
//
// Unlike collatz_recursive_constructor_sieve.cpp, it does NOT enumerate all
// 2^k residues and intentionally omits the same-depth coalescence constructor.
// It carries only unresolved affine families forward.  Therefore it is a
// sound weaker system: every closure it reports is exact, while extra live
// states are UNKNOWN rather than false.
//
// State at depth k:
//   b mod 2^k,
//   T^k(a*2^k+b) = a*3^c + d  for all a>=0.
//
// Exact child states are derived algebraically in O(1).  Each child is then
// tested by:
//   C) universal direct descent;
//   D) the compiled reverse-predecessor bridge.
//
// Closed children are discarded immediately and never materialized again.
// This is the RealityGraph-style "future work compiled away" path.
//
// For memory efficiency c is packed into the low 6 bits of dc=(d<<6)|c.
// The program aborts rather than truncate if this exact representation is
// insufficient.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;

static inline u128 T(u128 n){return (n&1)?(3*n+1)/2:n/2;}
static u128 iterate(u128 n,int steps){for(int i=0;i<steps;++i)n=T(n);return n;}

struct RevCert{int o;int steps;uint64_t C;uint64_t residue;};

static std::vector<std::unordered_map<uint64_t,RevCert>>
load_bank(const std::string& path,int& max_o){
  std::ifstream in(path);
  if(!in){std::cerr<<"BANK_OPEN_FAILED\n";std::exit(2);}
  std::vector<RevCert> all;max_o=0;std::string line;
  while(std::getline(in,line)){
    if(line.empty())continue;
    std::istringstream ss(line);RevCert z{};
    if(!(ss>>z.o>>z.steps>>z.C>>z.residue)){
      std::cerr<<"BANK_PARSE_FAILED\n";std::exit(3);
    }
    max_o=std::max(max_o,z.o);all.push_back(z);
  }
  std::vector<std::unordered_map<uint64_t,RevCert>> bank(max_o+1);
  for(const auto& z:all){
    auto [it,ok]=bank[z.o].emplace(z.residue,z);
    if(!ok){std::cerr<<"BANK_DUPLICATE\n";std::exit(4);}
  }
  std::cout<<"LIVE_BRIDGE_BANK certificates="<<all.size()
           <<" max_o="<<max_o<<"\n";
  return bank;
}

struct State{uint64_t b;uint64_t dc;};
static constexpr uint64_t CMASK=63;

static State make_state(uint64_t b,uint64_t d,int c){
  if(c<0||c>=64){std::cerr<<"PACK_C_RANGE\n";std::exit(5);}
  if(d>=(UINT64_C(1)<<58)){std::cerr<<"PACK_D_RANGE\n";std::exit(6);}
  return {b,(d<<6)|uint64_t(c)};
}
static inline int state_c(const State&s){return int(s.dc&CMASK);}
static inline uint64_t state_d(const State&s){return s.dc>>6;}

static bool bridge_closes(
    uint64_t b,int c,uint64_t d,int k,
    const std::vector<std::unordered_map<uint64_t,RevCert>>& bank,
    int max_o,const std::vector<uint64_t>& p3,
    RevCert& used,i128& pcoef,i128& pconst){
  const int top=std::min(c,max_o);
  uint64_t mod=1;
  for(int o=1;o<=top;++o){
    mod*=3;
    auto it=bank[o].find(d%mod);
    if(it==bank[o].end())continue;
    const RevCert& z=it->second;
    const i128 den=i128(mod);
    const i128 nc=(i128(1)<<z.steps)*i128(d)-i128(z.C);
    if(nc%den!=0){std::cerr<<"BRIDGE_DIV_FAIL\n";std::exit(7);}
    pconst=nc/den;
    pcoef=(i128(1)<<z.steps)*i128(p3[c-z.o]);
    const i128 L=pcoef-(i128(1)<<k);
    const i128 R=i128(b)-pconst;
    if(L<0&&L<R&&pcoef+pconst>0){used=z;return true;}
    return false; // prefix-free retained reverse bank
  }
  return false;
}

// Stronger nested O^j reverse family, intentionally retained even though O
// already makes the predecessor smaller than the *future* target m.
//
// If d == -1 (mod 3^j), then for every affine parameter a (provided c>=j):
//
//   m(a) = a*3^c + d
//   p_j(a) = 2^j * ((m(a)+1)/3^j) - 1
//          = a*2^j*3^(c-j) + 2^j*((d+1)/3^j) - 1
//
// and T^j(p_j(a)) = m(a).  Larger j gives a stronger coefficient contraction
// (2/3)^j, which can beat the original n even when the first O bridge cannot.
static bool deep_o_closes(
    uint64_t b,int c,uint64_t d,int k,
    const std::vector<uint64_t>& p3,
    int& used_j,i128& pcoef,i128& pconst){
  if(c<2 || d==UINT64_MAX)return false;
  const uint64_t dp1=d+1;

  int maxj=0;
  for(int j=1;j<=c;++j){
    if(dp1%p3[j])break;
    maxj=j;
  }
  if(maxj<2)return false;

  const i128 M=i128(1)<<k;
  for(int j=2;j<=maxj;++j){
    const uint64_t q=dp1/p3[j];
    const i128 pc=(i128(1)<<j)*i128(q)-1;
    const i128 pa=(i128(1)<<j)*i128(p3[c-j]);
    const i128 L=pa-M;
    const i128 R=i128(b)-pc;
    if(L<0&&L<R&&pa+pc>0){
      used_j=j;pcoef=pa;pconst=pc;return true;
    }
  }
  return false;
}

// Parametric reverse family O,E,O^r collapsed into one exact schema.
//
// For m with 3^(r+1) | (2m+1), define
//
//   p_r = 2^r * (4m+1)/3^(r+1) - 1.
//
// This is exactly the reverse word O,E,O^r.  In affine numerator form the
// recurrence gives C_r = 3^(r+1)-2^r, hence
//
//   p_r = [2^(r+2)m - (3^(r+1)-2^r)] / 3^(r+1)
//       = 2^r*(4m+1)/3^(r+1)-1.
//
// Therefore T^(r+2)(p_r)=m.
//
// For m(a)=a*3^c+d this is uniform whenever c>=r+1 and
// 3^(r+1)|(4d+1), with affine predecessor
//
//   A = 2^(r+2) * 3^(c-r-1)
//   D = 2^r * (4d+1)/3^(r+1) - 1.
static bool param_eor_closes(
    uint64_t b,int c,uint64_t d,int k,
    const std::vector<uint64_t>& p3,
    int& used_r,i128& outA,i128& outD){
  if(c<2 || d>(UINT64_MAX-1)/4)return false;
  const uint64_t z=4*d+1;

  for(int r=1;r+1<=c;++r){
    const uint64_t den=p3[r+1];
    if(z%den!=0)break; // divisibility is nested in r
    const uint64_t q=z/den;
    const i128 A=(i128(1)<<(r+2))*i128(p3[c-r-1]);
    const i128 D=(i128(1)<<r)*i128(q)-1;
    const i128 M=i128(1)<<k;
    const i128 L=A-M;
    const i128 R=i128(b)-D;
    if(A>0 && A+D>0 && L<0 && L<R){
      used_r=r;outA=A;outD=D;return true;
    }
  }
  return false;
}

int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: live_recursive K BANK\n";return 2;}
  const int K=std::stoi(argv[1]);
  const std::string bankpath=argv[2];
  if(K<1||K>34){std::cerr<<"K_OUT_OF_RANGE\n";return 2;}

  std::vector<uint64_t> p3(K+2,1);
  for(int i=1;i<(int)p3.size();++i){
    if(p3[i-1]>UINT64_MAX/3){std::cerr<<"P3_OVERFLOW\n";return 3;}
    p3[i]=p3[i-1]*3;
  }

  int max_o=0;
  const auto bank=load_bank(bankpath,max_o);

  std::vector<State> cur,next;
  cur.push_back(make_state(0,0,0));
  uint64_t total_descent=0,total_bridge=0,total_deep_o=0,total_param_eor=0;
  uint64_t bridge_controls=0,deep_o_controls=0,param_controls=0;

  for(int k=1;k<=K;++k){
    const uint64_t half=UINT64_C(1)<<(k-1);
    const uint64_t M=UINT64_C(1)<<k;
    next.clear();
    if(cur.size()<=std::numeric_limits<size_t>::max()/2)
      next.reserve(cur.size()*2);

    uint64_t descent=0,bridge=0,deep_o=0,param_eor=0;

    for(const State&s:cur){
      const uint64_t b0=s.b,d0=state_d(s);
      const int c0=state_c(s);
      if(c0>k){std::cerr<<"STATE_C_IMPOSSIBLE\n";return 8;}

      for(int e=0;e<2;++e){
        const uint64_t b=b0+(e?half:0);
        const uint64_t y=d0+(e?p3[c0]:0);
        int c=c0;uint64_t d;
        if(y&1){
          ++c;
          if(y>(UINT64_MAX-1)/3){std::cerr<<"CHILD_D_OVERFLOW\n";return 9;}
          d=(3*y+1)/2;
        }else d=y/2;

        const i128 L=i128(p3[c])-i128(M);
        const i128 R=i128(b)-i128(d);
        if(L<0&&L<R){++descent;++total_descent;continue;}

        RevCert z{};i128 pc=0,pk=0;
        if(bridge_closes(b,c,d,k,bank,max_o,p3,z,pc,pk)){
          ++bridge;++total_bridge;

          // Deterministic direct controls on every bridge while the total is
          // modest, then on a fixed prefix.  Exact algebra above remains the
          // certificate for all accepted families.
          if(bridge_controls<20000){
            for(uint64_t a:{1ULL,3ULL}){
              const u128 n=u128(a)*M+b;
              const u128 m=u128(a)*p3[c]+d;
              const i128 ps=i128(a)*pc+pk;
              if(ps<=0||u128(ps)>=n||iterate(n,k)!=m||
                 iterate(u128(ps),z.steps)!=m){
                std::cerr<<"LIVE_BRIDGE_CONTROL_FAILED k="<<k<<" b="<<b<<"\n";
                return 10;
              }
              ++bridge_controls;
            }
          }
          continue;
        }

        int oj=0;i128 opc=0,opk=0;
        if(deep_o_closes(b,c,d,k,p3,oj,opc,opk)){
          ++deep_o;++total_deep_o;

          if(deep_o_controls<20000){
            for(uint64_t a:{1ULL,3ULL}){
              const u128 n=u128(a)*M+b;
              const u128 m=u128(a)*p3[c]+d;
              const i128 ps=i128(a)*opc+opk;
              if(ps<=0||u128(ps)>=n||iterate(n,k)!=m||
                 iterate(u128(ps),oj)!=m){
                std::cerr<<"DEEP_O_CONTROL_FAILED k="<<k<<" b="<<b
                         <<" j="<<oj<<"\n";
                return 11;
              }
              ++deep_o_controls;
            }
          }
          continue;
        }

        int er=0;i128 eA=0,eD=0;
        if(param_eor_closes(b,c,d,k,p3,er,eA,eD)){
          ++param_eor;++total_param_eor;

          if(param_controls<20000){
            for(uint64_t a:{1ULL,3ULL}){
              const u128 n=u128(a)*M+b;
              const u128 m=u128(a)*p3[c]+d;
              const i128 ps=i128(a)*eA+eD;
              if(ps<=0||u128(ps)>=n||
                 iterate(n,k)!=m||
                 iterate(u128(ps),er+2)!=m){
                std::cerr<<"PARAM_EOR_CONTROL_FAILED k="<<k
                         <<" b="<<b<<" r="<<er<<"\n";
                return 12;
              }
              ++param_controls;
            }
          }
          continue;
        }

        next.push_back(make_state(b,d,c));
      }
    }

    const double frac=double(next.size())/double(UINT64_C(1)<<(k-1));
    std::cout<<"LIVE_RECURSIVE_LEVEL"
             <<" k="<<k
             <<" parents="<<cur.size()
             <<" descent="<<descent
             <<" bridge="<<bridge
             <<" deep_o="<<deep_o
             <<" param_eor="<<param_eor
             <<" live="<<next.size()
             <<" odd_live_fraction="<<frac<<"\n";
    cur.swap(next);
  }

  std::cout<<"LIVE_RECURSIVE_DONE K="<<K
           <<" final_live="<<cur.size()
           <<" total_descent="<<total_descent
           <<" total_bridge="<<total_bridge
           <<" total_deep_o="<<total_deep_o
           <<" total_param_eor="<<total_param_eor
           <<" bridge_controls="<<bridge_controls
           <<" deep_o_controls="<<deep_o_controls
           <<" param_controls="<<param_controls<<"\n";
  std::cout<<"VERIFIED_PARAMETRIC_EOR_CONSTRUCTOR_SIEVE\n";
  return 0;
}
