#include <algorithm>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <unordered_map>
#include <vector>

using u64=std::uint64_t;
using u128=__uint128_t;

static inline u64 T(u64 x){
  if(x&1ULL){
    u128 z=(u128)3*x+1;
    assert(z<=std::numeric_limits<u64>::max());
    return (u64)(z/2);
  }
  return x/2;
}

struct Entry{u64 source,q,k;};
struct Row{u64 x,q,k;};

int main(int argc,char**argv){
  if(argc!=2){std::cerr<<"usage: v23 certs.tsv\n";return 2;}
  std::ofstream out(argv[1]);
  out<<"n\tkind\ta\tqn\tp\tb\tqp\tx\n";

  const u64 limit=1ULL<<20;
  const u64 cap=4096;
  std::unordered_map<u64,Entry> owner;
  owner.reserve((size_t)limit*3);

  u64 tested=0,direct=0,splice=0,merge=0,residual=0,censored=0;
  for(u64 n=3;n<limit;n+=2){
    ++tested;
    u64 Q=(4*n)/3;
    u64 x=n,q=0,k=0;
    int kind=-1;
    std::vector<Row> path; path.reserve(256);
    Entry hit{0,0,0};

    while(k<=cap){
      if(x<n){kind=0;++direct;break;}
      if((x&7ULL)==5ULL && (u128)x<=(u128)4*n){kind=1;++splice;break;}
      auto it=owner.find(x);
      if(it!=owner.end() && it->second.source<n){
        kind=2;++merge;hit=it->second;break;
      }
      if(q==Q && (x&1ULL)){kind=3;++residual;break;}
      path.push_back({x,q,k});
      if(x&1ULL)++q;
      x=T(x);++k;
    }

    if(kind==-1){++censored;continue;}
    if(kind==0) out<<n<<"\tD\t"<<k<<"\t"<<q<<"\t0\t0\t0\t"<<x<<"\n";
    else if(kind==1) out<<n<<"\tS\t"<<k<<"\t"<<q<<"\t0\t0\t0\t"<<x<<"\n";
    else if(kind==2) out<<n<<"\tM\t"<<k<<"\t"<<q<<"\t"<<hit.source<<"\t"<<hit.k<<"\t"<<hit.q<<"\t"<<x<<"\n";
    else out<<n<<"\tR\t"<<k<<"\t"<<q<<"\t0\t0\t0\t"<<x<<"\n";

    if(kind<=2){
      for(const auto&s:path){
        if(owner.find(s.x)==owner.end()) owner.emplace(s.x,Entry{n,s.q,s.k});
      }
    }
  }

  assert(tested==524287 && censored==0);
  std::cout<<"SCHEMA COLLATZ_CRYSTAL_LIFT_STABLE_COVER_V23_EXTRACT\n";
  std::cout<<"TESTED "<<tested<<" DIRECT "<<direct<<" SPLICE "<<splice
           <<" MERGE "<<merge<<" RESIDUAL "<<residual<<" CENSORED "<<censored<<"\n";
  std::cout<<"GLOBAL_COLLATZ UNKNOWN\n";
  return 0;
}
