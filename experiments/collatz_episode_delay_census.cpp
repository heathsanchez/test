// Exact high-throughput census of non-descending odd episodes.
//
// For odd x>1 write x=2^r m-1 with m odd. One complete odd episode is:
//
//   z = 3^r m - 1
//   s = v2(z)
//   x' = z / 2^s
//   r' = v2(x'+1)
//   m' = (x'+1)/2^r'
//
// We iterate complete odd episodes until x'<x0, where x0 is the original
// odd integer.  This is deliberately weaker than checking every shortcut
// intermediate; a green descent certificate is therefore sound.
//
// The purpose is to measure how the maximum non-descending episode count
// scales with 2-adic residue precision P.  If recurrence is governed by a
// divisibility countdown, max delay should grow with required precision,
// not with the exponentially growing number of residues.
//
// Exact unsigned-128 arithmetic is sufficient for the bounded parameter
// ranges admitted below; every multiplication is overflow-checked.

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <queue>
#include <string>
#include <vector>

using u128 = unsigned __int128;

static std::string s128(u128 x){
  if(!x) return "0";
  std::string s;
  while(x){ s.push_back(char('0'+x%10)); x/=10; }
  std::reverse(s.begin(),s.end());
  return s;
}

static int v2u(u128 x){
  if(!x){ std::cerr<<"V2_ZERO\n"; std::exit(3); }
  int r=0;
  while((x&1)==0){ x>>=1; ++r; }
  return r;
}

static bool mul_checked(u128 a,u128 b,u128& out){
  const u128 M=~u128(0);
  if(a && b>M/a) return false;
  out=a*b; return true;
}

struct Worst {
  uint32_t delay;
  int r0;
  uint64_t m0;
  u128 x0;
};

struct Better {
  bool operator()(const Worst&a,const Worst&b) const {
    if(a.delay!=b.delay) return a.delay>b.delay;
    if(a.r0!=b.r0) return a.r0>b.r0;
    return a.m0>b.m0;
  }
};

int main(int argc,char**argv){
  if(argc!=5){
    std::cerr<<"usage: episode_delay MAX_R PRECISION MAX_EPISODES TOP_N\n";
    return 2;
  }
  const int max_r=std::stoi(argv[1]);
  const int P=std::stoi(argv[2]);
  const int max_eps=std::stoi(argv[3]);
  const int top_n=std::stoi(argv[4]);
  if(max_r<1||max_r>28||P<8||P>26||max_eps<1||max_eps>10000||
     top_n<1||top_n>1000) return 2;

  std::vector<u128> p3(max_r+64,1);
  for(size_t i=1;i<p3.size();++i){
    if(!mul_checked(p3[i-1],u128(3),p3[i])){
      std::cerr<<"POW3_OVERFLOW\n"; return 4;
    }
  }

  const uint64_t M=UINT64_C(1)<<P;
  uint64_t cases=0,base_cases=0,closed=0,unresolved=0;
  uint32_t max_delay=0;
  int max_delay_r=0;
  uint64_t max_delay_m=0;
  u128 max_delay_x=0;

  std::vector<uint64_t> delay_hist(max_eps+1,0);
  std::priority_queue<Worst,std::vector<Worst>,Better> top;

  for(int r0=1;r0<=max_r;++r0){
    for(uint64_t m0=1;m0<M;m0+=2){
      ++cases;
      u128 x0=(u128(1)<<r0)*u128(m0)-1;
      if(x0==1){ ++base_cases; continue; }

      int r=r0;
      u128 m=m0;
      bool done=false;
      uint32_t d=0;

      for(int e=1;e<=max_eps;++e){
        if(r<1 || size_t(r)>=p3.size()){
          std::cerr<<"R_RANGE_EXCEEDED r="<<r<<"\n"; return 5;
        }
        u128 prod;
        if(!mul_checked(p3[r],m,prod) || prod==0){
          std::cerr<<"EPISODE_PRODUCT_OVERFLOW"
                   <<" r0="<<r0<<" m0="<<m0<<" e="<<e<<"\n";
          return 6;
        }
        const u128 z=prod-1;
        const int s=v2u(z);
        const u128 xp=z>>s;
        const int rp=v2u(xp+1);
        const u128 mp=(xp+1)>>rp;

        d=e;
        if(xp<x0){
          done=true;
          break;
        }
        r=rp;
        m=mp;
      }

      if(done){
        ++closed;
        if(d<=uint32_t(max_eps)) ++delay_hist[d];
        if(d>max_delay){
          max_delay=d; max_delay_r=r0; max_delay_m=m0; max_delay_x=x0;
        }
        Worst w{d,r0,m0,x0};
        if((int)top.size()<top_n) top.push(w);
        else {
          const Worst& q=top.top();
          if(w.delay>q.delay ||
             (w.delay==q.delay && (w.r0<q.r0 ||
               (w.r0==q.r0 && w.m0<q.m0)))){
            top.pop(); top.push(w);
          }
        }
      }else{
        ++unresolved;
        if(unresolved<=32)
          std::cout<<"EPISODE_DELAY_UNRESOLVED"
                   <<" r="<<r0<<" m="<<m0<<" x="<<s128(x0)<<"\n";
      }
    }
  }

  std::vector<Worst> rows;
  while(!top.empty()){ rows.push_back(top.top()); top.pop(); }
  std::sort(rows.begin(),rows.end(),[](const Worst&a,const Worst&b){
    if(a.delay!=b.delay) return a.delay>b.delay;
    if(a.r0!=b.r0) return a.r0<b.r0;
    return a.m0<b.m0;
  });

  std::cout<<"EPISODE_DELAY_CENSUS"
           <<" max_r="<<max_r
           <<" precision="<<P
           <<" cases="<<cases
           <<" base_cases="<<base_cases
           <<" closed="<<closed
           <<" unresolved="<<unresolved
           <<" max_delay="<<max_delay
           <<" max_delay_r="<<max_delay_r
           <<" max_delay_m="<<max_delay_m
           <<" max_delay_x="<<s128(max_delay_x)
           <<" delay_per_precision="<<(double(max_delay)/double(P))
           <<"\n";

  for(size_t i=0;i<rows.size();++i)
    std::cout<<"EPISODE_DELAY_WORST"
             <<" rank="<<(i+1)
             <<" delay="<<rows[i].delay
             <<" r="<<rows[i].r0
             <<" m="<<rows[i].m0
             <<" x="<<s128(rows[i].x0)<<"\n";

  if(unresolved==0)
    std::cout<<"ALL_NONBASE_CASES_DESCEND_WITHIN_EPISODE_CAP\n";
  std::cout<<"VERIFIED_EXACT_EPISODE_DELAY_CENSUS\n";
  return 0;
}
