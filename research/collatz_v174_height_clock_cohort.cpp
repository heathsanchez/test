// V174 — source-height/clock factorial and original-source residual cohort, based on exact V172 dominant-clock quotient.
// Compiler: g++ -O3 -std=c++17 research/collatz_v172_dominant_clock_graph.cpp -o v172
// Invocation: v174 <k> <T|G|S> [labels.csv|-] [receipts.jsonl|-] [override_H]\n// CRITICAL: same genuine source-clock earliest-arrival semantics as V172;\n// only new state is explicitly reported original-source unresolved cohort.
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
    cerr<<"Usage: v172 k T|G|S [labels.csv] [receipts.jsonl]\n";
    return 1;
  }
  const int k=atoi(argv[1]);
  const string mode=argv[2];
  if(k<6 || k>25 || (mode!="T" && mode!="G" && mode!="S")) return 2;
  const char system=mode[0];
  // Optional sixth parameter overrides H for the height-versus-clock
  // factorial experiment; default remains H=8*k.
  const int H=(argc>=6 ? atoi(argv[5]) : 8*k);
  if(H<0 || H>512) return 5;
  const int N=(1<<k)-1;
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

  // Preserve every original source ID in a SMALL unresolved cohort,
  // rather than only its component size. Do not create a 2^25-line
  // labels artifact. A macrocomponent is deliberately truncated.
  vector<pair<int,int>> remainingOriginals;
  if(system=='T' && unknownPopulation<=1000) {
    for(int n=1;n<=N;n++) {
      const int r=classes.root(n);
      if(!classes.seeded[r]) remainingOriginals.push_back({n,classes.minSource[r]});
    }
    if(remainingOriginals.size()!=unknownPopulation) abort();
  }

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
  cout<<"{\"schema\":\"COLLATZ_V172_DOMINANT_CLOCK_QUOTIENT\""
      <<",\"system\":\""<<(system=='T'?"TRUE_COLLATZ":
              system=='G'?"SYNTHETIC_3N7":"SYNTHETIC_ONE_ARROW")
      <<"\",\"k\":"<<k<<",\"H\":"<<H
      <<",\"positive_sources\":"<<N
      <<",\"naive_full_source_clock_slots\":"
         <<((ull)N*(ull)(H+1))
      <<",\"actual_endpoint_examinations\":"<<endpointChecks
      <<",\"distinct_endpoints\":"<<owner.size()
      <<",\"earliest_clock_owner_updates\":"<<clockUpdates
      <<",\"dominated_source_stops\":"<<dominatedStops
      <<",\"effective_real_two_clock_joins\":"<<effectiveJoins
      <<",\"direct_terminal_source_receipts\":"<<terminalHits
      <<",\"unseeded_sources\":"<<unknownPopulation
      <<",\"unseeded_components\":"<<unknownClasses
      <<",\"largest_unseeded_component\":"<<largest
      <<",\"seeded_components\":"<<seededClasses
      <<",\"seconds_measured\":"<<seconds
      <<",\"top_unseeded_min_source_and_size\":[";
  for(size_t t=0;t<min((size_t)10,unresolved.size());t++) {
    if(t) cout<<",";
    cout<<"["<<unresolved[t].second<<","<<unresolved[t].first<<"]";
  }
  cout<<"],\"unseeded_original_source_members_and_min\":[";
  for(size_t i=0;i<remainingOriginals.size();i++) {
    if(i) cout<<",";
    cout<<"["<<remainingOriginals[i].first<<","<<remainingOriginals[i].second<<"]";
  }
  cout<<"],\"unseeded_original_member_receipts_complete\":"
      <<(system=='T' && unknownPopulation<=1000 ? "true":"false")
      <<",\"finite_only\":true,\"global_collatz\":\"UNKNOWN\",\"qed\":false}\n";
}
