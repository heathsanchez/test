// Remote falsification of the direct one-step Collatz cone.
// This is NOT proof. It samples exact arbitrary-precision odd integers at
// distant bit lengths and looks for a counterexample to the frozen rule:
//
//   exists f<=512 with y=T^(K+f)(n) satisfying
//     y<n
//   or
//     y == 2 (mod 3) and y<T(n).
//
// The second clause gives p=(2y-1)/3<n with T(p)=y.

#include <boost/multiprecision/cpp_int.hpp>
#include <cstdint>
#include <iostream>
#include <random>
#include <string>

using Big=boost::multiprecision::cpp_int;

static inline Big T(Big n){
  if((n&1)!=0){n=3*n+1;n/=2;return n;}
  n/=2;return n;
}

static Big make_sample(int K,uint64_t idx){
  std::mt19937_64 g(UINT64_C(0x9e3779b97f4a7c15) ^ (uint64_t(K)<<32) ^ idx);
  Big n=Big(1)<<K;
  int pos=0;
  while(pos<K){
    uint64_t w=g();
    const int take=std::min(64,K-pos);
    Big mask=(Big(1)<<take)-1;
    n |= (Big(w)&mask)<<pos;
    pos+=take;
  }
  n |= 1;
  return n;
}

int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: remote_cone K SAMPLES\n";return 2;}
  const int K=std::stoi(argv[1]);
  const uint64_t N=std::stoull(argv[2]);
  if(K<2||K>4096||N<1)return 2;

  uint64_t closed_direct=0,closed_cone=0,hard=0;
  int worst_f=-1;
  Big worst_n=0;

  for(uint64_t i=0;i<N;++i){
    Big n=make_sample(K,i);
    const Big t1=(3*n+1)/2;
    Big y=n;
    for(int j=0;j<K;++j)y=T(y);

    bool closed=false;
    for(int f=0;f<=512;++f){
      if(f>0)y=T(y);
      if(y<n){
        ++closed_direct;
        if(f>worst_f){worst_f=f;worst_n=n;}
        closed=true;break;
      }
      if(y%3==2 && y<t1){
        // Exact witness replay.
        const Big p=(2*y-1)/3;
        if(!(p>0 && p<n && T(p)==y)){
          std::cerr<<"REMOTE_CONE_REPLAY_FAIL K="<<K<<" sample="<<i<<"\n";
          return 3;
        }
        ++closed_cone;
        if(f>worst_f){worst_f=f;worst_n=n;}
        closed=true;break;
      }
    }
    if(!closed){
      ++hard;
      std::cout<<"REMOTE_CONE_COUNTEREXAMPLE_CANDIDATE"
               <<" K="<<K<<" sample="<<i
               <<" n="<<worst_n<<"\n";
      // Continue to count all failures rather than stop at first.
    }
  }

  std::cout<<"REMOTE_ONE_STEP_CONE_RESULT"
           <<" K="<<K<<" samples="<<N
           <<" direct="<<closed_direct
           <<" cone="<<closed_cone
           <<" hard="<<hard
           <<" worst_f="<<worst_f<<"\n";
  std::cout<<"REMOTE_ONE_STEP_CONE_FALSIFICATION_COMPLETE\n";
  return 0;
}
