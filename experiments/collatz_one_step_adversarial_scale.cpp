// Structured adversarial falsification / scaling study for the direct one-step cone.
//
// The random remote census can miss the all-odd-prefix edge n=2^(K+1)-1.
// This program tests exact near-upper-shell adversaries n=2^(K+1)-d for odd d,
// plus a few lower-edge controls, and measures the first forward context f
// at which
//   y=T^(K+f)(n) < n
// or
//   y == 2 (mod 3) and y < T(n).
//
// This is a scaling experiment, not a proof.

#include <boost/multiprecision/cpp_int.hpp>
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <vector>

using Big=boost::multiprecision::cpp_int;

static inline Big T(Big n){
  if((n&1)!=0){n=3*n+1;n/=2;return n;}
  n/=2;return n;
}

static int first_certificate(const Big& n,int K,int H){
  const Big t1=(3*n+1)/2;
  Big y=n;
  for(int j=0;j<K;++j)y=T(y);
  for(int f=0;f<=H;++f){
    if(f>0)y=T(y);
    if(y<n)return f;
    if(y%3==2 && y<t1){
      const Big p=(2*y-1)/3;
      if(!(p>0 && p<n && T(p)==y)){
        std::cerr<<"ADVERSARIAL_REPLAY_FAIL\n";
        std::exit(3);
      }
      return f;
    }
  }
  return -1;
}

int main(int argc,char**argv){
  if(argc!=2){std::cerr<<"usage: adversarial K\n";return 2;}
  const int K=std::stoi(argv[1]);
  const int H=std::max(512,8*K);
  if(K<2||K>4096)return 2;

  std::vector<Big> seeds;
  const Big top=Big(1)<<(K+1);
  const Big low=Big(1)<<K;
  for(int d=1;d<=63;d+=2)seeds.push_back(top-d);
  for(int d=1;d<=63;d+=2)seeds.push_back(low+d);

  int worst_f=-1,worst_index=-1;
  uint64_t failures=0;
  for(size_t i=0;i<seeds.size();++i){
    const int f=first_certificate(seeds[i],K,H);
    if(f<0){++failures;continue;}
    if(f>worst_f){worst_f=f;worst_index=int(i);}
  }

  int minimal_c=-1;
  if(failures==0){
    for(int c=0;c<=8;++c){
      const int budget=(c==0)?512:std::max(512,c*K);
      bool all=true;
      for(const Big& n:seeds){
        if(first_certificate(n,K,budget)<0){all=false;break;}
      }
      if(all){minimal_c=c;break;}
    }
  }

  std::cout<<"ADVERSARIAL_ONE_STEP_SCALE_RESULT"
           <<" K="<<K
           <<" seeds="<<seeds.size()
           <<" search_H="<<H
           <<" failures="<<failures
           <<" worst_f="<<worst_f
           <<" worst_index="<<worst_index
           <<" minimal_c="<<minimal_c
           <<" ratio="<<(worst_f<0?-1.0:double(worst_f)/double(K))
           <<"\n";
  std::cout<<"ADVERSARIAL_ONE_STEP_SCALE_COMPLETE\n";
  return 0;
}
