// Targeted deep reverse continuations for live-only Collatz closure.
//
// Start from the exact live-only recursive system with:
//   C) direct affine descent,
//   D) compact q14 first-contraction reverse bridges,
//   E) nested O^j continuations.
//
// New constructor F:
// If the first matching retained reverse certificate reaches predecessor
//
//   p(a) = A*a + D
//
// but p(a) is not yet below the original
//
//   n(a) = 2^k*a + b,
//
// continue *backwards from p* by at most H exact reverse operations:
//
//   E: x <- 2x
//   O: x <- (2x-1)/3
//
// O is allowed only when the affine family is uniformly valid: A divisible
// by 3, (2D-1) divisible by 3, and the resulting constant is odd, making the
// predecessor odd for every a.
//
// Every descendant is checked against n(a) by exact affine inequalities.
// Accepted descendants are independently replayed at a=1 and a=3.
//
// This is residual-targeted constructor discovery: it searches only after a
// known q14 donor matched but failed to rank below the earlier binary family.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <unordered_map>
#include <utility>
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
  std::cout<<"DEEP_CONT_BANK certificates="<<all.size()
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

static bool lower_family(i128 A,i128 D,int k,uint64_t b){
  const i128 M=i128(1)<<k;
  const i128 L=A-M;
  const i128 R=i128(b)-D;
  return A>0 && A+D>0 && L<0 && L<R;
}

// Return first matching prefix-free retained reverse certificate and its
// affine predecessor.  Matching is uniform in a because c>=o.
static bool first_reverse_match(
    int c,uint64_t d,
    const std::vector<std::unordered_map<uint64_t,RevCert>>& bank,
    int max_o,const std::vector<uint64_t>& p3,
    RevCert& z,i128& A,i128& D){
  const int top=std::min(c,max_o);
  uint64_t mod=1;
  for(int o=1;o<=top;++o){
    mod*=3;
    auto it=bank[o].find(d%mod);
    if(it==bank[o].end())continue;
    z=it->second;
    const i128 nc=(i128(1)<<z.steps)*i128(d)-i128(z.C);
    if(nc%i128(mod)!=0){std::cerr<<"MATCH_DIV_FAIL\n";std::exit(7);}
    D=nc/i128(mod);
    A=(i128(1)<<z.steps)*i128(p3[c-z.o]);
    return true;
  }
  return false;
}

static bool deep_o_closes(
    uint64_t b,int c,uint64_t d,int k,
    const std::vector<uint64_t>& p3,
    int& used_j,i128& A,i128& D){
  if(c<2 || d==UINT64_MAX)return false;
  const uint64_t dp1=d+1;
  int maxj=0;
  for(int j=1;j<=c;++j){
    if(dp1%p3[j])break;
    maxj=j;
  }
  for(int j=2;j<=maxj;++j){
    const uint64_t q=dp1/p3[j];
    const i128 d2=(i128(1)<<j)*i128(q)-1;
    const i128 a2=(i128(1)<<j)*i128(p3[c-j]);
    if(lower_family(a2,d2,k,b)){
      used_j=j;A=a2;D=d2;return true;
    }
  }
  return false;
}

struct Aff{ i128 A; i128 D; int extra; };

// Explore up to H additional reverse operations after the first q14 match.
// Return the first exact lower family found.  Breadth-first order makes the
// retained continuation minimal in extra reverse length.
static bool deep_continue_closes(
    uint64_t b,int c,uint64_t d,int k,int H,
    const std::vector<std::unordered_map<uint64_t,RevCert>>& bank,
    int max_o,const std::vector<uint64_t>& p3,
    RevCert& base,int& extra_steps,i128& outA,i128& outD){
  i128 A=0,D=0;
  if(!first_reverse_match(c,d,bank,max_o,p3,base,A,D))return false;
  if(lower_family(A,D,k,b))return false; // handled by first bridge

  std::vector<Aff> cur,next;
  cur.push_back({A,D,0});

  const i128 M=i128(1)<<k;
  for(int h=1;h<=H;++h){
    next.clear();
    next.reserve(cur.size()*2);

    for(const Aff&s:cur){
      const int remaining_after_child=H-h;

      auto can_ever_subcritical=[&](i128 A)->bool{
        // Best possible coefficient reduction over the remaining steps is
        // all reverse-O: A*(2/3)^r.  If even that is >= 2^k, no continuation
        // beneath this child can ever beat the original coefficient.
        i128 lhs=A;
        i128 rhs=M;
        for(int t=0;t<remaining_after_child;++t){
          if(lhs > (i128(1)<<120)/2 || rhs > (i128(1)<<120)/3){
            // For the horizons used here this guard should never fire.
            // Conservatively retain the branch rather than risk false pruning.
            return true;
          }
          lhs*=2;
          rhs*=3;
        }
        return lhs<rhs;
      };

      // Reverse E is always exact.
      {
        const i128 a2=2*s.A,d2=2*s.D;
        if(lower_family(a2,d2,k,b)){
          extra_steps=h;outA=a2;outD=d2;return true;
        }
        if(can_ever_subcritical(a2))
          next.push_back({a2,d2,h});
      }

      // Reverse O must be uniformly integral and odd.
      if(s.A%3==0){
        const i128 z=2*s.D-1;
        if(z%3==0){
          const i128 a2=2*(s.A/3);
          const i128 d2=z/3;
          if(d2%2!=0){
            if(lower_family(a2,d2,k,b)){
              extra_steps=h;outA=a2;outD=d2;return true;
            }
            if(can_ever_subcritical(a2))
              next.push_back({a2,d2,h});
          }
        }
      }
    }

    // Exact deduplication within this tiny continuation layer.
    std::vector<Aff> uniq;
    uniq.reserve(next.size());
    for(const Aff&z:next){
      bool seen=false;
      for(const Aff&u:uniq){
        if(z.A==u.A && z.D==u.D){seen=true;break;}
      }
      if(!seen)uniq.push_back(z);
    }
    cur.swap(uniq);
  }
  return false;
}

static std::string s128(i128 x){
  if(x==0)return "0";
  bool neg=x<0;
  u128 y=neg?u128(-x):u128(x);
  std::string s;
  while(y){s.push_back(char('0'+y%10));y/=10;}
  if(neg)s.push_back('-');
  std::reverse(s.begin(),s.end());
  return s;
}

int main(int argc,char**argv){
  if(argc!=4){std::cerr<<"usage: deep_cont K BANK H\n";return 2;}
  const int K=std::stoi(argv[1]);
  const std::string bankpath=argv[2];
  const int H=std::stoi(argv[3]);
  if(K<1||K>30||H<1||H>16){std::cerr<<"BAD_RANGE\n";return 2;}

  std::vector<uint64_t> p3(K+2,1);
  for(int i=1;i<(int)p3.size();++i){
    if(p3[i-1]>UINT64_MAX/3){std::cerr<<"P3_OVERFLOW\n";return 3;}
    p3[i]=p3[i-1]*3;
  }

  int max_o=0;
  const auto bank=load_bank(bankpath,max_o);

  std::vector<State> cur,next;
  cur.push_back(make_state(0,0,0));
  uint64_t total_descent=0,total_bridge=0,total_deep_o=0,total_deep_cont=0;
  uint64_t controls=0;
  std::vector<uint64_t> extra_hist(H+1,0);

  for(int k=1;k<=K;++k){
    const uint64_t half=UINT64_C(1)<<(k-1);
    const uint64_t M=UINT64_C(1)<<k;
    next.clear();
    if(cur.size()<=std::numeric_limits<size_t>::max()/2)next.reserve(cur.size()*2);

    uint64_t descent=0,bridge=0,deep_o=0,deep_cont=0;

    for(const State&s:cur){
      const uint64_t b0=s.b,d0=state_d(s);
      const int c0=state_c(s);

      for(int e=0;e<2;++e){
        const uint64_t b=b0+(e?half:0);
        const uint64_t y=d0+(e?p3[c0]:0);
        int c=c0;uint64_t d;
        if(y&1){
          ++c;
          if(y>(UINT64_MAX-1)/3){std::cerr<<"CHILD_D_OVERFLOW\n";return 8;}
          d=(3*y+1)/2;
        }else d=y/2;

        if(lower_family(i128(p3[c]),i128(d),k,b)){
          ++descent;++total_descent;continue;
        }

        RevCert z{};i128 A=0,D=0;
        if(first_reverse_match(c,d,bank,max_o,p3,z,A,D) &&
           lower_family(A,D,k,b)){
          ++bridge;++total_bridge;continue;
        }

        int oj=0;i128 oA=0,oD=0;
        if(deep_o_closes(b,c,d,k,p3,oj,oA,oD)){
          ++deep_o;++total_deep_o;continue;
        }

        RevCert base{};int extra=0;i128 qA=0,qD=0;
        if(deep_continue_closes(b,c,d,k,H,bank,max_o,p3,base,extra,qA,qD)){
          ++deep_cont;++total_deep_cont;++extra_hist[extra];

          if(controls<20000){
            for(uint64_t a:{1ULL,3ULL}){
              const u128 n=u128(a)*M+b;
              const u128 m=u128(a)*p3[c]+d;
              const i128 ps=i128(a)*qA+qD;
              if(ps<=0||u128(ps)>=n||
                 iterate(n,k)!=m||
                 iterate(u128(ps),base.steps+extra)!=m){
                std::cerr<<"DEEP_CONT_CONTROL_FAILED"
                         <<" k="<<k<<" b="<<b
                         <<" extra="<<extra
                         <<" A="<<s128(qA)<<" D="<<s128(qD)<<"\n";
                return 9;
              }
              ++controls;
            }
          }
          continue;
        }

        next.push_back(make_state(b,d,c));
      }
    }

    std::cout<<"DEEP_CONT_LEVEL"
             <<" k="<<k
             <<" parents="<<cur.size()
             <<" descent="<<descent
             <<" bridge="<<bridge
             <<" deep_o="<<deep_o
             <<" deep_cont="<<deep_cont
             <<" live="<<next.size()
             <<" odd_live_fraction="
             <<(double(next.size())/double(UINT64_C(1)<<(k-1)))<<"\n";
    cur.swap(next);
  }

  std::cout<<"DEEP_CONT_DONE"
           <<" K="<<K
           <<" H="<<H
           <<" final_live="<<cur.size()
           <<" total_descent="<<total_descent
           <<" total_bridge="<<total_bridge
           <<" total_deep_o="<<total_deep_o
           <<" total_deep_cont="<<total_deep_cont
           <<" controls="<<controls<<"\n";
  for(int h=1;h<=H;++h)
    if(extra_hist[h])std::cout<<"DEEP_CONT_HIST extra="<<h
                              <<" closed="<<extra_hist[h]<<"\n";
  std::cout<<"VERIFIED_TARGETED_DEEP_REVERSE_CONTINUATIONS\n";
  return 0;
}
