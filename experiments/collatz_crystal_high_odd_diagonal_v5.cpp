#include <cstdint>
#include <iostream>
#include <limits>
#include <string>
#include <vector>
#include <algorithm>

using u64 = std::uint64_t;
using u128 = __uint128_t;

static u64 T(u64 x) {
  if (x & 1ULL) {
    u128 z=(u128)3*x+1;
    if (z>std::numeric_limits<u64>::max()) {
      std::cerr<<"overflow "<<x<<"\n"; std::abort();
    }
    return (u64)(z/2);
  }
  return x/2;
}

#include "collatz_qmin_4096.inc"

struct Rec {
  u64 n,entry_depth,entry_q,entry_y,exit_depth,exit_y;
};

int main(int argc,char**argv){
  u64 limit = argc>1 ? std::stoull(argv[1]) : (1ULL<<22);
  size_t H = argc>2 ? std::stoull(argv[2]) : 4096;
  if(H>4096){ std::cerr<<"H>4096 unsupported by pinned exact qmin table\\n"; return 2; }
  std::vector<Rec> recs;
  u64 crossed_before=0,desc_before=0,censored=0,max_delay=0;
  for(u64 n=3;n<limit;n+=2){
    u64 y=n,q=0;
    bool entered=false,closed=false;
    Rec r{n,0,0,0,0,0};
    for(size_t j=0;j<H;++j){
      if(j>0 && y<n){
        if(!entered) ++desc_before;
        else { r.exit_depth=j; r.exit_y=y; max_delay=std::max(max_delay,(u64)j-r.entry_depth); recs.push_back(r); }
        closed=true; break;
      }
      if(!entered && q>=n){
        // Prefix survival has been maintained because crossing stops below.
        entered=true; r.entry_depth=j; r.entry_q=q; r.entry_y=y;
      }
      bool odd=y&1ULL;
      if(odd) ++q;
      y=T(y);
      size_t jp=j+1;
      if(!entered && q < QMIN[jp]){
        ++crossed_before; closed=true; break;
      }
    }
    if(!closed){
      if(entered){
        // Continue solely to witness a later direct OrdinaryExit.
        for(size_t j=H;j<8*H;++j){
          if(y<n){ r.exit_depth=j; r.exit_y=y; max_delay=std::max(max_delay,(u64)j-r.entry_depth); recs.push_back(r); closed=true; break; }
          y=T(y);
        }
      }
      if(!closed) ++censored;
    }
  }

  std::cout<<"{\n";
  std::cout<<"  \"schema\":\"COLLATZ_CRYSTAL_HIGH_ODD_DIAGONAL_V5\",\n";
  std::cout<<"  \"limit\":"<<limit<<",\n";
  std::cout<<"  \"prefix_horizon\":"<<H<<",\n";
  std::cout<<"  \"high_odd_sources\":"<<recs.size()<<",\n";
  std::cout<<"  \"crossed_before_high_odd\":"<<crossed_before<<",\n";
  std::cout<<"  \"direct_descended_before_high_odd\":"<<desc_before<<",\n";
  std::cout<<"  \"censored\":"<<censored<<",\n";
  std::cout<<"  \"max_exit_delay\":"<<max_delay<<",\n";
  std::cout<<"  \"records\":[";
  for(size_t i=0;i<recs.size();++i){
    auto&r=recs[i]; if(i)std::cout<<",";
    std::cout<<"{\"n\":"<<r.n<<",\"entry_depth\":"<<r.entry_depth
             <<",\"entry_q\":"<<r.entry_q<<",\"entry_y\":"<<r.entry_y
             <<",\"exit_depth\":"<<r.exit_depth<<",\"exit_y\":"<<r.exit_y<<"}";
  }
  std::cout<<"],\n";
  std::cout<<"  \"candidate\":\"prefix-live q>=n domain collapses to a finite small-source exception set on the declared sweep\",\n";
  std::cout<<"  \"universal_status\":\"UNKNOWN\",\n";
  std::cout<<"  \"global_collatz\":\"UNKNOWN\"\n";
  std::cout<<"}\n";
}
