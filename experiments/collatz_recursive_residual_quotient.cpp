// Exact recursive residual consequence quotient for the shortcut Collatz map.
//
// This experiment changes the unit of work from individual residues at every
// modulus to the *hereditary live residual tree*.
//
// For a residue b mod 2^k, let c be the number of odd shortcut steps in the
// first k steps and d=T^k(b).  Then for every a>=0:
//
//   T^k(a*2^k+b) = a*3^c + d.                         (1)
//
// If the family is live at depth k, its two children at depth k+1 can be
// derived exactly without replaying the first k steps.  Write e in {0,1} for
// the next high residue bit.  Substituting a=2A+e in (1) gives
//
//   T^k(A*2^(k+1) + b + e*2^k) = 2A*3^c + (d+e*3^c).
//
// The parity of y=d+e*3^c is independent of A, so one shortcut step gives the
// child's exact affine state (c',d').
//
// A child family is closed by immediate strong-induction descent whenever
//
//   l = 3^c' - 2^(k+1) < 0
//   l < r = b' - d'.
//
// Because l<0, A*l is maximized at A=1, so these inequalities imply
//
//   A*3^c' + d' < A*2^(k+1) + b'   for every A>=1.
//
// Once a node is closed, every extension is inherited closure and is never
// materialized.  This program intentionally omits the additional global
// coalescence rule from collatz_strong_sieve_scout.cpp.  It is therefore a
// sound *weaker* closure system: it may leave extra UNKNOWN nodes but cannot
// gain closure from the omitted rule.
//
// After constructing the exact live-only tree, we quotient nodes bottom-up by
// their complete bounded future consequence: two nodes are equivalent through
// target K iff their ordered (0-child,1-child) signature is identical, with
// CLOSED=0 and unresolved-at-K=1.  This is exact finite-horizon consequence
// minimization, not a claim of global Collatz closure.
//
// The purpose is to measure whether the residual language itself compresses
// and stabilizes strongly enough to motivate a recursively closed constructor
// algebra.

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <limits>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using u128 = unsigned __int128;
using i128 = __int128;

static constexpr uint32_t DEAD = std::numeric_limits<uint32_t>::max();

struct State {
  uint64_t b;
  uint64_t d;
  uint32_t c;
};

struct Edge {
  uint32_t lo;
  uint32_t hi;
};

static inline u128 T128(u128 n) {
  return (n & 1) ? (3 * n + 1) / 2 : n / 2;
}

static std::pair<uint32_t,uint64_t> direct_cd(uint64_t b, int k) {
  u128 x = b;
  uint32_t c = 0;
  for (int i=0;i<k;++i) {
    if (x & 1) ++c;
    x = T128(x);
  }
  if (x > std::numeric_limits<uint64_t>::max()) {
    std::cerr << "DIRECT_D_OVERFLOW\n";
    std::exit(3);
  }
  return {c, static_cast<uint64_t>(x)};
}

static u128 direct_iterate(u128 n, int k) {
  for (int i=0;i<k;++i) n=T128(n);
  return n;
}

static void verify_state(
    const State& s,
    int k,
    const std::vector<uint64_t>& p3) {
  auto [c,d] = direct_cd(s.b,k);
  if (c!=s.c || d!=s.d) {
    std::cerr << "STATE_DIRECT_REPLAY_MISMATCH"
              << " k=" << k
              << " b=" << s.b
              << " expected_c=" << s.c
              << " got_c=" << c
              << " expected_d=" << s.d
              << " got_d=" << d << "\n";
    std::exit(4);
  }

  // Independent checks of the exact affine identity (1).
  const u128 M = u128(1) << k;
  for (uint64_t a : {1ULL,3ULL}) {
    const u128 n = u128(a)*M + s.b;
    const u128 lhs = direct_iterate(n,k);
    const u128 rhs = u128(a)*p3[s.c] + s.d;
    if (lhs != rhs) {
      std::cerr << "AFFINE_IDENTITY_MISMATCH"
                << " k=" << k << " b=" << s.b
                << " a=" << a << "\n";
      std::exit(5);
    }
  }
}

static uint64_t pair_key(uint32_t a, uint32_t b) {
  return (uint64_t(a) << 32) | uint64_t(b);
}

int main(int argc, char** argv) {
  if (argc != 2) {
    std::cerr << "usage: recursive_residual K\n";
    return 2;
  }
  const int K = std::stoi(argv[1]);
  if (K < 1 || K > 32) {
    std::cerr << "K_OUT_OF_EXACT_SCOUT_RANGE\n";
    return 2;
  }

  std::vector<uint64_t> p3(K+2,1);
  for (int i=1;i<(int)p3.size();++i) {
    if (p3[i-1] > std::numeric_limits<uint64_t>::max()/3) {
      std::cerr << "POW3_OVERFLOW\n";
      return 3;
    }
    p3[i] = p3[i-1]*3;
  }

  std::vector<State> states;
  states.push_back({0,0,0});

  // edges[k] maps live nodes at depth k to live/dead children at k+1.
  std::vector<std::vector<Edge>> edges(K);
  std::vector<uint64_t> live_count(K+1,0);
  live_count[0]=1;
  u128 raw_live_nodes=1;

  uint64_t replay_checks=0;
  uint64_t killed_checks=0;

  for (int k=1;k<=K;++k) {
    const uint64_t half = uint64_t(1) << (k-1);
    const uint64_t M = uint64_t(1) << k;

    auto& E = edges[k-1];
    E.resize(states.size());

    if (states.size() > size_t(std::numeric_limits<uint32_t>::max())) {
      std::cerr << "PARENT_INDEX_RANGE_EXCEEDED\n";
      return 6;
    }

    std::vector<State> next;
    if (states.size() <= size_t(std::numeric_limits<uint32_t>::max()/2)) {
      next.reserve(states.size()*2);
    }

    uint64_t killed=0;

    for (size_t i=0;i<states.size();++i) {
      const State s=states[i];
      if (s.c >= p3.size()) {
        std::cerr << "C_RANGE_EXCEEDED\n";
        return 7;
      }
      const uint64_t P=p3[s.c];
      Edge edge{DEAD,DEAD};

      for (int e=0;e<2;++e) {
        const uint64_t b = s.b + (e ? half : 0);
        const uint64_t y = s.d + (e ? P : 0);

        uint32_t c=s.c;
        uint64_t d;
        if (y & 1) {
          ++c;
          if (y > (std::numeric_limits<uint64_t>::max()-1)/3) {
            std::cerr << "CHILD_D_OVERFLOW\n";
            return 8;
          }
          d=(3*y+1)/2;
        } else {
          d=y/2;
        }

        const i128 l=i128(p3[c])-i128(M);
        const i128 r=i128(b)-i128(d);
        const bool closed=(l<0 && l<r);

        if (closed) {
          ++killed;
          // Deterministically sample exact concrete replay of the universal
          // descent inequality at A=1.  The algebraic l/r test itself is exact
          // for all A>=1.
          if (killed_checks < 4096) {
            const u128 n=u128(M)+b;
            const u128 z=direct_iterate(n,k);
            if (!(z<n)) {
              std::cerr << "KILLED_CHILD_FAILED_DIRECT_DESCENT"
                        << " k=" << k << " b=" << b << "\n";
              return 9;
            }
            ++killed_checks;
          }
          continue;
        }

        if (next.size() >= size_t(std::numeric_limits<uint32_t>::max())) {
          std::cerr << "CHILD_INDEX_RANGE_EXCEEDED\n";
          return 10;
        }
        const uint32_t idx=static_cast<uint32_t>(next.size());
        next.push_back({b,d,c});
        if (e==0) edge.lo=idx; else edge.hi=idx;
      }
      E[i]=edge;
    }

    // Independent direct controls: exhaustive while tiny, then deterministic
    // spread samples.  These are controls on implementation, not assumptions.
    if (!next.empty()) {
      if (next.size() <= 4096) {
        for (const State& s:next) {
          verify_state(s,k,p3);
          ++replay_checks;
        }
      } else {
        const size_t samples=257;
        for (size_t j=0;j<samples;++j) {
          const size_t idx=(j*(next.size()-1))/(samples-1);
          verify_state(next[idx],k,p3);
          ++replay_checks;
        }
      }
    }

    live_count[k]=next.size();
    raw_live_nodes += u128(next.size());

    std::cout << "RECURSIVE_LEVEL"
              << " k=" << k
              << " parents=" << states.size()
              << " generated=" << (u128(states.size())*2)
              << " killed_by_descent=" << killed
              << " live=" << next.size()
              << "\n";

    states.swap(next);
  }

  const uint64_t frontier_live=states.size();

  // Semantic state values are no longer required.  Free the potentially huge
  // frontier before allocating bottom-up signature vectors.
  std::vector<State>().swap(states);

  // Signature 0=CLOSED, 1=UNKNOWN at target horizon.
  std::vector<uint32_t> next_sig(frontier_live,1),cur_sig;
  std::unordered_map<uint64_t,uint32_t> intern;
  intern.reserve(65536);
  uint32_t next_id=2;

  uint64_t max_unique=1;
  int max_unique_depth=K;

  std::cout << std::setprecision(12)
            << "RECURSIVE_QUOTIENT_LEVEL"
            << " k=" << K
            << " remaining=0"
            << " nodes=" << frontier_live
            << " unique_signatures=1"
            << " compression=" << (frontier_live ? double(frontier_live) : 0.0)
            << "\n";

  for (int k=K-1;k>=0;--k) {
    const auto& E=edges[k];
    cur_sig.resize(E.size());

    std::unordered_set<uint32_t> unique;
    unique.reserve(std::min<size_t>(E.size(),65536));

    for (size_t i=0;i<E.size();++i) {
      const uint32_t a=(E[i].lo==DEAD) ? 0 : next_sig[E[i].lo];
      const uint32_t b=(E[i].hi==DEAD) ? 0 : next_sig[E[i].hi];
      const uint64_t key=pair_key(a,b);

      auto it=intern.find(key);
      if (it==intern.end()) {
        if (next_id==DEAD) {
          std::cerr << "SIGNATURE_ID_RANGE_EXCEEDED\n";
          return 11;
        }
        it=intern.emplace(key,next_id++).first;
      }
      cur_sig[i]=it->second;
      unique.insert(it->second);
    }

    const uint64_t u=unique.size();
    if (u>max_unique) {
      max_unique=u;
      max_unique_depth=k;
    }

    const double compression = u ? double(E.size())/double(u) : 0.0;
    std::cout << "RECURSIVE_QUOTIENT_LEVEL"
              << " k=" << k
              << " remaining=" << (K-k)
              << " nodes=" << E.size()
              << " unique_signatures=" << u
              << " compression=" << compression
              << "\n";

    next_sig.swap(cur_sig);
  }

  if (next_sig.size()!=1) {
    std::cerr << "ROOT_SIGNATURE_COUNT_MISMATCH\n";
    return 12;
  }

  const uint32_t root_signature=next_sig[0];

  auto print_u128=[](u128 x) {
    if (!x) { std::cout << '0'; return; }
    std::string s;
    while (x) {
      s.push_back(char('0'+x%10));
      x/=10;
    }
    std::reverse(s.begin(),s.end());
    std::cout << s;
  };

  std::cout << "RECURSIVE_CONTROLS"
            << " direct_state_replays=" << replay_checks
            << " direct_killed_replays=" << killed_checks
            << "\n";

  std::cout << "RECURSIVE_QUOTIENT_DONE"
            << " K=" << K
            << " frontier_live=" << frontier_live
            << " raw_live_nodes=";
  print_u128(raw_live_nodes);
  std::cout << " signature_types=" << next_id
            << " root_signature=" << root_signature
            << " max_unique_signatures=" << max_unique
            << " max_unique_depth=" << max_unique_depth
            << "\n";

  std::cout << "VERIFIED_RECURSIVE_RESIDUAL_CONSEQUENCE_QUOTIENT\n";
  return 0;
}
