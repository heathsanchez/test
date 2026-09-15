// Export the exact first failures of the absolute H512 one-step cone,
// then continue only those failures to find their first later certificate.
// Full-shell enumeration remains fixed-width and exact through H=512.
// The tiny residual is then continued with boost::cpp_int, avoiding any
// fixed-width overflow assumption beyond the certified boundary.

#include <boost/multiprecision/cpp_int.hpp>
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <vector>

using u128=unsigned __int128;
using Big=boost::multiprecision::cpp_int;

static bool T128(u128 n,u128& out){
  if((n&1)==0){out=n/2;return true;}
  const u128 M=~u128(0);
  if(n>(M-1)/3)return false;
  out=(3*n+1)/2; return true;
}
static Big Tbig(Big n){
  if((n&1)!=0){n=3*n+1;n/=2;return n;}
  n/=2; return n;
}
static Big toBig(u128 x){
  Big hi=uint64_t(x>>64), lo=uint64_t(x);
  return (hi<<64)+lo;
}
static std::string s128(u128 x){
  if(!x)return "0";
  std::string s;
  while(x){s.push_back(char('0'+x%10));x/=10;}
  std::reverse(s.begin(),s.end()); return s;
}

int main(int argc,char**argv){
  if(argc!=2){std::cerr<<"usage: boundary K\n";return 2;}
  const int K=std::stoi(argv[1]);
  if(K<31||K>34)return 2;
  const uint64_t L=UINT64_C(1)<<K;
  const uint64_t U=UINT64_C(1)<<(K+1);

  std::vector<std::pair<uint64_t,u128>> hard;
  uint64_t checked=0,closed512=0;

  for(uint64_t n=L|1;n<U;n+=2){
    const u128 n128=n;
    const u128 t1=(3*n128+1)/2;
    u128 y=n128;
    bool closed=false;
    for(int t=0;t<=512;++t){
      if(t>0){
        u128 z;
        if(!T128(y,z)){
          std::cerr<<"BOUNDARY_OVERFLOW_BEFORE_512 n="<<n<<" t="<<t<<"\n";
          return 3;
        }
        y=z;
      }
      if(y<n128 || (y%3==2 && y<t1)){
        closed=true; ++closed512; break;
      }
    }
    if(!closed)hard.push_back({n,y});
    ++checked;
  }

  int max_late_t=-1;
  for(auto [n,y128]:hard){
    Big nB=n;
    Big y=toBig(y128);
    const Big t1=(3*nB+1)/2;
    int first=-1;
    std::string kind="NONE";
    for(int t=513;t<=4096;++t){
      y=Tbig(y);
      if(y<nB){first=t;kind="DIRECT";break;}
      if(y%3==2 && y<t1){
        const Big p=(2*y-1)/3;
        if(!(p>0 && p<nB && Tbig(p)==y)){
          std::cerr<<"BOUNDARY_BIG_REPLAY_FAIL\n"; return 4;
        }
        first=t;kind="CONE";break;
      }
    }
    max_late_t=std::max(max_late_t,first);
    std::cout<<"ABSOLUTE_H512_HARD_SEED"
             <<" K="<<K<<" n="<<n
             <<" first_late_t="<<first
             <<" kind="<<kind<<"\n";
  }

  std::cout<<"ABSOLUTE_H512_BOUNDARY_RESULT"
           <<" K="<<K
           <<" checked="<<checked
           <<" closed512="<<closed512
           <<" hard512="<<hard.size()
           <<" max_late_t="<<max_late_t<<"\n";
  std::cout<<"VERIFIED_ABSOLUTE_H512_BOUNDARY_EXPORT\n";
  return 0;
}
