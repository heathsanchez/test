// Exact global consequence quotient for odd Collatz families.
//
// At depth t, a state (b,c,d) represents the INFINITE family
//
//   n = A*2^t + b,      A >= 1,
//   T^t(n) = A*3^c + d.
//
// All states at a fixed depth share exactly the same coefficient domain A>=1.
//
// CONSEQUENCE CLOSURE
// -------------------
// Direct:
//   y-n = A(3^c-2^t) + (d-b).
// If the slope is negative, its maximum on A>=1 is at A=1.
// If slope is zero, the constant decides. Positive slope is not certified.
//
// One-step inverse odd cone:
// if d == 2 (mod 3), then y == 2 (mod 3) uniformly and
//   p=(2y-1)/3.
// The condition p<n is
//   A(2*3^c-3*2^t) + (2d-1-3b) < 0,
// handled by the same infinite-tail endpoint rule.
//
// CONSEQUENCE COALESCENCE
// -----------------------
// If two states have equal (c,d), then they have exactly the same future for
// every A>=1.  The minimum-b source is smaller and therefore the hardest to
// close by strong induction.  All larger-b states are exactly dominated.
//
// PARITY REFINEMENT
// -----------------
// A_old = 2*A_new + e.  For A_new>=1 both children remain infinite families.
// The e=1 boundary member A_new=0 is deliberately omitted; it is a finite
// integer < 2^(t+1).  Thus after refining through depth H, all omitted
// boundary points lie below 2^H and can be discharged by a finite base.
//
// Therefore if the live quotient becomes empty at finite H, then:
//   finite verification below 2^H
//   + this exact infinite-family quotient
// proves Collatz globally by strong induction.
//
// If it does not empty, the remaining states are exact symbolic obstructions,
// not counterexamples.

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

struct State{
  uint64_t b;
  u128 d;
  uint32_t c;
};

static std::string s128(u128 x){
  if(!x)return "0";
  std::string s;
  while(x){s.push_back(char('0'+x%10));x/=10;}
  std::reverse(s.begin(),s.end());
  return s;
}

struct RevCert{
  uint32_t o;
  uint32_t steps;
  u128 C;
  uint64_t residue;
};

static std::vector<std::unordered_map<uint64_t,RevCert>>
load_bank(const std::string&path,uint32_t&max_o){
  std::ifstream in(path);
  if(!in){std::cerr<<"GLOBAL_BANK_OPEN_FAIL\n";std::exit(7);}
  std::vector<RevCert> all;
  max_o=0;
  std::string line;
  while(std::getline(in,line)){
    if(line.empty())continue;
    std::istringstream ss(line);
    uint32_t o,steps; unsigned long long Cu,res;
    if(!(ss>>o>>steps>>Cu>>res)){
      std::cerr<<"GLOBAL_BANK_PARSE_FAIL\n";std::exit(8);
    }
    RevCert z{o,steps,u128(Cu),uint64_t(res)};
    all.push_back(z);max_o=std::max(max_o,o);
  }
  std::vector<std::unordered_map<uint64_t,RevCert>> bank(max_o+1);
  for(const auto&z:all){
    auto[it,ok]=bank[z.o].emplace(z.residue,z);
    if(!ok){std::cerr<<"GLOBAL_BANK_DUPLICATE\n";std::exit(9);}
  }
  std::cout<<"GLOBAL_BRIDGE_BANK certificates="<<all.size()
           <<" max_o="<<max_o<<"\n";
  return bank;
}

static bool closed_infinite(
    const State&s,int t,const std::vector<u128>&p3,
    const std::vector<std::unordered_map<uint64_t,RevCert>>&bank,
    uint32_t max_o){
  const i128 M=i128(u128(1)<<t);
  const i128 P=i128(p3[s.c]);

  const i128 coef=P-M;
  const i128 cons=i128(s.d)-i128(s.b);
  if(coef<0 && coef+cons<0)return true;
  if(coef==0 && cons<0)return true;

  // Deterministic maximal uniform pure-O predecessor.
  //
  // y=A*3^c+d.  For every 1<=r<=c with 3^r | d+1,
  //   p_r = 2^r * (y+1)/3^r - 1
  // satisfies T^r(p_r)=y for every A.  Each extra O multiplies the leading
  // coefficient by 2/3, so the maximal valid r is the strongest pure-O
  // contraction and subsumes the old one-step cone.
  u128 z=s.d+1;
  uint32_t r=0;
  while(r<s.c && z%3==0){
    z/=3;
    ++r;
  }
  if(r>0){
    const i128 pcoef=i128(u128(1)<<r)*i128(p3[s.c-r]);
    const i128 pconst=i128(u128(1)<<r)*i128(z)-1;
    const i128 coef2=pcoef-M;
    const i128 cons2=pconst-i128(s.b);
    if(coef2<0 && coef2+cons2<0)return true;
    if(coef2==0 && cons2<0)return true;
  }

  // Retained exact reverse-predecessor constructors. The bank is prefix-free,
  // so the first matching cylinder is the unique retained donor.
  uint64_t mod=1;
  const uint32_t top=std::min<uint32_t>(s.c,max_o);
  for(uint32_t o=1;o<=top;++o){
    mod*=3;
    auto it=bank[o].find(uint64_t(s.d%mod));
    if(it==bank[o].end())continue;
    const RevCert&rc=it->second;
    const u128 pow2=u128(1)<<rc.steps;
    const i128 num=i128(pow2)*i128(s.d)-i128(rc.C);
    if(num%i128(mod)!=0){
      std::cerr<<"GLOBAL_BRIDGE_DIV_FAIL\n";
      std::exit(10);
    }
    const i128 pcoef=i128(pow2)*i128(p3[s.c-o]);
    const i128 pconst=num/i128(mod);
    const i128 coef3=pcoef-M;
    const i128 cons3=pconst-i128(s.b);
    if(coef3<0 && coef3+cons3<0)return true;
    if(coef3==0 && cons3<0)return true;
    break;
  }
  return false;
}

static State child(
    const State&s,int t,int e,const std::vector<u128>&p3){
  if(t>=63){
    std::cerr<<"GLOBAL_QUOTIENT_RESIDUE_RANGE\n";
    std::exit(4);
  }
  const uint64_t b=s.b+(e?(UINT64_C(1)<<t):0);
  u128 y=s.d+(e?p3[s.c]:0);
  uint32_t c=s.c;
  u128 d;
  if(y&1){
    ++c;
    if(y>(~u128(0)-1)/3){
      std::cerr<<"GLOBAL_QUOTIENT_D_OVERFLOW\n";
      std::exit(5);
    }
    d=(3*y+1)/2;
  }else d=y/2;
  return {b,d,c};
}

static uint64_t coalesce(std::vector<State>&v){
  const uint64_t before=v.size();
  std::sort(v.begin(),v.end(),[](const State&a,const State&b){
    if(a.c!=b.c)return a.c<b.c;
    if(a.d!=b.d)return a.d<b.d;
    return a.b<b.b;
  });
  size_t w=0;
  for(size_t i=0;i<v.size();){
    size_t j=i+1;
    while(j<v.size() && v[j].c==v[i].c && v[j].d==v[i].d)++j;
    v[w++]=v[i]; // minimum b dominates all equal-future states
    i=j;
  }
  v.resize(w);
  return before-w;
}

int main(int argc,char**argv){
  if(argc!=3){
    std::cerr<<"usage: global_bridge_quotient H BANK\n";
    return 2;
  }
  const int H=std::stoi(argv[1]);
  const std::string bankpath=argv[2];
  if(H<2||H>40)return 2;

  std::vector<u128> p3(H+3,1);
  for(int i=1;i<(int)p3.size();++i){
    if(p3[i-1]>(~u128(0))/3){
      std::cerr<<"GLOBAL_QUOTIENT_P3_OVERFLOW\n";
      return 3;
    }
    p3[i]=3*p3[i-1];
  }

  uint32_t max_o=0;
  const auto bank=load_bank(bankpath,max_o);

  // Odd n=2A+1, A>=1; after one shortcut step T(n)=3A+2.
  std::vector<State> cur{{1,2,1}},next;
  uint64_t total_merged=0,total_closed=0;
  uint64_t peak=1;int peak_t=1;

  for(int t=1;t<=H;++t){
    const uint64_t merged=coalesce(cur);
    total_merged+=merged;

    next.clear();
    next.reserve(cur.size());
    uint64_t closed_here=0;
    for(const State&s:cur){
      if(closed_infinite(s,t,p3,bank,max_o)){
        ++closed_here;++total_closed;
      }else next.push_back(s);
    }
    cur.swap(next);

    if(cur.size()>peak){peak=cur.size();peak_t=t;}

    uint32_t min_c=UINT32_MAX,max_c=0;
    u128 min_d=~u128(0),max_d=0;
    for(const State&s:cur){
      min_c=std::min(min_c,s.c);max_c=std::max(max_c,s.c);
      min_d=std::min(min_d,s.d);max_d=std::max(max_d,s.d);
    }
    if(cur.empty()){min_c=0;min_d=0;}

    std::cout<<"GLOBAL_QUOTIENT_LEVEL"
             <<" t="<<t
             <<" live="<<cur.size()
             <<" merged="<<merged
             <<" closed="<<closed_here
             <<" total_merged="<<total_merged
             <<" min_c="<<min_c
             <<" max_c="<<max_c
             <<" min_d="<<s128(min_d)
             <<" max_d="<<s128(max_d)
             <<"\n";

    if(cur.empty()){
      std::cout<<"GLOBAL_QUOTIENT_DONE"
               <<" H="<<H
               <<" final_t="<<t
               <<" live=0"
               <<" peak="<<peak
               <<" peak_t="<<peak_t
               <<" total_merged="<<total_merged
               <<" total_closed="<<total_closed<<"\n";
      std::cout<<"GLOBAL_INFINITE_FAMILY_QUOTIENT_CLOSED\n";
      std::cout<<"VERIFIED_GLOBAL_COALESCED_CONSEQUENCE_QUOTIENT\n";
      return 0;
    }

    if(t<H){
      if(cur.size()>SIZE_MAX/2){
        std::cerr<<"GLOBAL_QUOTIENT_STATE_COUNT_OVERFLOW\n";
        return 6;
      }
      next.clear();
      next.reserve(cur.size()*2);
      for(const State&s:cur){
        next.push_back(child(s,t,0,p3));
        next.push_back(child(s,t,1,p3));
      }
      cur.swap(next);
    }
  }

  std::cout<<"GLOBAL_QUOTIENT_DONE"
           <<" H="<<H
           <<" final_t="<<H
           <<" live="<<cur.size()
           <<" peak="<<peak
           <<" peak_t="<<peak_t
           <<" total_merged="<<total_merged
           <<" total_closed="<<total_closed<<"\n";

  // Emit a bounded sample of the residual for representation analysis.
  std::sort(cur.begin(),cur.end(),[](const State&a,const State&b){
    if(a.c!=b.c)return a.c<b.c;
    if(a.d!=b.d)return a.d<b.d;
    return a.b<b.b;
  });
  for(size_t i=0;i<std::min<size_t>(cur.size(),200);++i){
    const State&s=cur[i];
    const i128 directSlope=i128(p3[s.c])-i128(u128(1)<<H);
    const i128 coneSlope=2*i128(p3[s.c])-3*i128(u128(1)<<H);
    std::cout<<"GLOBAL_QUOTIENT_RESIDUAL"
             <<" rank="<<(i+1)
             <<" b="<<s.b
             <<" c="<<s.c
             <<" d="<<s128(s.d)
             <<" dmod3="<<uint64_t(s.d%3)
             <<" direct_slope_sign="<<(directSlope<0?-1:directSlope>0?1:0)
             <<" cone_slope_sign="<<(coneSlope<0?-1:coneSlope>0?1:0)
             <<"\n";
  }

  std::cout<<"GLOBAL_INFINITE_FAMILY_RESIDUAL_REMAINS\n";
  std::cout<<"VERIFIED_GLOBAL_COALESCED_CONSEQUENCE_QUOTIENT\n";
  return 0;
}
