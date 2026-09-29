#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <map>
#include <unordered_map>
#include <vector>

using u64 = std::uint64_t;
using u128 = __uint128_t;

static inline u64 T(u64 x) {
  if (x & 1ULL) {
    u128 z=(u128)3*x+1;
    assert(z<=std::numeric_limits<u64>::max());
    return (u64)(z/2);
  }
  return x/2;
}

struct Entry { u64 source,q,k; };
struct Row { u64 x,q,k; };

int main() {
  const u64 limit=1ULL<<20;
  const u64 cap=4096;

  std::unordered_map<u64,Entry> owner;
  owner.reserve((size_t)limit*3);

  u64 tested=0,direct=0,splice=0,merge=0,residual=0,censored=0;
  u64 maxCloseK=0,maxMergeK=0,maxOwnerK=0;
  std::map<long long,u64> deltaDepth,deltaOdd;
  std::map<int,u64> classes;
  u64 maxRatioN=1,maxRatioP=0,maxRatioK=0,maxRatioB=0,maxRatioX=0;
  u64 minGap=std::numeric_limits<u64>::max(),minGapN=0,minGapP=0;
  std::vector<std::array<u64,7>> examples;

  for(u64 n=3;n<limit;n+=2){
    ++tested;
    u64 Q=(4*n)/3;
    u64 x=n,q=0,k=0;
    int kind=-1;
    std::vector<Row> path;
    path.reserve(256);

    while(k<=cap){
      if(x<n){kind=0;++direct;break;}
      if((x&7ULL)==5ULL && (u128)x<=(u128)4*n){kind=1;++splice;break;}

      auto it=owner.find(x);
      if(it!=owner.end() && it->second.source<n){
        kind=2;++merge;
        const Entry e=it->second;
        maxMergeK=std::max(maxMergeK,k);
        maxOwnerK=std::max(maxOwnerK,e.k);
        deltaDepth[(long long)k-(long long)e.k]++;
        deltaOdd[(long long)q-(long long)e.q]++;
        u64 gap=n-e.source;
        if(gap<minGap){minGap=gap;minGapN=n;minGapP=e.source;}
        if((u128)e.source*maxRatioN>(u128)maxRatioP*n){
          maxRatioP=e.source;maxRatioN=n;
          maxRatioK=k;maxRatioB=e.k;maxRatioX=x;
        }
        if(examples.size()<30) examples.push_back({n,e.source,k,e.k,q,e.q,x});
        break;
      }

      if(q==Q && (x&1ULL)){
        kind=3;++residual;
        if(examples.size()<30) examples.push_back({n,0,k,0,q,0,x});
        break;
      }

      path.push_back({x,q,k});
      if(x&1ULL) ++q;
      x=T(x); ++k;
    }

    if(kind==-1){++censored;continue;}
    if(kind<=2){
      maxCloseK=std::max(maxCloseK,k);
      classes[(int)(n%24)]++;
      // First closed source to own a state is the least source, because n rises.
      for(const auto &s:path){
        if(owner.find(s.x)==owner.end()) owner.emplace(s.x,Entry{n,s.q,s.k});
      }
    }
  }

  assert(tested==524287);
  assert(censored==0);

  std::vector<std::pair<u64,long long>> topD,topQ;
  for(auto [d,c]:deltaDepth) topD.push_back({c,d});
  for(auto [d,c]:deltaOdd) topQ.push_back({c,d});
  std::sort(topD.rbegin(),topD.rend());
  std::sort(topQ.rbegin(),topQ.rend());

  std::cout<<"{\n";
  std::cout<<"  \"schema\":\"COLLATZ_CRYSTAL_SOURCE_ORDER_CONSTRUCTOR_V22\",\n";
  std::cout<<"  \"limit\":"<<limit<<",\n";
  std::cout<<"  \"tested_odd_sources\":"<<tested<<",\n";
  std::cout<<"  \"direct\":"<<direct<<",\n";
  std::cout<<"  \"splice\":"<<splice<<",\n";
  std::cout<<"  \"lower_source_merge\":"<<merge<<",\n";
  std::cout<<"  \"constructor_free_boundary\":"<<residual<<",\n";
  std::cout<<"  \"censored\":"<<censored<<",\n";
  std::cout<<"  \"max_close_depth\":"<<maxCloseK<<",\n";
  std::cout<<"  \"max_merge_depth\":"<<maxMergeK<<",\n";
  std::cout<<"  \"max_smaller_source_depth\":"<<maxOwnerK<<",\n";
  std::cout<<"  \"closest_merge_source_ratio\":{\"p\":"<<maxRatioP<<",\"n\":"<<maxRatioN
           <<",\"n_depth\":"<<maxRatioK<<",\"p_depth\":"<<maxRatioB<<",\"common\":"<<maxRatioX<<"},\n";
  std::cout<<"  \"minimum_source_gap\":{\"gap\":"<<minGap<<",\"n\":"<<minGapN<<",\"p\":"<<minGapP<<"},\n";
  std::cout<<"  \"top_delta_depth\":[";
  for(size_t i=0;i<std::min<size_t>(20,topD.size());++i){if(i)std::cout<<",";std::cout<<"[\""<<topD[i].second<<"\","<<topD[i].first<<"]";}
  std::cout<<"],\n";
  std::cout<<"  \"top_delta_odd\":[";
  for(size_t i=0;i<std::min<size_t>(20,topQ.size());++i){if(i)std::cout<<",";std::cout<<"[\""<<topQ[i].second<<"\","<<topQ[i].first<<"]";}
  std::cout<<"],\n";
  std::cout<<"  \"examples\":[";
  for(size_t i=0;i<examples.size();++i){if(i)std::cout<<",";auto a=examples[i];
    std::cout<<"{\"n\":"<<a[0]<<",\"p\":"<<a[1]<<",\"a\":"<<a[2]<<",\"b\":"<<a[3]
             <<",\"qn\":"<<a[4]<<",\"qp\":"<<a[5]<<",\"x\":"<<a[6]<<"}";}
  std::cout<<"],\n";
  std::cout<<"  \"bounded_status\":\""<<(residual==0?"ZERO_RESIDUAL":"RESIDUAL")<<"\",\n";
  std::cout<<"  \"interpretation\":\"V20 weighted budget guard ablated; earlier lower-source collision alone is the exact OrdinaryExit constructor consumed by the V20 Lean shell\",\n";
  std::cout<<"  \"universal_status\":\"UNKNOWN\",\n";
  std::cout<<"  \"global_collatz\":\"UNKNOWN\"\n";
  std::cout<<"}\n";
  return 0;
}
