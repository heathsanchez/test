// Exact symbolic Collatz verifier on an UNBOUNDED affine tail.
//
// This removes the finite-shell upper endpoint from collatz_absolute_cone_dfs.
// Odd n=2a+1.  The t=0 inverse-odd cone closes a == 2 (mod 3).
// For a=3q+r, r in {0,1}, after one shortcut step:
//
//   n(q)=6q+(2r+1)
//   y(q)=9q+(3r+2).
//
// Here q ranges over [L, infinity), not a finite shell.
//
// An affine consequence A q+B < C q+D is uniform on [L,infinity) iff
//   A-C < 0 and it holds at q=L,
// or A-C == 0 and B-D < 0.
// Positive coefficient difference can never be certified uniformly at
// infinity and is split by q=2q'+e.
//
// Likewise the exact one-step inverse-odd cone
//   y == 2 (mod 3), p=(2y-1)/3 < n
// is certified on the entire infinite tail only when its affine difference
// has nonpositive slope and the lower endpoint passes.
//
// Therefore:
//   * CLOSED leaves are exact theorems for infinitely many integers;
//   * OPEN leaves are not counterexamples, only exact symbolic obstructions.
//
// If every branch closes at finite depth, then every odd n above the chosen
// lower bound has a lower strong-induction consequence. Combined with a
// finite base, that is an all-integers Collatz proof.
//
// No finite upper bound, sampling, floating point, or overflow-prone concrete
// trajectory arithmetic is used in the symbolic tree.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;

static constexpr u128 UMAX=~u128(0);
static constexpr u128 I128MAX=(u128(1)<<127)-1;

[[noreturn]] static void fail(const char* what){
  std::cerr<<"INFINITE_TAIL_RANGE_FAIL "<<what<<"\n";
  std::exit(9);
}
static u128 addc(u128 a,u128 b,const char* w){
  if(a>UMAX-b)fail(w); return a+b;
}
static u128 mulc(u128 a,u128 b,const char* w){
  if(a && b>UMAX/a)fail(w); return a*b;
}
static i128 si(u128 x,const char* w){
  if(x>I128MAX)fail(w); return i128(x);
}

struct State{
  u128 Nc,Nd,Yc,Yd;
  uint64_t L;
  std::string bits;
};

struct Stats{
  uint64_t nodes=0;
  uint64_t closed=0;
  uint64_t open=0;
  uint64_t direct_closed=0;
  uint64_t cone_closed=0;
  int max_depth=0;
  std::vector<State> frontier;
};

static uint64_t child_lower(uint64_t L,int e){
  // q_old = 2 q_new + e >= L.
  if(L<=uint64_t(e))return 0;
  return (L-uint64_t(e)+1)/2;
}

static bool tail_lt(
    u128 Ac,u128 Ad,u128 Bc,u128 Bd,uint64_t L){
  const i128 coef=si(Ac,"lt_Ac")-si(Bc,"lt_Bc");
  const i128 cons=si(Ad,"lt_Ad")-si(Bd,"lt_Bd");
  if(coef>0)return false;
  if(coef==0)return cons<0;
  return coef*i128(L)+cons<0;
}

static bool tail_cone(const State&s){
  // Need y == 2 mod 3 uniformly. Since Yc is always a multiple of 3 after
  // the a=3q+r normalization, Yd decides the residue.
  if(s.Yc%3!=0)fail("cone_nonuniform_mod3");
  if(s.Yd%3!=2)return false;

  // p=(2y-1)/3 < n  <=>  2y-1 < 3n.
  const i128 coef=2*si(s.Yc,"cone_Yc")-3*si(s.Nc,"cone_Nc");
  const i128 cons=2*si(s.Yd,"cone_Yd")-3*si(s.Nd,"cone_Nd")-1;
  if(coef>0)return false;
  if(coef==0)return cons<0;
  return coef*i128(s.L)+cons<0;
}

static std::string s128(u128 x){
  if(!x)return "0";
  std::string s;
  while(x){s.push_back(char('0'+x%10));x/=10;}
  std::reverse(s.begin(),s.end());
  return s;
}

static void dfs(const State&s,int t,int H,Stats&st){
  ++st.nodes;
  st.max_depth=std::max(st.max_depth,t);

  if(tail_lt(s.Yc,s.Yd,s.Nc,s.Nd,s.L)){
    ++st.closed;++st.direct_closed;return;
  }
  if(tail_cone(s)){
    ++st.closed;++st.cone_closed;return;
  }

  if(t==H){
    ++st.open;
    st.frontier.push_back(s);
    return;
  }

  for(int e=0;e<2;++e){
    State z;
    z.L=child_lower(s.L,e);
    z.bits=s.bits+char('0'+e);

    z.Nc=mulc(2,s.Nc,"child_Nc");
    z.Nd=addc(s.Nd,mulc(u128(e),s.Nc,"child_Nd_mul"),"child_Nd");

    const u128 rawYc=mulc(2,s.Yc,"raw_Yc");
    const u128 rawYd=addc(s.Yd,mulc(u128(e),s.Yc,"raw_Yd_mul"),"raw_Yd");
    if(rawYd&1){
      z.Yc=mulc(3,rawYc,"odd_Yc")/2;
      z.Yd=addc(mulc(3,rawYd,"odd_Yd_mul"),1,"odd_Yd_add")/2;
    }else{
      z.Yc=rawYc/2;
      z.Yd=rawYd/2;
    }
    dfs(z,t+1,H,st);
  }
}

int main(int argc,char**argv){
  if(argc!=4){
    std::cerr<<"usage: infinite_tail MIN_N H FRONTIER_OUT\n";
    return 2;
  }
  const uint64_t MIN_N=std::stoull(argv[1]);
  const int H=std::stoi(argv[2]);
  const std::string outpath=argv[3];
  if(MIN_N<3||H<1||H>70)return 2;

  // We only need odd n>=MIN_N.  Write n=2a+1.
  const uint64_t oddMin=(MIN_N&1)?MIN_N:MIN_N+1;
  const uint64_t aMin=(oddMin-1)/2;

  Stats st;

  // a == 2 mod 3 closes at t=0 by y=n and p=(2n-1)/3<n.
  // Remaining r=0,1 are a=3q+r.
  for(int r:{0,1}){
    uint64_t qL=0;
    if(aMin>uint64_t(r))
      qL=(aMin-uint64_t(r)+2)/3;

    State s{6,u128(2*r+1),9,u128(3*r+2),qL,std::string(1,char('0'+r))};
    dfs(s,1,H,st);
  }

  std::ofstream out(outpath);
  if(!out){std::cerr<<"FRONTIER_OPEN_FAIL\n";return 3;}
  for(const State&s:st.frontier){
    const i128 slopeNum=si(s.Yc,"out_Yc")-si(s.Nc,"out_Nc");
    const i128 coneSlope=2*si(s.Yc,"out_cY")-3*si(s.Nc,"out_cN");
    out<<"OPEN"
       <<" bits="<<s.bits
       <<" depth="<<s.bits.size()
       <<" L="<<s.L
       <<" Nc="<<s128(s.Nc)
       <<" Nd="<<s128(s.Nd)
       <<" Yc="<<s128(s.Yc)
       <<" Yd="<<s128(s.Yd)
       <<" y_minus_n_slope=";
    if(slopeNum<0)out<<"-"<<s128(u128(-slopeNum));else out<<s128(u128(slopeNum));
    out<<" cone_slope=";
    if(coneSlope<0)out<<"-"<<s128(u128(-coneSlope));else out<<s128(u128(coneSlope));
    out<<" ymod3="<<uint64_t(s.Yd%3)
       <<"\n";
  }
  out.close();

  std::cout<<"INFINITE_TAIL_RESULT"
           <<" min_n="<<MIN_N
           <<" H="<<H
           <<" nodes="<<st.nodes
           <<" closed_leaves="<<st.closed
           <<" direct_closed="<<st.direct_closed
           <<" cone_closed="<<st.cone_closed
           <<" open_leaves="<<st.open
           <<" max_depth="<<st.max_depth<<"\n";

  if(st.open==0)
    std::cout<<"ALL_INFINITE_TAIL_BRANCHES_CLOSED\n";
  else
    std::cout<<"INFINITE_TAIL_SYMBOLIC_OBSTRUCTION_REMAINS\n";
  std::cout<<"VERIFIED_INFINITE_TAIL_SYMBOLIC_QUOTIENT\n";
  return 0;
}
