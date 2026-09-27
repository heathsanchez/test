#include <boost/multiprecision/cpp_int.hpp>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using boost::multiprecision::cpp_int;

struct Owner {
  uint32_t source;
  uint32_t depth;
};

struct Hit {
  uint32_t source;
  uint32_t odd_count;
  uint32_t depth_at_highodd;
  uint64_t state_at_highodd;
  bool coefficient_survives;
  uint32_t merge_depth;
  uint64_t meeting_state;
  uint32_t smaller_source;
  uint32_t smaller_source_depth;
};

static uint64_t T(uint64_t x) {
  if ((x & 1ULL) == 0) return x / 2;
  __uint128_t z = (static_cast<__uint128_t>(3) * x + 1) / 2;
  if (z > std::numeric_limits<uint64_t>::max()) {
    std::cerr << "uint64 overflow at state " << x << "\n";
    std::exit(3);
  }
  return static_cast<uint64_t>(z);
}

static cpp_int pow3(uint32_t e) {
  cpp_int base = 3;
  cpp_int out = 1;
  while (e) {
    if (e & 1U) out *= base;
    e >>= 1U;
    if (e) base *= base;
  }
  return out;
}

int main(int argc, char** argv) {
  uint32_t limit = (1U << 24) - 1;
  if (argc > 1) limit = static_cast<uint32_t>(std::stoul(argv[1]));
  if (limit < 27) return 2;

  std::unordered_map<uint64_t, Owner> owner;
  owner.reserve(static_cast<size_t>(limit) * 2);
  owner.emplace(1, Owner{1, 0});
  owner.emplace(2, Owner{1, 1});

  std::vector<Hit> hits;
  std::vector<uint64_t> path;
  path.reserve(512);
  uint32_t max_merge_depth = 0;
  uint64_t max_state = 2;

  for (uint32_t n = 2; n <= limit; ++n) {
    uint64_t x = n;
    uint32_t q = 0;
    uint32_t k = 0;
    bool high_seen = false;
    uint32_t high_k = 0;
    uint64_t high_x = 0;
    bool high_survives = false;
    path.clear();

    auto it = owner.find(x);
    while (it == owner.end()) {
      if (!high_seen && q >= n) {
        high_seen = true;
        high_k = k;
        high_x = x;
        cpp_int lhs = cpp_int(1) << k;
        cpp_int rhs = pow3(q);
        high_survives = lhs <= rhs;
      }

      path.push_back(x);
      if (x > max_state) max_state = x;
      q += static_cast<uint32_t>(x & 1ULL);
      x = T(x);
      ++k;
      if (k > 100000U) {
        std::cerr << "step cap exceeded at source " << n << "\n";
        return 4;
      }
      it = owner.find(x);
    }

    if (k > max_merge_depth) max_merge_depth = k;
    if (high_seen && high_survives) {
      hits.push_back(Hit{
        n, q >= n ? n : q, high_k, high_x, high_survives,
        k, x, it->second.source, it->second.depth
      });
    }

    for (uint32_t d = 0; d < path.size(); ++d) {
      owner.emplace(path[d], Owner{n, d});
    }

    if (n == ((1U << 20) - 1)) {
      if (hits.size() != 1 || hits[0].source != 27) {
        std::cerr << "2^20 regression failed; hit count=" << hits.size() << "\n";
        return 5;
      }
    }
    if (n == limit) break; // avoid uint32 wrap if caller supplies UINT32_MAX
  }

  std::cout << "{\n";
  std::cout << "  \"schema\":\"COLLATZ_HIGHODD_SOURCE_ORDER_CENSUS_V1\",\n";
  std::cout << "  \"source_limit\":" << limit << ",\n";
  std::cout << "  \"owner_states\":" << owner.size() << ",\n";
  std::cout << "  \"max_merge_depth\":" << max_merge_depth << ",\n";
  std::cout << "  \"max_state_indexed\":\"" << max_state << "\",\n";
  std::cout << "  \"highodd_before_lower_merge_count\":" << hits.size() << ",\n";
  std::cout << "  \"hits\":[";
  for (size_t i = 0; i < hits.size(); ++i) {
    const auto& h = hits[i];
    if (i) std::cout << ",";
    std::cout << "\n    {"
      << "\"source\":" << h.source
      << ",\"depth_at_highodd\":" << h.depth_at_highodd
      << ",\"odd_count\":" << h.source
      << ",\"state_at_highodd\":\"" << h.state_at_highodd << "\""
      << ",\"coefficient_survives\":" << (h.coefficient_survives ? "true" : "false")
      << ",\"merge_depth\":" << h.merge_depth
      << ",\"meeting_state\":\"" << h.meeting_state << "\""
      << ",\"smaller_source\":" << h.smaller_source
      << ",\"smaller_source_depth\":" << h.smaller_source_depth
      << "}";
  }
  if (!hits.empty()) std::cout << "\n  ";
  std::cout << "],\n";
  std::cout << "  \"interpretation\":\"Exact bounded source-order census. A hit means the source reaches q>=n with surviving multiplicative coefficient before its first certified merge into any smaller processed source future.\",\n";
  std::cout << "  \"epistemic_state\":\"BOUNDED_EVIDENCE_ONLY\",\n";
  std::cout << "  \"global_collatz\":\"UNKNOWN\"\n";
  std::cout << "}\n";
  return 0;
}
