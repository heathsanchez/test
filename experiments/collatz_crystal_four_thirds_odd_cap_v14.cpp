#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <vector>

using u64 = std::uint64_t;
using u128 = __uint128_t;

static inline u128 T(u128 x) {
  return (x & 1) ? (3*x + 1)/2 : x/2;
}

static std::string s128(u128 x){
  if(!x) return "0";
  std::string s;
  while(x){ s.push_back(char('0' + x%10)); x/=10; }
  std::reverse(s.begin(),s.end());
  return s;
}

struct EqRow { u64 n,k,q; u128 x; };

int main(int argc,char**argv){
  const u64 limit = argc>1 ? std::stoull(argv[1]) : (1ULL<<26);
  const u64 step_cap = argc>2 ? std::stoull(argv[2]) : 4096;

  u64 tested=0, direct=0, splice=0, censored=0;
  u64 strict_viol_sources=0, strict_viol_states=0;
  u64 equality_sources=0, equality_states=0;
  std::vector<EqRow> first_eq, first_bad;
  u64 best_n=0,best_q=0,best_k=0; u128 best_x=0;

  for(u64 n=3;n<limit;n+=2){
    ++tested;
    u128 x=n;
    u64 q=0,k=0;
    bool eq_source=false,bad_source=false,closed=false;
    while(k<=step_cap){
      if(x < n){ ++direct; closed=true; break; }
      if((x & 7)==5 && x <= (u128)4*n){ ++splice; closed=true; break; }

      // q = oddCount(n,k) at the current state x=T^k(n).
      if((u128)3*q > (u128)4*n){
        ++strict_viol_states;
        if(!bad_source){ ++strict_viol_sources; bad_source=true; }
        if(first_bad.size()<20) first_bad.push_back({n,k,q,x});
      } else if((u128)3*q == (u128)4*n) {
        ++equality_states;
        if(!eq_source){ ++equality_sources; eq_source=true; }
        if(first_eq.size()<40) first_eq.push_back({n,k,q,x});
      }

      if((u128)q * best_n > (u128)best_q * n || best_n==0){
        best_n=n; best_q=q; best_k=k; best_x=x;
      }

      if(x & 1) ++q;
      x=T(x); ++k;
    }
    if(!closed && k>step_cap) ++censored;
  }

  std::cout<<"{\n";
  std::cout<<"  \"schema\":\"COLLATZ_CRYSTAL_FOUR_THIRDS_ODD_CAP_V14\",\n";
  std::cout<<"  \"limit\":"<<limit<<",\n";
  std::cout<<"  \"step_cap\":"<<step_cap<<",\n";
  std::cout<<"  \"tested_odd_sources\":"<<tested<<",\n";
  std::cout<<"  \"direct_descent_sources\":"<<direct<<",\n";
  std::cout<<"  \"quarter_splice_sources\":"<<splice<<",\n";
  std::cout<<"  \"censored\":"<<censored<<",\n";
  std::cout<<"  \"strict_violation_sources\":"<<strict_viol_sources<<",\n";
  std::cout<<"  \"strict_violation_states\":"<<strict_viol_states<<",\n";
  std::cout<<"  \"equality_sources\":"<<equality_sources<<",\n";
  std::cout<<"  \"equality_states\":"<<equality_states<<",\n";
  std::cout<<"  \"record_ratio\":{\"n\":"<<best_n<<",\"q\":"<<best_q<<",\"k\":"<<best_k
           <<",\"x\":\""<<s128(best_x)<<"\"},\n";

  auto rows=[&](const char* name,const std::vector<EqRow>& v){
    std::cout<<"  \""<<name<<"\":[";
    for(size_t i=0;i<v.size();++i){
      if(i) std::cout<<",";
      std::cout<<"{\"n\":"<<v[i].n<<",\"k\":"<<v[i].k<<",\"q\":"<<v[i].q
               <<",\"x\":\""<<s128(v[i].x)<<"\"}";
    }
    std::cout<<"],\n";
  };
  rows("first_equalities",first_eq);
  rows("first_strict_violations",first_bad);

  std::cout<<"  \"candidate\":\"before direct descent or source-relative quarter splice, 3*oddCount(n,k) <= 4*n; equality is a terminal boundary rather than a recurrent regime\",\n";
  std::cout<<"  \"claim_boundary\":\"bounded exact conservative screen: direct descent and quarter splice only; OrdinaryExit lower merges are deliberately ignored, so zero strict violations is stronger bounded evidence but not a universal theorem\",\n";
  std::cout<<"  \"universal_status\":\"UNKNOWN\",\n";
  std::cout<<"  \"global_collatz\":\"UNKNOWN\"\n";
  std::cout<<"}\n";
  return 0;
}
