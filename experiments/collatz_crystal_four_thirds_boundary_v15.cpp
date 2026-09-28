#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <vector>
using u64=std::uint64_t;
using u128=__uint128_t;

static inline u128 T(u128 x){return (x&1)?(3*x+1)/2:x/2;}
static std::string s128(u128 x){if(!x)return"0";std::string s;while(x){s.push_back(char('0'+x%10));x/=10;}std::reverse(s.begin(),s.end());return s;}

struct Row{u64 n,Q,k,q,evens;u128 x,core;int cls;const char* kind;};

int main(int argc,char**argv){
  const u64 limit=argc>1?std::stoull(argv[1]):(1ULL<<26);
  const u64 cap=argc>2?std::stoull(argv[2]):4096;
  u64 tested=0,direct=0,splice=0,censored=0;
  u64 entrants=0,cls0=0,cls1=0,cls2=0;
  u64 core_descent=0,core_splice=0,core_nonexit=0;
  u64 boundary_violation=0;
  u64 max_wait=0; Row record{};
  std::vector<Row> first;
  for(u64 n=3;n<limit;n+=2){
    ++tested;
    const u64 Q=(4*n)/3;
    u128 x=n;u64 q=0,k=0;
    bool closed=false,seen=false;
    while(k<=cap){
      if(x<n){++direct;closed=true;break;}
      if((x&7)==5 && x<=(u128)4*n){++splice;closed=true;break;}
      if(q>Q){++boundary_violation;break;}
      if(!seen && q==Q){
        seen=true;++entrants;
        int cls=int(n%3); if(cls==0)++cls0; else if(cls==1)++cls1; else ++cls2;
        u128 core=x;u64 e=0;
        while((core&1)==0){core>>=1;++e;}
        const char* kind="NONEXIT";
        if(core<n){kind="DESCENT";++core_descent;}
        else if((core&7)==5 && core<=(u128)4*n){kind="QUARTER_SPLICE";++core_splice;}
        else ++core_nonexit;
        Row r{n,Q,k,q,e,x,core,cls,kind};
        if(first.size()<100)first.push_back(r);
        if(e>max_wait){max_wait=e;record=r;}
      }
      if(x&1)++q;
      x=T(x);++k;
    }
    if(!closed && k>cap)++censored;
  }
  std::cout<<"{\n";
  std::cout<<"  \"schema\":\"COLLATZ_CRYSTAL_FOUR_THIRDS_BOUNDARY_V15\",\n";
  std::cout<<"  \"limit\":"<<limit<<",\"cap\":"<<cap<<",\n";
  std::cout<<"  \"tested\":"<<tested<<",\"direct\":"<<direct<<",\"splice\":"<<splice<<",\"censored\":"<<censored<<",\n";
  std::cout<<"  \"boundary_entrants\":"<<entrants<<",\"class0\":"<<cls0<<",\"class1\":"<<cls1<<",\"class2\":"<<cls2<<",\n";
  std::cout<<"  \"odd_core_descent\":"<<core_descent<<",\"odd_core_splice\":"<<core_splice<<",\"odd_core_nonexit\":"<<core_nonexit<<",\n";
  std::cout<<"  \"boundary_violation\":"<<boundary_violation<<",\"max_forced_even_tail\":"<<max_wait<<",\n";
  std::cout<<"  \"record\":{\"n\":"<<record.n<<",\"Q\":"<<record.Q<<",\"k\":"<<record.k<<",\"x\":\""<<s128(record.x)<<"\",\"evens\":"<<record.evens<<",\"core\":\""<<s128(record.core)<<"\"},\n";
  std::cout<<"  \"first\":[";
  for(size_t i=0;i<first.size();++i){if(i)std::cout<<",";auto&r=first[i];
    std::cout<<"{\"n\":"<<r.n<<",\"class\":"<<r.cls<<",\"Q\":"<<r.Q<<",\"k\":"<<r.k<<",\"q\":"<<r.q
      <<",\"x\":\""<<s128(r.x)<<"\",\"evens\":"<<r.evens<<",\"core\":\""<<s128(r.core)<<"\",\"kind\":\""<<r.kind<<"\"}";}
  std::cout<<"],\n";
  std::cout<<"  \"candidate\":\"at first q=floor(4n/3) admission before direct/splice exit, the forced-even odd core is itself a direct descent or source-relative quarter splice\",\n";
  std::cout<<"  \"claim_boundary\":\"bounded exact falsifier only; class2 is independently impossible for minimal bad sources by Lean inverse-odd source elimination\",\n";
  std::cout<<"  \"universal_status\":\"UNKNOWN\",\"global_collatz\":\"UNKNOWN\"\n}\n";
}
