#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <map>
#include <unordered_map>
#include <vector>

using u64 = std::uint64_t;
using u128 = __uint128_t;
using i64 = std::int64_t;

static inline u64 T(u64 x) {
  if (x & 1ULL) {
    u128 z = (u128)3 * x + 1;
    assert(z <= std::numeric_limits<u64>::max());
    return (u64)(z / 2);
  }
  return x / 2;
}

struct Entry { i64 budget; u64 source, q, k; };
struct StateRow { u64 x, q, k; i64 budget; };

int main() {
  const u64 limit = 1ULL << 20;
  const u64 cap = 4096;

  std::unordered_map<u64, Entry> best;
  best.reserve((size_t)limit * 2);

  u64 tested=0, direct=0, splice=0, merge=0, violation=0, censored=0;
  std::map<int,std::array<u64,3>> byClass;
  u64 maxMergeK=0, maxOwnerK=0;

  for (u64 n=3; n<limit; n+=2) {
    ++tested;
    u64 x=n, q=0, k=0;
    bool closed=false;
    int kind=-1;
    std::vector<StateRow> path;
    path.reserve(256);

    while (k<=cap) {
      if (x<n) { kind=0; ++direct; closed=true; break; }
      if ((x&7ULL)==5ULL && (u128)x <= (u128)4*n) {
        kind=1; ++splice; closed=true; break;
      }

      i64 budget=(i64)(4*n)-(i64)(3*q);
      if (budget<0) { kind=3; ++violation; break; }

      auto it=best.find(x);
      if (it!=best.end() && it->second.source<n &&
          it->second.budget<=budget) {
        kind=2; ++merge; closed=true;
        maxMergeK=std::max(maxMergeK,k);
        maxOwnerK=std::max(maxOwnerK,it->second.k);
        break;
      }

      path.push_back({x,q,k,budget});
      if (x&1ULL) ++q;
      x=T(x); ++k;
    }

    if (kind==-1) ++censored;
    if (kind>=0 && kind<3) byClass[(int)(n%24)][kind]++;

    if (closed) {
      for (const auto &s : path) {
        auto it=best.find(s.x);
        if (it==best.end()) {
          best.emplace(s.x,Entry{s.budget,n,s.q,s.k});
        } else if (s.budget < it->second.budget) {
          it->second=Entry{s.budget,n,s.q,s.k};
        }
      }
    }
  }

  assert(tested==524287);
  assert(direct==85143);
  assert(splice==237022);
  assert(merge==202122);
  assert(violation==0);
  assert(censored==0);
  assert(direct+splice+merge==tested);

  std::cout << "{\n";
  std::cout << "  \"schema\":\"COLLATZ_CRYSTAL_FOUR_THIRDS_CONSTRUCTOR_V20\",\n";
  std::cout << "  \"limit\":" << limit << ",\n";
  std::cout << "  \"tested_odd_sources\":" << tested << ",\n";
  std::cout << "  \"direct_exit_sources\":" << direct << ",\n";
  std::cout << "  \"quarter_splice_sources\":" << splice << ",\n";
  std::cout << "  \"weighted_lower_merge_sources\":" << merge << ",\n";
  std::cout << "  \"budget_violations\":" << violation << ",\n";
  std::cout << "  \"censored\":" << censored << ",\n";
  std::cout << "  \"max_merge_source_depth\":" << maxMergeK << ",\n";
  std::cout << "  \"max_smaller_source_depth\":" << maxOwnerK << ",\n";
  std::cout << "  \"minimal_bad_source_classes\":{";
  bool first=true;
  for (int c : {3,7,15,19}) {
    if (!first) std::cout << ",";
    first=false;
    auto a=byClass[c];
    std::cout << "\"" << c << "\":{\"direct\":" << a[0]
              << ",\"splice\":" << a[1]
              << ",\"merge\":" << a[2] << "}";
  }
  std::cout << "},\n";
  std::cout << "  \"protected_output\":\"DIRECT_OR_QUARTER_SPLICE_OR_BUDGET_PRESERVING_LOWER_SOURCE_MERGE\",\n";
  std::cout << "  \"bounded_v20_residual\":0,\n";
  std::cout << "  \"interpretation\":\"the V15 source-ordered weighted closure is already a bounded producer for the V20 constructor interface; the remaining task is universal constructor totality, not parity-word nonexistence\",\n";
  std::cout << "  \"universal_status\":\"UNKNOWN\",\n";
  std::cout << "  \"global_collatz\":\"UNKNOWN\"\n";
  std::cout << "}\n";
}
