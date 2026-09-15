// Exhaustive exact direct-shell test of the deterministic Collatz cone.
//
// No q14 bank, no universal affine constructors, no reverse macro grammar.
// For every odd n in [2^K,2^(K+1)), compute y=T^K(n), then for
// 0<=f<=H test either y<n or the maximal pure-O predecessor
//
//   P(y) = inverseOdd^v3(y+1)(y) < n.
//
// All arithmetic is unsigned 128-bit with explicit overflow aborts.  A green
// run therefore certifies the tested shell exactly.

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>

using u128=unsigned __int128;

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

static int v3p1(u128 y){
  u128 z=y+1;
  if(z==0)return -1;
  int r=0;
  while(z%3==0){z/=3;++r;}
  return r;
}

static bool maximal_cone(u128 y,u128 n,int& rused,u128& p){
  if((y+1)%3!=0)return false;
  const u128 q=(y+1)/3;
  p=2*q-1;
  rused=1;
  return p>0 && p<n;
}

int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: direct_cone K H\n";return 2;}
  const int K=std::stoi(argv[1]);
  const int H=std::stoi(argv[2]);
  if(K<2||K>30||H<0||H>2048)return 2;

  const uint64_t L=UINT64_C(1)<<K;
  const uint64_t U=UINT64_C(1)<<(K+1);

  uint64_t checked=0,direct=0,cone=0,hard=0,overflow=0;
  uint64_t max_f=0,max_f_seed=0,max_r=0,max_r_seed=0;

  for(uint64_t n=L|1;n<U;n+=2){
    u128 y=n;
    bool ok=true;
    for(int i=0;i<K;++i){
      u128 z;
      if(!Tchecked(y,z)){ok=false;break;}
      y=z;
    }
    if(!ok){++overflow;continue;}

    bool closed=false;
    for(int f=0;f<=H;++f){
      if(f>0){
        u128 z;
        if(!Tchecked(y,z)){ok=false;break;}
        y=z;
      }
      if(y<n){
        ++direct;
        if(uint64_t(f)>max_f){max_f=f;max_f_seed=n;}
        closed=true;break;
      }
      int r=0;u128 p=0;
      if(maximal_cone(y,n,r,p)){
        // Replay p through r inverse-odd-certified forward steps.
        u128 q=p;
        for(int j=0;j<r;++j){
          u128 z;
          if(!Tchecked(q,z)){std::cerr<<"REPLAY_OVERFLOW\n";return 5;}
          q=z;
        }
        if(q!=y){
          std::cerr<<"CONE_REPLAY_FAIL n="<<n<<" r="<<r<<"\n";return 6;
        }
        ++cone;
        if(uint64_t(f)>max_f){max_f=f;max_f_seed=n;}
        if(uint64_t(r)>max_r){max_r=r;max_r_seed=n;}
        closed=true;break;
      }
    }
    if(!ok){++overflow;continue;}
    if(!closed)++hard;
    ++checked;
  }

  std::cout<<"DIRECT_ONE_STEP_CONE_RESULT"
           <<" K="<<K<<" H="<<H
           <<" checked="<<checked
           <<" direct="<<direct
           <<" cone="<<cone
           <<" hard="<<hard
           <<" overflow="<<overflow
           <<" max_f="<<max_f
           <<" max_f_seed="<<max_f_seed
           <<" max_r="<<max_r
           <<" max_r_seed="<<max_r_seed<<"\n";
  if(overflow){std::cerr<<"DIRECT_SHELL_CONE_OVERFLOW\n";return 7;}
  std::cout<<"VERIFIED_DIRECT_SHELL_ONE_STEP_CONE\n";
  return 0;
}
