// V168 — source-attached, order-independent future-coalescence ledger.
//
// Compile: g++ -O3 -std=c++17 research/collatz_v168_retrospective_quotient.cpp -o v168
// Invoke:  ./v168 <k> <initial_H> <max_owner_clock> <T|G> [receipt.jsonl]
//
// This is a BOUNDED EXACT certificate audit. It never asserts an
// all-positive Collatz proof. Every merge records actual independent
// original-source clock coordinates and a common Nat endpoint.
// The root set is {1,2} for the genuine shortcut T and {7,14}
// for the deliberately non-Collatz control G(n)=(3n+7)/2 (odd).
//
// During phase 1 two UNKNOWN sources may merge. Only a witnessed
// terminal hit, or a path to an already good class, certifies them.
// During phase 2 an unresolved class's MINIMUM positive source is
// followed beyond H until it meets an observed component or a terminal
// root. Any real repeated nonterminal endpoint is recorded as an
// observed cycle and is NEVER treated as convergence.
//
// Stage-one scans end early when their component has a good witness:
// this is a sound, not exhaustive, H-window collision subset. The
// initial quotient is therefore the witnessed graph, not a claim
// about every possible pair of length-H orbit prefixes.
//
// Class equality is proved abstractly in Lean V168 via typed
// symm/trans closure, but source-specific 2^k ledgers remain finite
// executable evidence, not millions of separately kernel-reified
// Lean theorem statements.
//
// GLOBAL COLLATZ UNKNOWN. NO QED.

#include <bits/stdc++.h>
using namespace std;
using ull = unsigned long long;

static inline ull next_value(ull x, bool synthetic) {
  if (!(x & 1ULL)) return x / 2;
  const __uint128_t y = 3 * (__uint128_t)x + (synthetic ? 7 : 1);
  if (y / 2 > numeric_limits<ull>::max())
    throw overflow_error("A real orbit exceeded the audited UInt64 envelope");
  return (ull)(y / 2);
}

struct UnionClasses {
  vector<int> parent, size;
  vector<unsigned char> hasTerminal;

  explicit UnionClasses(int N)
      : parent(N + 1), size(N + 1, 1), hasTerminal(N + 1, 0) {
    iota(parent.begin(), parent.end(), 0);
  }

  int root(int n) {
    int r = n;
    while (parent[r] != r) r = parent[r];
    while (parent[n] != n) {
      int p = parent[n];
      parent[n] = r;
      n = p;
    }
    return r;
  }

  bool unite(int a, int b) {
    a = root(a);
    b = root(b);
    if (a == b) return false;
    if (size[a] < size[b]) swap(a, b);
    parent[b] = a;
    size[a] += size[b];
    hasTerminal[a] |= hasTerminal[b];
    return true;
  }

  void mark(int n) { hasTerminal[root(n)] = 1; }
  bool good(int n) { return hasTerminal[root(n)] != 0; }
};

struct ClassSize {
  int minimumSource, count;
};
struct Snapshot {
  int goodComponents, unknownComponents, unknownSources, largestUnknown;
  vector<ClassSize> unresolved;
};

static Snapshot snapshot(UnionClasses &classes, int N) {
  vector<int> weight(N + 1, 0), minimum(N + 1, 0);
  int unknownMass = 0, goodComponents = 0, badComponents = 0, maxWeight = 0;
  vector<ClassSize> unresolved;
  for (int n = 1; n <= N; ++n) {
    int r = classes.root(n);
    weight[r]++;
    if (!minimum[r]) minimum[r] = n;
    if (!classes.hasTerminal[r]) unknownMass++;
  }
  for (int n = 1; n <= N; ++n) {
    if (classes.parent[n] != n) continue;
    if (classes.hasTerminal[n]) {
      goodComponents++;
    } else {
      badComponents++;
      unresolved.push_back({minimum[n], weight[n]});
      maxWeight = max(maxWeight, weight[n]);
    }
  }
  sort(unresolved.begin(), unresolved.end(),
       [](ClassSize a, ClassSize b) {
         return a.count != b.count
                    ? a.count > b.count
                    : a.minimumSource < b.minimumSource;
       });
  return {goodComponents, badComponents, unknownMass, maxWeight,
          move(unresolved)};
}

static void emitClasses(ostream &o, const vector<ClassSize> &v, int limit) {
  o << "[";
  for (int j = 0; j < (int)v.size() && j < limit; ++j) {
    if (j) o << ",";
    o << "[" << v[j].minimumSource << "," << v[j].count << "]";
  }
  o << "]";
}

int main(int argc, char **argv) {
  if (argc < 5) {
    cerr << "usage: v168 <k> <H> <ownerMaxClock> <T|G> [receipt.jsonl]\n";
    return 1;
  }
  const int k = atoi(argv[1]);
  const int H = atoi(argv[2]);
  const int maxClock = atoi(argv[3]);
  const bool synthetic = string(argv[4]) == "G";
  if (k < 4 || k > 24 || H < 0 || H > 511 ||
      maxClock < H || maxClock > 2000) return 2;
  const int N = (1 << k) - 1;
  const int rootA = synthetic ? 7 : 1;
  const int rootB = synthetic ? 14 : 2;

  UnionClasses classes(N);
  // These seed roots are independently warranted closed actual cycles.
  if (next_value(rootA, synthetic) != (ull)rootB ||
      next_value(rootB, synthetic) != (ull)rootA) abort();
  classes.unite(rootA, rootB);
  classes.mark(rootA);

  // 12 low bits encode actual clock, 24 high bits original source id.
  unordered_map<ull, ull> endpointOwner;
  endpointOwner.max_load_factor(0.82);
  endpointOwner.reserve((size_t)N * 2);

  const bool saveLedger = argc > 5 && string(argv[5]) != "-";
  ofstream ledger;
  if (saveLedger) {
    ledger.open(argv[5]);
    if (!ledger) return 3;
    ledger << "{\"type\":\"seed\",\"source\":" << rootA
           << ",\"clock\":1,\"other\":" << rootB
           << ",\"other_clock\":0}\n";
  }

  long long checkedSourceClocks = 0;
  long long collisions = 0;
  long long effectiveMerges = 1; // the seeded true terminal cycle edge
  long long terminalHits = 0;

  // Phase 1: a source's provisional future class can be joined to
  // another UNKNOWN component. No convergence is inferred from that.
  // A good hit is sufficient to end this source's exploration early.
  for (int n = 1; n <= N; ++n) {
    ull x = (ull)n;
    for (int i = 0; i <= H; ++i) {
      checkedSourceClocks++;
      const bool isTerminal =
          synthetic ? (x == 7 || x == 14) : (x == 1 || x == 2);
      if (isTerminal) {
        classes.unite(n, (int)x);
        classes.mark(n);
        terminalHits++;
        if (saveLedger)
          ledger << "{\"type\":\"terminal\",\"source\":" << n
                 << ",\"clock\":" << i
                 << ",\"endpoint\":" << x << "}\n";
        break;
      }
      auto [it, inserted] =
          endpointOwner.emplace(x, ((ull)n << 12) | (unsigned)i);
      if (!inserted) {
        int p = (int)(it->second >> 12);
        int j = (int)(it->second & 4095);
        if (p <= 0 || p > n) abort();
        if (p != n) {
          collisions++;
          if (classes.unite(n, p)) {
            effectiveMerges++;
            if (saveLedger)
              ledger << "{\"type\":\"merge\",\"source\":" << n
                     << ",\"clock\":" << i
                     << ",\"other\":" << p
                     << ",\"other_clock\":" << j
                     << ",\"endpoint\":" << x << "}\n";
          }
          if (classes.good(n)) break;
        }
      }
      if (i < H) x = next_value(x, synthetic);
    }
  }

  const Snapshot initial = snapshot(classes, N);
  if (saveLedger)
    ledger << "{\"type\":\"phase\",\"name\":\"after_initial\"}\n";

  long long adaptiveSteps = 0, adaptiveEdges = 0;
  long long newEndpointStates = 0, adaptiveTerminalHits = 0;
  long long initialOwnersAttempted = 0, ownersAlreadyClosed = 0;
  long long ownersClosedAfterExtension = 0, selfCycles = 0;
  int largestNewClock = 0;
  vector<pair<int, int>> cycleReceipts;

  // Phase 2: work on the minimum actual source in each provisional
  // unclosed future component, with the largest components first.
  for (auto unresolved : initial.unresolved) {
    int owner = unresolved.minimumSource;
    if (classes.good(owner)) {
      ownersAlreadyClosed++;
      continue;
    }
    initialOwnersAttempted++;
    ull x = (ull)owner;

    // Track real repeated values; in G7 a 4-cycle is a protected
    // negative control, not a terminal certificate.
    unordered_map<ull, int> localClocks;
    localClocks.reserve((size_t)maxClock + 3);
    bool alreadyCyclic = false;
    for (int t = 0; t <= H; ++t) {
      auto [it, fresh] = localClocks.emplace(x, t);
      if (!fresh) {
        selfCycles++;
        alreadyCyclic = true;
        cycleReceipts.emplace_back(owner, t - it->second);
        if (saveLedger)
          ledger << "{\"type\":\"cycle\",\"source\":" << owner
                 << ",\"clock\":" << t
                 << ",\"earlier_clock\":" << it->second
                 << ",\"endpoint\":" << x << "}\n";
        break;
      }
      x = next_value(x, synthetic);
    }
    if (alreadyCyclic) continue;

    // Invariant on entry: x is T^(H+1)(owner), genuine Nat.
    for (int t = H + 1; t <= maxClock; ++t) {
      adaptiveSteps++;
      largestNewClock = max(largestNewClock, t);
      const bool isTerminal =
          synthetic ? (x == 7 || x == 14) : (x == 1 || x == 2);
      if (isTerminal) {
        adaptiveTerminalHits++;
        classes.unite(owner, (int)x);
        classes.mark(owner);
        if (saveLedger)
          ledger << "{\"type\":\"terminal\",\"source\":" << owner
                 << ",\"clock\":" << t
                 << ",\"endpoint\":" << x << "}\n";
      }

      auto [it, inserted] =
          endpointOwner.emplace(x, ((ull)owner << 12) | (unsigned)t);
      if (inserted) {
        newEndpointStates++;
      } else {
        int p = (int)(it->second >> 12);
        int j = (int)(it->second & 4095);
        if (p <= 0 || p > N || j > maxClock) abort();
        if (p != owner && classes.unite(owner, p)) {
          adaptiveEdges++;
          if (saveLedger)
            ledger << "{\"type\":\"merge\",\"source\":" << owner
                   << ",\"clock\":" << t
                   << ",\"other\":" << p
                   << ",\"other_clock\":" << j
                   << ",\"endpoint\":" << x << "}\n";
        }
      }
      if (classes.good(owner)) {
        ownersClosedAfterExtension++;
        break;
      }
      auto [localIt, fresh] = localClocks.emplace(x, t);
      if (!fresh) {
        selfCycles++;
        cycleReceipts.emplace_back(owner, t - localIt->second);
        if (saveLedger)
          ledger << "{\"type\":\"cycle\",\"source\":" << owner
                 << ",\"clock\":" << t
                 << ",\"earlier_clock\":" << localIt->second
                 << ",\"endpoint\":" << x << "}\n";
        break;
      }
      x = next_value(x, synthetic);
    }
  }

  const Snapshot final = snapshot(classes, N);
  cout << "{\"schema\":\"COLLATZ_V168_RETROACTIVE_FUTURE_QUOTIENT\""
       << ",\"map\":\"" << (synthetic ? "G7_SYNTHETIC" : "TRUE_COLLATZ")
       << "\",\"k\":" << k << ",\"initial_clock\":" << H
       << ",\"owner_clock_cap\":" << maxClock << ",\"positive_source_cutoff\":"
       << N << ",\"initial_checked_source_clock_pairs\":" << checkedSourceClocks
       << ",\"initial_actual_meetings\":" << collisions
       << ",\"initial_effective_mergers_including_seed\":" << effectiveMerges
       << ",\"initial_terminal_hits\":" << terminalHits
       << ",\"initial_unresolved_sources\":" << initial.unknownSources
       << ",\"initial_unresolved_components\":" << initial.unknownComponents
       << ",\"initial_largest_unresolved_component\":" << initial.largestUnknown
       << ",\"initial_good_components\":" << initial.goodComponents
       << ",\"initial_top_components\":";
  emitClasses(cout, initial.unresolved, 15);
  cout << ",\"additional_owner_attempts\":" << initialOwnersAttempted
       << ",\"initial_owners_already_closed_on_refinement\":" << ownersAlreadyClosed
       << ",\"owners_closed_by_extension\":" << ownersClosedAfterExtension
       << ",\"additional_source_clock_steps\":" << adaptiveSteps
       << ",\"additional_actual_two_clock_mergers\":" << adaptiveEdges
       << ",\"additional_direct_terminal_hits\":" << adaptiveTerminalHits
       << ",\"additional_new_endpoint_states\":" << newEndpointStates
       << ",\"largest_new_owner_clock\":" << largestNewClock
       << ",\"observed_nonterminal_cycle_receipts\":" << selfCycles
       << ",\"cycle_examples\":[";
  for (int i = 0; i < (int)cycleReceipts.size() && i < 12; ++i) {
    if (i) cout << ",";
    cout << "[" << cycleReceipts[i].first << ","
         << cycleReceipts[i].second << "]";
  }
  cout << "],\"final_unresolved_sources\":" << final.unknownSources
       << ",\"final_unresolved_components\":" << final.unknownComponents
       << ",\"final_largest_unresolved_component\":" << final.largestUnknown
       << ",\"final_good_components\":" << final.goodComponents
       << ",\"final_top_components\":";
  emitClasses(cout, final.unresolved, 15);
  cout << ",\"finite_certificate_coverage_only\":true"
       << ",\"global_collatz\":\"UNKNOWN\",\"qed\":false}\n";
  return 0;
}
