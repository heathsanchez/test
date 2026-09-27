#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

using u64=std::uint64_t;
using u128=__uint128_t;

static u64 T(u64 x){
  if(x&1ULL){
    u128 z=(u128)3*x+1;
    assert(z<=std::numeric_limits<u64>::max());
    return (u64)(z/2);
  }
  return x/2;
}

int main(int argc,char**argv){
  u64 limit=argc>1?std::stoull(argv[1]):(1ULL<<26);
  u64 cap=argc>2?std::stoull(argv[2]):4096;
  u64 tested=0,unresolved=0,record_steps=0,record_n=0,record_x=0,record_p=0;
  u64 decision_splice=0,decision_descent=0,decision_unresolved=0;
  u64 decision_record_steps=0,decision_record_n=0,max_band_returns=0,max_band_returns_n=0;
  std::vector<u64> first;
  for(u64 n=3;n<limit;n+=2){
    ++tested;
    u64 x=n;
    bool ok=false;
    bool decided=false, above=false;
    u64 band_returns=0;
    for(u64 j=0;j<=cap;++j){
      if(!decided && x<n){
        decided=true; ++decision_descent;
        if(j>decision_record_steps){decision_record_steps=j;decision_record_n=n;}
      }
      if(!decided && (x&7ULL)==5ULL && (u128)x <= (u128)4*n){
        decided=true; ++decision_splice;
        if(j>decision_record_steps){decision_record_steps=j;decision_record_n=n;}
      }
      if(above && (u128)x <= (u128)4*n){++band_returns;above=false;}
      if((u128)x > (u128)4*n) above=true;
      if((x&7ULL)==5ULL && (u128)x <= (u128)4*n){
        u64 p=(x-1)/4;
        assert(p>0 && p<n && (p&1ULL));
        u64 a=x;
        for(int t=0;t<3;++t)a=T(a);
        u64 b=T(p);
        assert(a==b);
        if(j>record_steps){record_steps=j;record_n=n;record_x=x;record_p=p;}
        ok=true;break;
      }
      x=T(x);
    }
    if(!decided) ++decision_unresolved;
    if(band_returns>max_band_returns){max_band_returns=band_returns;max_band_returns_n=n;}
    if(!ok){
      ++unresolved;
      if(first.size()<20)first.push_back(n);
    }
  }
  std::cout<<"{\n";
  std::cout<<"  \"schema\":\"COLLATZ_CRYSTAL_ODD_QUARTER_SPLICE_V6\",\n";
  std::cout<<"  \"limit\":"<<limit<<",\n";
  std::cout<<"  \"step_cap\":"<<cap<<",\n";
  std::cout<<"  \"tested_odd_sources\":"<<tested<<",\n";
  std::cout<<"  \"unresolved\":"<<unresolved<<",\n";
  std::cout<<"  \"record_steps\":"<<record_steps<<",\n";
  std::cout<<"  \"record_n\":"<<record_n<<",\n";
  std::cout<<"  \"record_x\":"<<record_x<<",\n";
  std::cout<<"  \"record_p\":"<<record_p<<",\n";
  std::cout<<"  \"decision_splice\":"<<decision_splice<<",\n";
  std::cout<<"  \"decision_descent\":"<<decision_descent<<",\n";
  std::cout<<"  \"decision_unresolved\":"<<decision_unresolved<<",\n";
  std::cout<<"  \"decision_record_steps\":"<<decision_record_steps<<",\n";
  std::cout<<"  \"decision_record_n\":"<<decision_record_n<<",\n";
  std::cout<<"  \"max_band_returns\":"<<max_band_returns<<",\n";
  std::cout<<"  \"max_band_returns_n\":"<<max_band_returns_n<<",\n";
  std::cout<<"  \"first_unresolved\":[";
  for(size_t i=0;i<first.size();++i){if(i)std::cout<<",";std::cout<<first[i];}
  std::cout<<"],\n";
  std::cout<<"  \"candidate\":\"every odd n>1 reaches x=5 mod8 with x<=4n; then p=(x-1)/4<n and T^3(x)=T(p)\",\n";
  std::cout<<"  \"fixed_origin_test\":\"before the quarter splice, classify the first source-order decision as direct descent or splice and count returns to the moving band [n,4n]\",\n";
  std::cout<<"  \"universal_status\":\"UNKNOWN\",\n";
  std::cout<<"  \"global_collatz\":\"UNKNOWN\"\n";
  std::cout<<"}\n";
}
