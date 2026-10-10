// V173 — adaptive source-locked component reclosure, preserving V172 initial graph.
// An actual two-clock edge may connect UNKNOWN classes without certifying them.
// After the initial H=8*k quotient, extend only one minimum original source
// representative of each still-unseeded component. Every new join is an
// exact Nat endpoint equality with two genuine independently replayable clocks.
// Status is bounded finite source certification; universal Collatz UNKNOWN.
// Compiler: g++ -O3 -std=c++17 research/collatz_v172_dominant_clock_graph.cpp -o v172
// Invocation: v172 <k> <T|G|S> [source_component_labels.csv] [source_edge_receipts.jsonl]
//
// Modes:
//   T true Collatz shortcut, even n/2, odd (3n+1)/2;
//   G synthetic generalized 3n+7 map, with disjoint positive cycles;
//   S synthetic ONE-ARROW map S(5)=5, S(n)=T(n) otherwise.
//
// All original vertices are positive n in [1,2^k).
// All clocks have the INDEPENDENT fixed ceiling H(k)=8k.
// A first arriving owner (p,j) at true endpoint x dominates an
// additional source (n,i) when j<=i: its remaining budget is at
// least as large. The source components are merged, then the
// later suffix may be skipped without losing future path connections.
// If i<j, replace the owner with the earlier arrival and continue.
//
// Formal V172 proves sound endpoint dominance and source-typed
// transitive preservation. This C++ program has independent exact
// exhaustive crosschecks at k<=14 against every source/clock edge.
// No universal Collatz convergence or no-giant theorem is inferred.

#include <bits/stdc++.h>
using namespace std;
using ull=unsigned long long;

struct Union {
  vector<int> parent, size, minSource;
  vector<unsigned char> seeded;
  explicit Union(int N)
      : parent(N+1), size(N+1,1), minSource(N+1), seeded(N+1,0) {
    iota(parent.begin(),parent.end(),0);
    iota(minSource.begin(),minSource.end(),0);
  }
  int root(int n) {
    int r=n;
    while(parent[r]!=r) r=parent[r];
    while(parent[n]!=n) {
      int x=parent[n];
      parent[n]=r;
      n=x;
    }
    return r;
  }
  bool join(int a,int b) {
    a=root(a);b=root(b);
    if(a==b) return false;
    if(size[a]<size[b]) swap(a,b);
    parent[b]=a;
    size[a]+=size[b];
    minSource[a]=min(minSource[a],minSource[b]);
    seeded[a]|=seeded[b];
    return true;
  }
  void mark(int n) { seeded[root(n)]=1; }
};

static inline ull step(ull x,char system) {
  if(system=='S' && x==5) return 5;
  if(!(x&1ULL)) return x/2;
  __uint128_t next=3*(__uint128_t)x+(system=='G'?7:1);
  next/=2;
  if(next>numeric_limits<ull>::max())
    throw overflow_error("exact natural orbit outside UInt64 envelope");
  return (ull)next;
}

int main(int argc,char **argv) {
  if(argc<3) {
    cerr<<"Usage: v173 k T|G|S [labels.csv] [full-ledger.jsonl]\n";
    return 1;
  }
  const int k=atoi(argv[1]);
  const string mode=argv[2];
  if(k<6 || k>25 || (mode!="T" && mode!="G" && mode!="S")) return 2;
  const char system=mode[0];
  const int H=8*k,N=(1<<k)-1;
  Union classes(N);
  unordered_map<ull,ull> owner;
  owner.max_load_factor(.75);
  owner.reserve((size_t)N*2);

  ofstream labels,receipts;
  if(argc>=4 && string(argv[3])!="-") {
    labels.open(argv[3]);
    if(!labels) return 3;
  }
  if(argc>=5 && string(argv[4])!="-") {
    receipts.open(argv[4]);
    if(!receipts) return 4;
  }
  ull endpointChecks=0,dominatedStops=0,clockUpdates=0;
  ull endpointInsertions=0,effectiveJoins=0,terminalHits=0;
  const auto start=chrono::steady_clock::now();

  for(int n=1;n<=N;n++) {
    ull x=n;
    for(int i=0;i<=H;i++) {
      endpointChecks++;
      const bool isTerminal=
          system=='G' ? (x==7 || x==14) : (x==1 || x==2);
      if(isTerminal) {
        classes.mark(n);
        terminalHits++;
        if(receipts)
          receipts<<"{\"type\":\"terminal\",\"source\":"<<n
                  <<",\"clock\":"<<i<<",\"endpoint\":"<<x<<"}\n";
        break;
      }

      // Pack original source and real source clock into a single
      // exact integer. N < 2^25, H<=200; 12 clock bits suffice.
      const ull record=((ull)n<<12)|(ull)i;
      auto [it,inserted]=owner.try_emplace(x,record);
      if(inserted) {
        endpointInsertions++;
      } else {
        const int p=(int)(it->second>>12);
        const int j=(int)(it->second&4095);
        if(p<=0 || p>N || j>H) abort();
        if(p!=n && classes.join(n,p)) {
          effectiveJoins++;
          if(receipts)
            receipts<<"{\"type\":\"meet\",\"source\":"<<n
                    <<",\"clock\":"<<i
                    <<",\"other\":"<<p
                    <<",\"other_clock\":"<<j
                    <<",\"endpoint\":"<<x<<"}\n";
        }

        if(i>=j) {
          // Dominated source arrives later or at same clock:
          // the earlier owner's genuine suffix covers it.
          dominatedStops++;
          break;
        }

        // Genuine earlier time at the SAME actual endpoint.
        // Extend the explored future budget from this new owner.
        it->second=record;
        clockUpdates++;
      }
      if(i<H) x=step(x,system);
    }
  }


  struct V173Summary {
    ull sources=0;
    int components=0,largest=0,goodComponents=0;
    vector<pair<int,int>> unseeded; // (size, least original source)
  };
  auto summarize=[&]() -> V173Summary {
    V173Summary v;
    for(int n=1;n<=N;n++) {
      if(classes.parent[n]!=n) continue;
      if(classes.seeded[n]) {
        v.goodComponents++;
      } else {
        v.sources+=classes.size[n];
        v.components++;
        v.largest=max(v.largest,classes.size[n]);
        v.unseeded.push_back({classes.size[n],classes.minSource[n]});
      }
    }
    sort(v.unseeded.begin(),v.unseeded.end(),
         [](auto a,auto b) { return a.first!=b.first
            ? a.first>b.first : a.second<b.second; });
    return v;
  };
  const V173Summary initial=summarize();
  if(receipts)
    receipts<<"{\"type\":\"phase\",\"name\":\"initial_complete\"}\n";
  vector<pair<int,int>> pending=initial.unseeded;
  sort(pending.rbegin(),pending.rend()); // larger classes first, desc least-source ties
  const int V173MaxClock=500;
  ull extraSourceClocks=0,newJoins=0,newTerminalHits=0;
  int ownersAttempted=0,ownersClosed=0,ownersAlreadyClosed=0,cycles=0;
  int largestNewClock=0;
  struct V173Join {int source,clock,other,otherClock;ull endpoint;};
  vector<V173Join> added;
  vector<pair<int,int>> recordedCycles;
  for(auto [size,rep]:pending) {
    (void)size;
    if(classes.seeded[classes.root(rep)]) {
      ownersAlreadyClosed++;
      continue;
    }
    ownersAttempted++;
    ull x=(ull)rep;
    unordered_map<ull,int> seen;
    seen.reserve((size_t)V173MaxClock+5);
    // The original prefix 0..H is recomputed EXACTLY for this
    // original source, never lifted from another source's state.
    for(int t=0;t<=V173MaxClock;t++) {
      if(t>H) {
        extraSourceClocks++;
        largestNewClock=max(largestNewClock,t);
        const bool isTerminal=
          (system=='G')?(x==7||x==14):(x==1||x==2);
        if(isTerminal) {
          classes.mark(rep);
          newTerminalHits++;
          ownersClosed++;
          if(receipts)
            receipts<<"{\"type\":\"terminal\",\"phase\":\"adaptive\",\"source\":"
                    <<rep<<",\"clock\":"<<t<<",\"endpoint\":"<<x<<"}\n";
          break;
        }
        const ull record=((ull)rep<<12)|(ull)t;
        auto [it,inserted]=owner.try_emplace(x,record);
        if(!inserted) {
          const int p=(int)(it->second>>12);
          const int j=(int)(it->second&4095);
          if(p<=0 || p>N || j>V173MaxClock) abort();
          if(p!=rep && classes.join(rep,p)) {
            newJoins++;
            added.push_back({rep,t,p,j,x});
            if(receipts)
              receipts<<"{\"type\":\"meet\",\"phase\":\"adaptive\",\"source\":"
                      <<rep<<",\"clock\":"<<t<<",\"other\":"<<p
                      <<",\"other_clock\":"<<j<<",\"endpoint\":"<<x<<"}\n";
          }
          if(classes.seeded[classes.root(rep)]) {
            ownersClosed++;
            break;
          }
        }
      }
      // A repeated nonterminal endpoint is an actual periodicity
      // certificate for this synthetic/true map, NOT a terminal seed.
      auto [it,fresh]=seen.try_emplace(x,t);
      if(!fresh) {
        cycles++;
        recordedCycles.push_back({rep,t-it->second});
        if(receipts)
          receipts<<"{\"type\":\"cycle\",\"source\":"<<rep
                  <<",\"clock\":"<<t<<",\"earlier_clock\":"
                  <<it->second<<",\"endpoint\":"<<x<<"}\n";
        break;
      }
      if(t<V173MaxClock) x=step(x,system);
    }
  }

  ull unknownPopulation=0;
  int unknownClasses=0,largest=0,seededClasses=0;
  vector<pair<int,int>> unresolved;
  for(int n=1;n<=N;n++) {
    if(classes.parent[n]!=n) continue;
    if(classes.seeded[n]) {
      seededClasses++;
    } else {
      unknownClasses++;
      unknownPopulation+=classes.size[n];
      largest=max(largest,classes.size[n]);
      unresolved.push_back({classes.size[n],classes.minSource[n]});
    }
  }
  sort(unresolved.begin(),unresolved.end(),
       [](auto a,auto b) {
         if(a.first!=b.first) return a.first>b.first;
         return a.second<b.second;
       });

  if(labels) {
    labels<<"n,seeded,unseeded_min_source\n";
    for(int n=1;n<=N;n++) {
      int r=classes.root(n);
      labels<<n<<","<<(int)classes.seeded[r]<<","
            <<(classes.seeded[r] ? 0 : classes.minSource[r])<<"\n";
    }
  }

  const double seconds=chrono::duration<double>(
    chrono::steady_clock::now()-start).count();
  cout<<"{\"schema\":\"COLLATZ_V173_ADAPTIVE_COMPONENT_RECLOSURE\""
      <<",\"system\":\""<<(system=='T'?"TRUE_COLLATZ":
              system=='G'?"SYNTHETIC_3N7":"SYNTHETIC_ONE_ARROW")
      <<"\",\"k\":"<<k<<",\"H\":"<<H
      <<",\"owner_clock_cap\":"<<V173MaxClock
      <<",\"positive_sources\":"<<N
      <<",\"naive_full_source_clock_slots\":"
        <<((ull)N*(ull)(H+1))
      <<",\"initial_endpoint_examinations\":"<<endpointChecks
      <<",\"initial_effective_source_meetings\":"<<effectiveJoins
      <<",\"initial_direct_terminal_hits\":"<<terminalHits
      <<",\"initial_unseeded_sources\":"<<initial.sources
      <<",\"initial_unseeded_components\":"<<initial.components
      <<",\"initial_largest_unseeded_component\":"<<initial.largest
      <<",\"initial_seeded_components\":"<<initial.goodComponents
      <<",\"adaptive_owner_attempts\":"<<ownersAttempted
      <<",\"adaptive_owners_already_closed\":"<<ownersAlreadyClosed
      <<",\"adaptive_owners_closed\":"<<ownersClosed
      <<",\"adaptive_source_clock_steps\":"<<extraSourceClocks
      <<",\"adaptive_effective_mergers\":"<<newJoins
      <<",\"adaptive_direct_terminal_hits\":"<<newTerminalHits
      <<",\"adaptive_cycles_observed\":"<<cycles
      <<",\"adaptive_largest_examined_clock\":"<<largestNewClock
      <<",\"final_unseeded_sources\":"<<unknownPopulation
      <<",\"final_unseeded_components\":"<<unknownClasses
      <<",\"final_largest_unseeded_component\":"<<largest
      <<",\"final_seeded_components\":"<<seededClasses
      <<",\"seconds_measured\":"<<seconds
      <<",\"adaptive_join_receipts\":[";
  for(size_t z=0;z<added.size();z++) {
    if(z) cout<<",";
    const auto &e=added[z];
    cout<<"{\"source\":"<<e.source<<",\"clock\":"<<e.clock
        <<",\"other\":"<<e.other<<",\"other_clock\":"<<e.otherClock
        <<",\"endpoint\":"<<e.endpoint<<"}";
  }
  cout<<"],\"initial_top_components\":[";
  for(size_t z=0;z<min((size_t)12,initial.unseeded.size());z++) {
    if(z) cout<<",";
    cout<<"["<<initial.unseeded[z].second<<","<<initial.unseeded[z].first<<"]";
  }
  cout<<"],\"final_top_components\":[";
  for(size_t z=0;z<min((size_t)12,unresolved.size());z++) {
    if(z) cout<<",";
    cout<<"["<<unresolved[z].second<<","<<unresolved[z].first<<"]";
  }
  cout<<"],\"finite_only\":true,\"global_collatz\":\"UNKNOWN\",\"qed\":false}\n";
  return 0;
}
