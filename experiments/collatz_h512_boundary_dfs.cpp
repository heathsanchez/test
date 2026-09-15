// Depth-first exact symbolic verifier for the Collatz one-step cone.
//
// This is the memory-scalable form of collatz_absolute_cone_symbolic.cpp.
// It certifies a contiguous shard of one odd bit-length shell without ever
// materializing the breadth frontier.
//
// Odd n = 2a+1.  A symbolic state represents
//
//   n(q)=Nc*q+Nd,
//   y(q)=T^t(n(q))=Yc*q+Yd,
//   q in [L,U].
//
// If direct descent or the one-step inverse-odd consequence is uniform on the
// interval, the entire family closes at once. Otherwise split q by parity and
// recurse. Singleton leaves are replayed with arbitrary-precision integers.
//
// Exactness is independent of shard count. Sharding only divides CPU work.

#include <boost/multiprecision/cpp_int.hpp>
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <limits>
#include <string>

using u128=unsigned __int128;
using i128=__int128;
using Big=boost::multiprecision::cpp_int;

struct State{
  u128 Nc,Nd,Yc,Yd;
  uint64_t L,U;
};

struct Stats{
  u128 represented=0;
  u128 uniform_closed=0;
  u128 early_singleton_closed=0;
  u128 boundary=0;
  u128 unresolved_after_rescue=0;
  uint64_t nodes=0;
  uint64_t uniform_nodes=0;
  uint64_t singleton_nodes=0;
  int max_depth=0;
  int max_late_t=0;
  uint64_t max_late_seed=0;
};

static inline Big Tbig(Big n){
  if((n&1)!=0){n=3*n+1;n/=2;return n;}
  n/=2;return n;
}

static uint64_t ceil_div2_shift(uint64_t L,int e){
  if(L<=uint64_t(e))return 0;
  return (L-uint64_t(e)+1)/2;
}

static bool uniform_lt(
    u128 Ac,u128 Ad,u128 Bc,u128 Bd,
    uint64_t L,uint64_t U){
  const i128 coef=i128(Ac)-i128(Bc);
  const i128 cons=i128(Ad)-i128(Bd);
  const i128 q=coef>=0?i128(U):i128(L);
  return coef*q+cons<0;
}

static bool uniform_cone(const State&s){
  if(s.Yc%3!=0){
    std::cerr<<"NONUNIFORM_MOD3_STATE\n";
    std::exit(5);
  }
  if(s.Yd%3!=2)return false;
  const i128 coef=2*i128(s.Yc)-3*i128(s.Nc);
  const i128 cons=2*i128(s.Yd)-3*i128(s.Nd)-1;
  const i128 q=coef>=0?i128(s.U):i128(s.L);
  return coef*q+cons<0;
}

struct CloseInfo{int t=-1; char kind='N';};

static CloseInfo exact_first_close(const Big& n,Big y,int t,int H){
  for(int j=t;j<=H;++j){
    if(y<n)return {j,'D'};
    if(y%3==2){
      Big p=(2*y-1)/3;
      if(p>0 && p<n){
        if(Tbig(p)!=y){
          std::cerr<<"SINGLETON_REPLAY_FAIL\n";
          std::exit(6);
        }
        return {j,'C'};
      }
    }
    if(j==H)break;
    y=Tbig(y);
  }
  return {-1,'N'};
}

static void dfs(const State&s,int t,int H,int rescueH,Stats&st,std::ofstream& out){
  ++st.nodes;
  st.max_depth=std::max(st.max_depth,t);
  const uint64_t mult=s.U-s.L+1;

  if(uniform_lt(s.Yc,s.Yd,s.Nc,s.Nd,s.L,s.U) || uniform_cone(s)){
    st.uniform_closed+=mult;
    ++st.uniform_nodes;
    return;
  }

  if(s.L==s.U){
    ++st.singleton_nodes;
    const u128 q=s.L;
    const u128 nu=s.Nc*q+s.Nd;
    const u128 yu=s.Yc*q+s.Yd;
    Big n=Big(uint64_t(nu>>64)); n<<=64; n+=uint64_t(nu);
    Big y=Big(uint64_t(yu>>64)); y<<=64; y+=uint64_t(yu);
    const CloseInfo ci=exact_first_close(n,y,t,rescueH);
    if(ci.t>=0 && ci.t<=H){
      ++st.early_singleton_closed;
    }else{
      ++st.boundary;
      if(ci.t<0){
        ++st.unresolved_after_rescue;
        out<<uint64_t(nu)<<" -1 N\n";
      }else{
        out<<uint64_t(nu)<<" "<<ci.t<<" "<<ci.kind<<"\n";
        if(ci.t>st.max_late_t){
          st.max_late_t=ci.t;
          st.max_late_seed=uint64_t(nu);
        }
      }
    }
    return;
  }

  if(t==H){
    std::cerr<<"BOUNDARY_NON_SINGLETON_AT_H mult="<<mult<<"\n";
    std::exit(8);
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
    dfs(z,t+1,H,rescueH,st,out);
  }
}

static uint64_t count_mod3(uint64_t L,uint64_t U,int r){
  if(L>U)return 0;
  auto upto=[&](uint64_t x)->uint64_t{
    if(x<uint64_t(r))return 0;
    return (x-uint64_t(r))/3+1;
  };
  return upto(U)-(L?upto(L-1):0);
}

static std::string s128(u128 x){
  if(!x)return "0";
  std::string s;
  while(x){s.push_back(char('0'+x%10));x/=10;}
  std::reverse(s.begin(),s.end());
  return s;
}

int main(int argc,char**argv){
  if(argc!=6){
    std::cerr<<"usage: boundary_dfs K SHARD_ID SHARDS RESCUE_H OUT\n";
    return 2;
  }
  const int K=std::stoi(argv[1]);
  const int H=512;
  const uint64_t SID=std::stoull(argv[2]);
  const uint64_t SHARDS=std::stoull(argv[3]);
  const int rescueH=std::stoi(argv[4]);
  const std::string outpath=argv[5];
  if(K<2||K>40||rescueH<=H||rescueH>4096||SHARDS<1||SID>=SHARDS)return 2;
  std::ofstream out(outpath);
  if(!out){std::cerr<<"BOUNDARY_OUT_OPEN_FAIL\n";return 2;}

  const uint64_t aGlobalL=UINT64_C(1)<<(K-1);
  const uint64_t total=UINT64_C(1)<<(K-1);
  const uint64_t offL=(u128(total)*SID)/SHARDS;
  const uint64_t offU=(u128(total)*(SID+1))/SHARDS;
  const uint64_t aL=aGlobalL+offL;
  const uint64_t aU=aGlobalL+offU-1;
  if(aL>aU)return 2;

  Stats st;
  st.represented=aU-aL+1;

  const uint64_t closed_t0=count_mod3(aL,aU,2);
  st.uniform_closed+=closed_t0;

  for(int r:{0,1}){
    const uint64_t qL=(aL<=uint64_t(r))?0:(aL-uint64_t(r)+2)/3;
    if(aU<uint64_t(r))continue;
    const uint64_t qU=(aU-uint64_t(r))/3;
    if(qL>qU)continue;

    State s{6,u128(2*r+1),9,u128(3*r+2),qL,qU};
    dfs(s,1,H,rescueH,st,out);
  }

  out.close();
  const u128 early=st.uniform_closed+st.early_singleton_closed;
  const u128 boundary=st.boundary;

  std::cout<<"H512_BOUNDARY_DFS_RESULT"
           <<" K="<<K
           <<" H="<<H
           <<" rescueH="<<rescueH
           <<" shard="<<SID
           <<" shards="<<SHARDS
           <<" represented="<<s128(st.represented)
           <<" early_closed="<<s128(early)
           <<" boundary="<<s128(boundary)
           <<" unresolved_after_rescue="<<s128(st.unresolved_after_rescue)
           <<" nodes="<<st.nodes
           <<" max_depth="<<st.max_depth
           <<" max_late_t="<<st.max_late_t
           <<" max_late_seed="<<st.max_late_seed<<"\n";

  if(early+boundary!=st.represented){
    std::cerr<<"H512_BOUNDARY_ACCOUNTING_FAIL\n";
    return 7;
  }
  std::cout<<"VERIFIED_H512_SYMBOLIC_BOUNDARY_SHARD\n";
  return 0;
}
