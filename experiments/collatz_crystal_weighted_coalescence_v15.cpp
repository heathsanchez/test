#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <string>
#include <unordered_map>
#include <vector>

using u64 = std::uint64_t;
using u128 = __uint128_t;
using i64 = std::int64_t;

static inline u64 T(u64 x) {
  if (x & 1ULL) {
    u128 z = (u128)3*x + 1;
    assert(z <= std::numeric_limits<u64>::max());
    return (u64)(z/2);
  }
  return x/2;
}

struct Entry {
  i64 budget;
  u64 source;
  u64 q;
  u64 k;
};

struct StateRow {
  u64 x,q,k;
  i64 budget;
};

struct Witness {
  u64 n,k,q,x;
  i64 budget;
  u64 p,pk,pq;
  i64 pbudget;
};

static void print_witness(const Witness& w) {
  std::cout<<"{"
    <<"\"n\":"<<w.n<<",\"k\":"<<w.k<<",\"q\":"<<w.q
    <<",\"x\":"<<w.x<<",\"budget\":"<<w.budget
    <<",\"p\":"<<w.p<<",\"p_k\":"<<w.pk<<",\"p_q\":"<<w.pq
    <<",\"p_budget\":"<<w.pbudget<<"}";
}

int main(int argc,char**argv){
  const u64 limit = argc>1 ? std::stoull(argv[1]) : (1ULL<<20);
  const u64 cap = argc>2 ? std::stoull(argv[2]) : 4096;

  std::unordered_map<u64,Entry> best;
  best.reserve((size_t)limit*2);

  u64 tested=0,direct=0,splice=0,merge=0,viol=0,censored=0;
  u64 inserted=0,replaced=0;
  i64 global_min_budget=std::numeric_limits<i64>::max();
  Witness minw{};
  std::vector<Witness> first_merges, first_violations, low_budget;

  for(u64 n=3;n<limit;n+=2){
    ++tested;
    u64 x=n,q=0,k=0;
    bool closed=false;
    enum Kind {NONE,DIRECT,SPLICE,MERGE,VIOL,CENSOR};
    Kind kind=NONE;
    Entry ment{};
    i64 mbudget=0;
    std::vector<StateRow> path;
    path.reserve(256);

    while(k<=cap){
      if(x<n){ kind=DIRECT; closed=true; ++direct; break; }
      if((x&7ULL)==5ULL && (u128)x <= (u128)4*n){
        kind=SPLICE; closed=true; ++splice; break;
      }

      i64 budget=(i64)(4*n)-(i64)(3*q);
      if(budget<global_min_budget){
        global_min_budget=budget;
        minw={n,k,q,x,budget,0,0,0,0};
      }
      if(budget<0){
        kind=VIOL; ++viol;
        if(first_violations.size()<20)
          first_violations.push_back({n,k,q,x,budget,0,0,0,0});
        break;
      }
      if(budget<=12 && low_budget.size()<80)
        low_budget.push_back({n,k,q,x,budget,0,0,0,0});

      auto it=best.find(x);
      if(it!=best.end() && it->second.source<n && it->second.budget<=budget){
        kind=MERGE; closed=true; ++merge; ment=it->second; mbudget=budget;
        if(first_merges.size()<80)
          first_merges.push_back({n,k,q,x,budget,
            ment.source,ment.k,ment.q,ment.budget});
        break;
      }

      path.push_back({x,q,k,budget});
      if(x&1ULL) ++q;
      x=T(x); ++k;
    }

    if(kind==NONE){
      kind=CENSOR; ++censored;
    }

    if(closed){
      // Strong-induction certificate: only sources already closed by an
      // elementary exit or a weighted merge are allowed to teach later ones.
      for(const auto &s:path){
        auto it=best.find(s.x);
        if(it==best.end()){
          best.emplace(s.x,Entry{s.budget,n,s.q,s.k});
          ++inserted;
        }else if(s.budget<it->second.budget){
          it->second=Entry{s.budget,n,s.q,s.k};
          ++replaced;
        }
      }
    }
  }

  std::cout<<"{\n";
  std::cout<<"  \"schema\":\"COLLATZ_CRYSTAL_WEIGHTED_COALESCENCE_V15\",\n";
  std::cout<<"  \"limit\":"<<limit<<",\n";
  std::cout<<"  \"step_cap\":"<<cap<<",\n";
  std::cout<<"  \"tested_odd_sources\":"<<tested<<",\n";
  std::cout<<"  \"direct_exit_sources\":"<<direct<<",\n";
  std::cout<<"  \"quarter_splice_sources\":"<<splice<<",\n";
  std::cout<<"  \"weighted_merge_sources\":"<<merge<<",\n";
  std::cout<<"  \"strict_budget_violations\":"<<viol<<",\n";
  std::cout<<"  \"censored\":"<<censored<<",\n";
  std::cout<<"  \"stored_common_future_states\":"<<best.size()<<",\n";
  std::cout<<"  \"inserted_states\":"<<inserted<<",\n";
  std::cout<<"  \"improved_state_budgets\":"<<replaced<<",\n";
  std::cout<<"  \"minimum_live_budget\":"<<global_min_budget<<",\n";
  std::cout<<"  \"minimum_live_budget_witness\":";
  print_witness(minw);
  std::cout<<",\n";

  auto print_rows=[&](const char* name,const std::vector<Witness>& rows){
    std::cout<<"  \""<<name<<"\":[";
    for(size_t i=0;i<rows.size();++i){
      if(i)std::cout<<",";
      print_witness(rows[i]);
    }
    std::cout<<"],\n";
  };
  print_rows("first_weighted_merges",first_merges);
  print_rows("first_strict_budget_violations",first_violations);
  print_rows("first_low_budget_states",low_budget);

  std::cout<<"  \"law\":\"at common future x, 4n-3q_n >= 4p-3q_p; future parity is identical, so the budget difference is invariant\",\n";
  std::cout<<"  \"candidate\":\"strong induction on source using direct descent, quarter splice, or weighted lower-source coalescence before four-thirds budget exhaustion\",\n";
  std::cout<<"  \"claim_boundary\":\"bounded source-ordered exact replay; complete finite closure does not prove universal existence of a weighted lower-source merge\",\n";
  std::cout<<"  \"universal_status\":\"UNKNOWN\",\n";
  std::cout<<"  \"global_collatz\":\"UNKNOWN\"\n";
  std::cout<<"}\n";
  return 0;
}
