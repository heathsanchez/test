// Exact future-consequence quotient for finite-horizon Collatz transfer survival.
//
// Key law:
//   at prefix depth p with R = TARGET-p suffix bits remaining, every future
//   survival/death consequence depends only on (q, d mod 2^R).
//
// The next parity depends only on d mod 2, and after one shortcut step the
// next residue modulo 2^(R-1) depends only on the previous residue modulo 2^R.
// The contraction test itself depends only on q and the absolute step index.
// Therefore prefixes with equal (q, d mod 2^R) are goal-equivalent through
// TARGET and can be merged immediately, with exact multiplicity.
//
// This is intentionally a scientific scout: it counts the exact live residue
// classes while carrying only the consequence quotient. It does not yet replace
// the production seed verifier.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>

using u128 = unsigned __int128;

static std::string s128(u128 x) {
  if (!x) return "0";
  std::string s;
  while (x) { s.push_back(char('0' + x % 10)); x /= 10; }
  std::reverse(s.begin(), s.end());
  return s;
}

struct Entry {
  uint64_t key;
  uint64_t weight;
};

static inline uint64_t make_key(uint16_t q, uint64_t r) {
  return (uint64_t(q) << 56) | r;
}
static inline uint16_t key_q(uint64_t k) { return uint16_t(k >> 56); }
static inline uint64_t key_r(uint64_t k) { return k & ((uint64_t(1) << 56) - 1); }

static uint64_t mask_bits(int r) {
  if (r <= 0) return 0;
  if (r >= 56) {
    std::cerr << "REMAINDER_BITS_TOO_LARGE\n";
    std::exit(4);
  }
  return (uint64_t(1) << r) - 1;
}

int main(int argc, char** argv) {
  if (argc < 3 || argc > 4) {
    std::cerr << "usage: future_quotient K TARGET_P [MAX_NODES]\n";
    return 2;
  }
  const int K = std::stoi(argv[1]);
  const int TARGET = std::stoi(argv[2]);
  const uint64_t MAX_NODES = argc == 4 ? std::stoull(argv[3]) : 12000000ULL;

  if (K < 1 || K > 50 || TARGET < 3 || TARGET > 55 || K + TARGET >= 127) {
    std::cerr << "BAD_RANGE\n";
    return 2;
  }

  std::vector<u128> pow3(K + TARGET + 2);
  pow3[0] = 1;
  for (size_t i = 1; i < pow3.size(); ++i) pow3[i] = pow3[i - 1] * 3;

  // Exact predecessor-half quotient at p=2, matching the retained prefix scout.
  const int killed_mod4 = (K & 1) ? 3 : 1;
  std::vector<Entry> cur;
  for (uint64_t m : {1ULL, 3ULL}) {
    if (int(m & 3ULL) == killed_mod4) continue;

    u128 d = (u128(m) << K) - 1;
    uint16_t q = 0;
    bool alive = true;
    for (int t = 1; t <= K + 2; ++t) {
      if (d & 1) { ++q; d = (3 * d + 1) >> 1; }
      else d >>= 1;
      if (pow3[q] < (u128(1) << t)) alive = false;
    }
    if (!alive) continue;

    const int R = TARGET - 2;
    uint64_t r = uint64_t(d) & mask_bits(R);
    cur.push_back({make_key(q, r), 1});
  }

  if (cur.empty()) {
    std::cout << "FUTURE_QUOTIENT_EMPTY_AT_ROOT K=" << K << " target=" << TARGET << "\n";
    return 0;
  }

  uint64_t represented = 0;
  for (const auto& e : cur) represented += e.weight;
  std::cout << std::setprecision(12)
            << "FUTURE_QUOTIENT_LEVEL K=" << K
            << " target=" << TARGET
            << " p=2 nodes=" << cur.size()
            << " represented_live=" << represented
            << " compression=" << (double(represented) / double(cur.size()))
            << " killed_here=0\n";

  uint64_t peak_nodes = cur.size();
  int peak_p = 2;

  for (int p = 2; p < TARGET; ++p) {
    const int np = p + 1;
    const int R = TARGET - p;
    const int NR = R - 1;
    const int W = K + np;
    const uint64_t mask = mask_bits(R);
    const uint64_t nmask = mask_bits(NR);

    // 3^q modulo 2^R for all reachable q.
    std::vector<uint64_t> p3mod(K + TARGET + 2);
    p3mod[0] = 1 & mask;
    for (size_t q = 1; q < p3mod.size(); ++q)
      p3mod[q] = (p3mod[q - 1] * 3ULL) & mask;

    // The quotient normally stays far smaller than the represented class set.
    std::unordered_map<uint64_t, uint64_t> nxt;
    uint64_t reserve_hint = std::min<uint64_t>(
        MAX_NODES, std::max<uint64_t>(1024, std::min<uint64_t>(cur.size() * 2ULL, MAX_NODES)));
    nxt.reserve(size_t(reserve_hint));

    uint64_t killed = 0;
    uint64_t parent_weight = 0;
    for (const auto& e : cur) {
      const uint16_t q = key_q(e.key);
      const uint64_t d = key_r(e.key) & mask;
      parent_weight += e.weight;

      for (int b = 0; b < 2; ++b) {
        uint64_t y = d;
        if (b) y = (y + p3mod[q]) & mask;

        uint16_t q2 = q;
        uint64_t d2;
        if (y & 1ULL) {
          ++q2;
          d2 = ((3ULL * y + 1ULL) >> 1) & nmask;
        } else {
          d2 = (y >> 1) & nmask;
        }

        if (pow3[q2] < (u128(1) << W)) {
          killed += e.weight;
          continue;
        }

        // With no suffix left, every surviving prefix is the same LIVE terminal.
        const uint64_t nk = (NR == 0) ? 1ULL : make_key(q2, d2);
        auto it = nxt.find(nk);
        if (it == nxt.end()) nxt.emplace(nk, e.weight);
        else it->second += e.weight;
      }
    }

    if (nxt.size() > MAX_NODES) {
      std::cout << "FUTURE_QUOTIENT_ABORT K=" << K
                << " target=" << TARGET
                << " p=" << np
                << " nodes=" << nxt.size()
                << " max_nodes=" << MAX_NODES << "\n";
      return 0;
    }

    uint64_t child_weight = 0;
    cur.clear();
    cur.reserve(nxt.size());
    for (const auto& kv : nxt) {
      cur.push_back({kv.first, kv.second});
      child_weight += kv.second;
    }

    if (child_weight + killed != parent_weight * 2ULL) {
      std::cerr << "WEIGHT_CONSERVATION_FAILED p=" << np << "\n";
      return 5;
    }

    if (cur.size() > peak_nodes) { peak_nodes = cur.size(); peak_p = np; }

    std::cout << "FUTURE_QUOTIENT_LEVEL K=" << K
              << " target=" << TARGET
              << " p=" << np
              << " nodes=" << cur.size()
              << " represented_live=" << child_weight
              << " compression=" << (cur.empty() ? 0.0 : double(child_weight) / double(cur.size()))
              << " killed_here=" << killed << "\n";
  }

  uint64_t final_live = 0;
  for (const auto& e : cur) final_live += e.weight;

  std::cout << "FUTURE_QUOTIENT_DONE K=" << K
            << " target=" << TARGET
            << " final_live_classes=" << final_live
            << " final_nodes=" << cur.size()
            << " peak_nodes=" << peak_nodes
            << " peak_p=" << peak_p << "\n";
  std::cout << "VERIFIED_EXACT_FINITE_HORIZON_FUTURE_MOD_QUOTIENT\n";
  return 0;
}
