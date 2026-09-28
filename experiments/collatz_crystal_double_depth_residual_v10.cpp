#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <vector>

using u64 = std::uint64_t;
using u128 = __uint128_t;

static u64 T(u64 x) {
  if (x & 1ULL) {
    u128 z = (u128)3 * x + 1;
    assert(z <= std::numeric_limits<u64>::max());
    return (u64)(z / 2);
  }
  return x / 2;
}

struct Residual {
  u64 n=0, q=0, y=0, future_steps=0, future_x=0;
  const char* future_kind="";
};

int main(int argc,char**argv){
  const u64 limit = argc>1 ? std::stoull(argv[1]) : (1ULL<<26);
  const u64 safety_cap = argc>2 ? std::stoull(argv[2]) : 4096;
  u64 tested=0, closed_before=0, residuals=0, censored=0;
  u64 direct=0, splice=0, max_pre_steps=0, max_future=0;
  std::vector<Residual> first;

  for(u64 n=3;n<limit;n+=2){
    ++tested;
    u64 x=n, q=0, k=0;
    const u64 checkpoint=2*n;
    bool closed=false;
    while(k<=checkpoint && k<=safety_cap){
      if(x<n){ closed=true; ++direct; break; }
      if((x&7ULL)==5ULL && (u128)x <= (u128)4*n){
        closed=true; ++splice; break;
      }
      if(k==checkpoint) break;
      if(x&1ULL) ++q;
      x=T(x); ++k;
    }
    if(closed){
      ++closed_before;
      max_pre_steps=std::max(max_pre_steps,k);
      continue;
    }
    if(k<checkpoint){
      // The declared safety cap was reached before 2*n. This is not evidence.
      ++censored;
      if(first.size()<20) first.push_back({n,q,x,0,0,"CENSORED"});
      continue;
    }

    // Exact V9 source-level consequence: non-descent at 2*n forces q>=n.
    assert(k==checkpoint);
    assert(x>=n);
    assert(q>=n);
    ++residuals;

    u64 y=x, qq=q, extra=0;
    const char* kind="CENSORED_FUTURE";
    u64 hit=0;
    for(;extra<=safety_cap;++extra){
      if(y<n){ kind="DESCENT"; hit=y; break; }
      if((y&7ULL)==5ULL && (u128)y <= (u128)4*n){
        kind="QUARTER_SPLICE"; hit=y; break;
      }
      if(y&1ULL) ++qq;
      y=T(y);
    }
    if(extra>safety_cap){
      ++censored;
    } else {
      max_future=std::max(max_future,extra);
    }
    if(first.size()<100)
      first.push_back({n,q,x,extra,hit,kind});
  }

  std::cout<<"{\n";
  std::cout<<"  \"schema\":\"COLLATZ_CRYSTAL_DOUBLE_DEPTH_RESIDUAL_V10\",\n";
  std::cout<<"  \"limit\":"<<limit<<",\n";
  std::cout<<"  \"safety_cap\":"<<safety_cap<<",\n";
  std::cout<<"  \"tested_odd_sources\":"<<tested<<",\n";
  std::cout<<"  \"closed_before_or_at_2n\":"<<closed_before<<",\n";
  std::cout<<"  \"direct_descent_closures\":"<<direct<<",\n";
  std::cout<<"  \"quarter_splice_closures\":"<<splice<<",\n";
  std::cout<<"  \"double_depth_residuals\":"<<residuals<<",\n";
  std::cout<<"  \"censored\":"<<censored<<",\n";
  std::cout<<"  \"max_preclosure_depth\":"<<max_pre_steps<<",\n";
  std::cout<<"  \"max_future_steps_from_checkpoint\":"<<max_future<<",\n";
  std::cout<<"  \"residual_rows\":[";
  for(size_t i=0;i<first.size();++i){
    if(i) std::cout<<",";
    const auto&r=first[i];
    std::cout<<"{\"n\":"<<r.n<<",\"q_at_2n\":"<<r.q
             <<",\"y_at_2n\":"<<r.y<<",\"future_steps\":"<<r.future_steps
             <<",\"future_x\":"<<r.future_x<<",\"future_kind\":\""<<r.future_kind<<"\"}";
  }
  std::cout<<"],\n";
  std::cout<<"  \"candidate\":\"all no-direct-descent/no-quarter-splice prefixes at depth 2n collapse to a finite exceptional source family; each exception then quarter-splices\",\n";
  std::cout<<"  \"claim_boundary\":\"bounded exact falsifier for the Lean V10 checkpoint interface; lower-source merges are not needed for closure and would only shrink the residual\",\n";
  std::cout<<"  \"universal_status\":\"UNKNOWN\",\n";
  std::cout<<"  \"global_collatz\":\"UNKNOWN\"\n";
  std::cout<<"}\n";
  return 0;
}
