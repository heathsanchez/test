// Symbolic compiler for the absolute one-step Collatz cone.
//
// Odd shell n in [2^K,2^(K+1)) is parameterized after removing the t=0
// cone class n == 2 (mod 3).  Each live state stores exact affine forms
//
//   n(q) = Nc*q + Nd
//   y(q) = T^t(n(q)) = Yc*q + Yd
//
// for q in a contiguous integer interval [L,U].
//
// Since after the first odd shortcut step Yc is divisible by 3, y mod 3 is
// uniform on each state.  We close a whole state when either
//
//   y < n
//
// or
//
//   y == 2 (mod 3) and 2y < 3n+1
//
// holds for every q in [L,U].  Otherwise we split q by parity, apply one
// exact shortcut step algebraically, and retain only the unresolved children.
//
// When a state becomes singleton, the remaining horizon is replayed exactly
// on that concrete integer.  A state cap turns large runs into a diagnostic
// census rather than an unsound claim.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;

struct State{
  u128 Nc,Nd,Yc,Yd;
  uint64_t L,U;
};

static std::string s128(u128 x){
  if(!x)return "0";
  std::string s;
  while(x){s.push_back(char('0'+x%10));x/=10;}
  std::reverse(s.begin(),s.end());
  return s;
}

static bool Tchecked(u128 n,u128& out){
  if((n&1)==0){out=n/2;return true;}
  const u128 MAX=~u128(0);
  if(n>(MAX-1)/3)return false;
  out=(3*n+1)/2;
  return true;
}

static uint64_t ceil_div2_shift(uint64_t L,int e){
  if(L<=uint64_t(e))return 0;
  return (L-uint64_t(e)+1)/2;
}

static bool uniform_lt(
    u128 Ac,u128 Ad,u128 Bc,u128 Bd,
    uint64_t L,uint64_t U){
  // Test A(q) < B(q) for every integer q in [L,U].
  const i128 coef=i128(Ac)-i128(Bc);
  const i128 cons=i128(Ad)-i128(Bd);
  const i128 q = coef>=0 ? i128(U) : i128(L);
  return coef*q+cons < 0;
}

static bool uniform_cone(const State&s){
  if(s.Yc%3!=0){
    std::cerr<<"NONUNIFORM_MOD3_STATE\n";
    std::exit(5);
  }
  if(s.Yd%3!=2)return false;

  // 2y < 3n+1  <=>  (2Yc-3Nc)q + (2Yd-3Nd-1) < 0.
  const i128 coef=2*i128(s.Yc)-3*i128(s.Nc);
  const i128 cons=2*i128(s.Yd)-3*i128(s.Nd)-1;
  const i128 q=coef>=0 ? i128(s.U) : i128(s.L);
  return coef*q+cons < 0;
}

static bool exact_closes(u128 n,u128 y,int t,int H){
  const u128 t1=(3*n+1)/2; // n is odd and small enough in supported shells.
  for(int j=t;j<=H;++j){
    if(y<n)return true;
    if(y%3==2 && y<t1){
      const u128 p=(2*y-1)/3;
      u128 z;
      if(!(p>0 && p<n && Tchecked(p,z) && z==y)){
        std::cerr<<"SINGLETON_CONE_REPLAY_FAIL\n";
        std::exit(6);
      }
      return true;
    }
    if(j==H)break;
    u128 z;
    if(!Tchecked(y,z)){
      std::cerr<<"SINGLETON_TRAJECTORY_OVERFLOW\n";
      std::exit(7);
    }
    y=z;
  }
  return false;
}

static uint64_t count_mod3(uint64_t L,uint64_t U,int r){
  if(L>U)return 0;
  auto upto=[&](uint64_t x)->uint64_t{
    // count 0<=a<=x with a mod3 == r
    if(x<uint64_t(r))return 0;
    return (x-uint64_t(r))/3+1;
  };
  return upto(U)-(L?upto(L-1):0);
}

int main(int argc,char**argv){
  if(argc!=4){
    std::cerr<<"usage: cone_symbolic K H STATE_CAP\n";
    return 2;
  }
  const int K=std::stoi(argv[1]);
  const int H=std::stoi(argv[2]);
  const uint64_t CAP=std::stoull(argv[3]);
  if(K<2||K>40||H<1||H>4096||CAP<1)return 2;

  // n=2a+1, a in [2^(K-1),2^K-1].
  const uint64_t aL=UINT64_C(1)<<(K-1);
  const uint64_t aU=(UINT64_C(1)<<K)-1;
  const uint64_t total=UINT64_C(1)<<(K-1);

  // t=0 cone immediately closes a==2 (mod3), since then n==2 (mod3)
  // and p=(2n-1)/3<n.
  const uint64_t closed_t0=count_mod3(aL,aU,2);

  std::vector<State> cur,next;
  cur.reserve(1024);

  // Remaining a = 3q+r, r=0 or1.
  for(int r:{0,1}){
    const uint64_t qL=(aL<=uint64_t(r))?0:(aL-uint64_t(r)+2)/3;
    if(aU<uint64_t(r))continue;
    const uint64_t qU=(aU-uint64_t(r))/3;
    if(qL>qU)continue;

    // n=2(3q+r)+1 = 6q+(2r+1)
    // T(n)=3(3q+r)+2 = 9q+(3r+2)
    cur.push_back({6,u128(2*r+1),9,u128(3*r+2),qL,qU});
  }

  uint64_t total_uniform_closed=closed_t0;
  uint64_t singleton_closed=0,singleton_hard=0;
  bool truncated=false;
  int last_t=1;

  for(int t=1;t<=H && !cur.empty();++t){
    last_t=t;
    uint64_t represented=0,uniform_closed=0,singletons=0;
    for(const State&s:cur)represented += s.U-s.L+1;

    next.clear();
    if(cur.size()<=CAP/2)next.reserve(cur.size()*2);

    for(const State&s:cur){
      const uint64_t mult=s.U-s.L+1;

      if(uniform_lt(s.Yc,s.Yd,s.Nc,s.Nd,s.L,s.U) || uniform_cone(s)){
        uniform_closed += mult;
        total_uniform_closed += mult;
        continue;
      }

      if(s.L==s.U){
        ++singletons;
        const u128 q=s.L;
        const u128 n=s.Nc*q+s.Nd;
        const u128 y=s.Yc*q+s.Yd;
        if(exact_closes(n,y,t,H))++singleton_closed;
        else ++singleton_hard;
        continue;
      }

      if(t==H){
        // unresolved non-singleton family; retain for diagnostic output.
        next.push_back(s);
        continue;
      }

      for(int e=0;e<2;++e){
        if(s.U<uint64_t(e))continue;
        const uint64_t L2=ceil_div2_shift(s.L,e);
        const uint64_t U2=(s.U-uint64_t(e))/2;
        if(L2>U2)continue;

        State z;
        z.L=L2;z.U=U2;
        z.Nc=2*s.Nc;
        z.Nd=s.Nd+u128(e)*s.Nc;

        const u128 rawYc=2*s.Yc;
        const u128 rawYd=s.Yd+u128(e)*s.Yc;
        if(rawYd&1){
          z.Yc=(3*rawYc)/2;
          z.Yd=(3*rawYd+1)/2;
        }else{
          z.Yc=rawYc/2;
          z.Yd=rawYd/2;
        }
        next.push_back(z);
      }

      if(next.size()>CAP){
        truncated=true;
        break;
      }
    }

    uint64_t next_repr=0;
    for(const State&s:next)next_repr += s.U-s.L+1;

    std::cout<<"CONE_SYMBOLIC_LEVEL"
             <<" K="<<K
             <<" t="<<t
             <<" states="<<cur.size()
             <<" represented="<<represented
             <<" uniform_closed="<<uniform_closed
             <<" singleton_states="<<singletons
             <<" next_states="<<next.size()
             <<" next_represented="<<next_repr
             <<" total_uniform_closed="<<total_uniform_closed
             <<" singleton_closed="<<singleton_closed
             <<" singleton_hard="<<singleton_hard
             <<" truncated="<<(truncated?1:0)<<"\n";

    if(truncated){
      cur.swap(next);
      break;
    }
    cur.swap(next);
  }

  uint64_t unresolved_repr=0;
  for(const State&s:cur)unresolved_repr += s.U-s.L+1;

  std::cout<<"CONE_SYMBOLIC_RESULT"
           <<" K="<<K
           <<" H="<<H
           <<" total_odd="<<total
           <<" closed_t0="<<closed_t0
           <<" uniform_closed="<<total_uniform_closed
           <<" singleton_closed="<<singleton_closed
           <<" singleton_hard="<<singleton_hard
           <<" frontier_states="<<cur.size()
           <<" frontier_represented="<<unresolved_repr
           <<" last_t="<<last_t
           <<" truncated="<<(truncated?1:0)<<"\n";

  if(!truncated && singleton_hard==0 && cur.empty()){
    std::cout<<"VERIFIED_SYMBOLIC_CONE_SHELL_CLOSED\n";
  }else{
    std::cout<<"SYMBOLIC_CONE_FRONTIER_RETAINED\n";
  }
  return 0;
}
