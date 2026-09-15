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
#include <map>
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

// Macro reverse block R_r = E O^r.
//
// For an affine family x(a)=A*a+D:
//
//   r=0: R_0(x)=2x,
//   r>=1:
//     R_r(x)=2^r*(2x+1)/3^r - 1,
//
// valid uniformly when 3^r divides both A and 2D+1.
//
// Every E/O continuation word decomposes uniquely into a sequence of these
// blocks.  Searching macro depth therefore searches structural run lengths,
// not individual reverse bits.
struct MacroState{
  i128 A;
  i128 D;
  int reverse_steps;
};

static int v3_i128(i128 x,int cap){
  if(x<0)x=-x;
  int v=0;
  while(v<cap && x%3==0){x/=3;++v;}
  return v;
}

static bool macro_blocks_close(
    uint64_t b,int k,
    i128 startA,i128 startD,
    int max_macro_depth,
    int& used_macro_depth,
    int& used_reverse_steps,
    i128& outA,i128& outD){
  std::vector<MacroState> cur,next;
  cur.push_back({startA,startD,0});
  const i128 M=i128(1)<<k;

  for(int depth=1;depth<=max_macro_depth;++depth){
    next.clear();

    for(const MacroState&s:cur){
      const int va=v3_i128(s.A,64);
      const int vd=v3_i128(2*s.D+1,64);
      const int rmax=std::min(va,vd);

      for(int r=0;r<=rmax;++r){
        i128 A,D;
        int add_steps;
        if(r==0){
          A=2*s.A;
          D=2*s.D;
          add_steps=1;
        }else{
          i128 den=1,pow2=1;
          for(int j=0;j<r;++j){den*=3;pow2*=2;}
          A=(2*pow2*s.A)/den;
          D=(pow2*(2*s.D+1))/den-1;
          add_steps=r+1;
        }

        const i128 L=A-M;
        const i128 R=i128(b)-D;
        if(A>0 && A+D>0 && L<0 && L<R){
          used_macro_depth=depth;
          used_reverse_steps=s.reverse_steps+add_steps;
          outA=A;outD=D;
          return true;
        }

        next.push_back({A,D,s.reverse_steps+add_steps});
      }
    }

    // Exact deduplication by affine state; retain the shortest reverse-step
    // realization of each state.
    std::vector<MacroState> uniq;
    for(const MacroState&z:next){
      bool found=false;
      for(MacroState&u:uniq){
        if(z.A==u.A && z.D==u.D){
          if(z.reverse_steps<u.reverse_steps)u.reverse_steps=z.reverse_steps;
          found=true;break;
        }
      }
      if(!found)uniq.push_back(z);
    }
    cur.swap(uniq);
  }
  return false;
}

static int v3_u128(u128 x,int cap=64){
  int v=0;
  while(v<cap && x%3==0){x/=3;++v;}
  return v;
}

// Exact shell-specific reverse macro search.  Here the affine parameter is
// fixed to a=1, so the state is the concrete positive integer predecessor.
// This proves closure only for the bit-length shell n=2^K+b, not for the
// whole family a*2^K+b.
static bool shell_macro_close(
    u128 start,u128 n,int max_blocks,
    int& used_blocks,int& used_reverse_steps,
    u128& witness){
  struct Node{u128 x;int blocks;int steps;};
  std::vector<Node> cur,next;
  cur.push_back({start,0,0});

  for(int depth=1;depth<=max_blocks;++depth){
    next.clear();

    for(const Node&s:cur){
      if(s.x==0)continue;
      // R_0 = reverse E.
      {
        const u128 x2=2*s.x;
        if(x2<n){
          used_blocks=depth;
          used_reverse_steps=s.steps+1;
          witness=x2;
          return true;
        }
        next.push_back({x2,depth,s.steps+1});
      }

      // R_r = E O^r, r>=1.
      const u128 z=2*s.x+1;
      const int rmax=v3_u128(z,64);
      u128 den=1,pow2=1;
      for(int r=1;r<=rmax;++r){
        den*=3;pow2*=2;
        const u128 x2=pow2*z/den-1;
        if(x2==0)continue;
        if(x2<n){
          used_blocks=depth;
          used_reverse_steps=s.steps+r+1;
          witness=x2;
          return true;
        }
        next.push_back({x2,depth,s.steps+r+1});
      }
    }

    // Exact bounded deduplication by concrete predecessor value.
    std::sort(next.begin(),next.end(),[](const Node&a,const Node&b){
      if(a.x!=b.x)return a.x<b.x;
      return a.steps<b.steps;
    });
    std::vector<Node> uniq;
    for(const Node&z:next){
      if(uniq.empty()||uniq.back().x!=z.x)uniq.push_back(z);
      else if(z.steps<uniq.back().steps)uniq.back().steps=z.steps;
    }
    cur.swap(uniq);
  }
  return false;
}

static std::string u128str(u128 x){
  if(!x)return "0";
  std::string s;
  while(x){s.push_back(char('0'+x%10));x/=10;}
  std::reverse(s.begin(),s.end());
  return s;
}

int main(int argc,char**argv){
  if(argc!=4){std::cerr<<"usage: shell_frontier K BANK SHELL_MACRO_DEPTH\n";return 2;}
  const int K=std::stoi(argv[1]);
  const std::string bankpath=argv[2];
  const int shell_macro_depth=std::stoi(argv[3]);
  const int macro_depth=6;
  if(K<1||K>30||shell_macro_depth<0||shell_macro_depth>12){
    std::cerr<<"K_OR_SHELL_DEPTH_OUT_OF_RANGE\n";return 2;
  }

  std::vector<uint64_t> p3(K+2,1);
  for(int i=1;i<(int)p3.size();++i){
    if(p3[i-1]>UINT64_MAX/3){std::cerr<<"P3_OVERFLOW\n";return 3;}
    p3[i]=p3[i-1]*3;
  }

  int max_o=0;
  const auto bank=load_bank(bankpath,max_o);

  std::vector<State> cur,next;
  cur.push_back(make_state(0,0,0));
  uint64_t total_descent=0,total_bridge=0,total_deep_o=0,total_macro=0;
  uint64_t bridge_controls=0,deep_o_controls=0,macro_controls=0;
  std::vector<uint64_t> macro_depth_hist(macro_depth+1,0);

  for(int k=1;k<=K;++k){
    const uint64_t half=UINT64_C(1)<<(k-1);
    const uint64_t M=UINT64_C(1)<<k;
    next.clear();
    if(cur.size()<=std::numeric_limits<size_t>::max()/2)
      next.reserve(cur.size()*2);

    uint64_t descent=0,bridge=0,deep_o=0,macro=0;

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

        // Start macro grammar from the first matching q14 donor.
        RevCert mb{};i128 mA=0,mD=0;
        bool have_base=false;
        {
          const int top=std::min(c,max_o);
          uint64_t mod=1;
          for(int o=1;o<=top;++o){
            mod*=3;
            auto it=bank[o].find(d%mod);
            if(it==bank[o].end())continue;
            mb=it->second;
            const i128 nc=(i128(1)<<mb.steps)*i128(d)-i128(mb.C);
            if(nc%i128(mod)!=0){std::cerr<<"MACRO_BASE_DIV_FAIL\n";return 12;}
            mD=nc/i128(mod);
            mA=(i128(1)<<mb.steps)*i128(p3[c-mb.o]);
            have_base=true;
            break;
          }
        }

        int md=0,msteps=0;i128 qA=0,qD=0;
        if(have_base && macro_blocks_close(
              b,k,mA,mD,macro_depth,md,msteps,qA,qD)){
          ++macro;++total_macro;++macro_depth_hist[md];

          if(macro_controls<20000){
            for(uint64_t a:{1ULL,3ULL}){
              const u128 n=u128(a)*M+b;
              const u128 m=u128(a)*p3[c]+d;
              const i128 ps=i128(a)*qA+qD;
              if(ps<=0||u128(ps)>=n||
                 iterate(n,k)!=m||
                 iterate(u128(ps),mb.steps+msteps)!=m){
                std::cerr<<"MACRO_CONTROL_FAILED k="<<k
                         <<" b="<<b<<" depth="<<md<<"\n";
                return 13;
              }
              ++macro_controls;
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
             <<" macro="<<macro
             <<" live="<<next.size()
             <<" odd_live_fraction="<<frac<<"\n";
    cur.swap(next);
  }


  // The universal-family fixpoint above is intentionally stronger than what
  // bit-length induction needs.  For the shell [2^K,2^(K+1)), every number
  // has a=1.  Re-evaluate the exact residual at that concrete parameter.
  const u128 shellM=u128(1)<<K;
  uint64_t shell_direct=0,shell_base=0,shell_macro=0,shell_hard=0;
  uint64_t shell_controls=0;
  std::map<int,uint64_t> shell_depth_hist;

  for(const State&s:cur){
    const uint64_t b=s.b,dd=state_d(s);
    const int cc=state_c(s);
    const u128 n=shellM+b;
    const u128 m=u128(p3[cc])+dd;

    if(m<n){
      ++shell_direct;
      if(shell_controls<20000){
        if(iterate(n,K)!=m){std::cerr<<"SHELL_DIRECT_REPLAY_FAIL\n";return 30;}
        ++shell_controls;
      }
      continue;
    }

    bool matched=false;
    RevCert donor{};
    u128 pred=0;
    const int top=std::min(cc,max_o);
    uint64_t mod=1;
    for(int o=1;o<=top;++o){
      mod*=3;
      auto it=bank[o].find(dd%mod);
      if(it==bank[o].end())continue;
      donor=it->second;
      const u128 num=(u128(1)<<donor.steps)*m-donor.C;
      if(num%mod){std::cerr<<"SHELL_DONOR_DIV_FAIL\n";return 31;}
      pred=num/mod;
      matched=true;
      break;
    }

    if(!matched||pred==0){
      ++shell_hard;
      continue;
    }

    if(pred<n){
      ++shell_base;
      if(shell_controls<20000){
        if(iterate(pred,donor.steps)!=m){std::cerr<<"SHELL_BASE_REPLAY_FAIL\n";return 32;}
        ++shell_controls;
      }
      continue;
    }

    int blocks=0,extra_steps=0;u128 witness=0;
    if(shell_macro_depth>0 && shell_macro_close(
          pred,n,shell_macro_depth,blocks,extra_steps,witness)){
      ++shell_macro;
      ++shell_depth_hist[blocks];
      if(shell_controls<20000){
        if(iterate(witness,donor.steps+extra_steps)!=m){
          std::cerr<<"SHELL_MACRO_REPLAY_FAIL"
                   <<" b="<<b<<" blocks="<<blocks<<"\n";
          return 33;
        }
        ++shell_controls;
      }
      continue;
    }

    ++shell_hard;
  }

  std::cout<<"SHELL_BOUNDARY_RESULT"
           <<" K="<<K
           <<" shell_macro_depth="<<shell_macro_depth
           <<" universal_residual="<<cur.size()
           <<" shell_direct="<<shell_direct
           <<" shell_base="<<shell_base
           <<" shell_macro="<<shell_macro
           <<" shell_hard="<<shell_hard
           <<" controls="<<shell_controls<<"\n";
  for(const auto&[d,n]:shell_depth_hist)
    std::cout<<"SHELL_MACRO_DEPTH blocks="<<d<<" closed="<<n<<"\n";

  // Residual obstruction profile after the macro grammar is exhausted.
  int critical_c=0;
  while(p3[critical_c] <= (UINT64_C(1)<<K))++critical_c;

  std::map<int,uint64_t> c_hist,excess_hist,donor_o_hist,donor_steps_hist,rmax_hist;
  uint64_t no_base=0;
  for(const State&s:cur){
    const int cc=state_c(s);
    const uint64_t dd=state_d(s);
    ++c_hist[cc];
    ++excess_hist[cc-critical_c];

    bool found=false;
    const int top=std::min(cc,max_o);
    uint64_t mod=1;
    for(int o=1;o<=top;++o){
      mod*=3;
      auto it=bank[o].find(dd%mod);
      if(it==bank[o].end())continue;
      const RevCert& z=it->second;
      ++donor_o_hist[z.o];
      ++donor_steps_hist[z.steps];

      const i128 nc=(i128(1)<<z.steps)*i128(dd)-i128(z.C);
      if(nc%i128(mod)!=0){std::cerr<<"PROFILE_BASE_DIV_FAIL\n";return 14;}
      const i128 D=nc/i128(mod);
      const i128 A=(i128(1)<<z.steps)*i128(p3[cc-z.o]);
      const int rm=std::min(v3_i128(A,64),v3_i128(2*D+1,64));
      ++rmax_hist[rm];
      found=true;
      break;
    }
    if(!found)++no_base;
  }

  std::cout<<"MACRO_FRONTIER_PROFILE"
           <<" K="<<K
           <<" macro_depth="<<macro_depth
           <<" critical_c="<<critical_c
           <<" live="<<cur.size()
           <<" no_base="<<no_base<<"\n";
  for(const auto&[v,n]:excess_hist)
    std::cout<<"MACRO_FRONTIER_C_EXCESS excess="<<v<<" count="<<n<<"\n";
  for(const auto&[v,n]:donor_o_hist)
    std::cout<<"MACRO_FRONTIER_DONOR_O o="<<v<<" count="<<n<<"\n";
  for(const auto&[v,n]:donor_steps_hist)
    std::cout<<"MACRO_FRONTIER_DONOR_STEPS steps="<<v<<" count="<<n<<"\n";
  for(const auto&[v,n]:rmax_hist)
    std::cout<<"MACRO_FRONTIER_RMAX rmax="<<v<<" count="<<n<<"\n";

  std::cout<<"LIVE_RECURSIVE_DONE K="<<K
           <<" final_live="<<cur.size()
           <<" total_descent="<<total_descent
           <<" total_bridge="<<total_bridge
           <<" total_deep_o="<<total_deep_o
           <<" total_macro="<<total_macro
           <<" bridge_controls="<<bridge_controls
           <<" deep_o_controls="<<deep_o_controls
           <<" macro_controls="<<macro_controls<<"\n";
  for(int d=1;d<=macro_depth;++d)
    if(macro_depth_hist[d])
      std::cout<<"MACRO_DEPTH_HIST depth="<<d
               <<" closed="<<macro_depth_hist[d]<<"\n";
  std::cout<<"VERIFIED_SHELL_BOUNDARY_CLOSURE_SCOUT\n";
  return 0;
}
