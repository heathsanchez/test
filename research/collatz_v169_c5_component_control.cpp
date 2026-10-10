// V169 C5 non-gcd basin countercontrol. BOUNDED EXACT only; NOT Collatz.
#include <bits/stdc++.h>
using namespace std;
using ull=unsigned long long;
static ull T5(ull x) {
  if (!(x & 1ULL)) return x/2;
  __uint128_t y=(__uint128_t)x*3+5;
  if (y/2>ULLONG_MAX) throw overflow_error("T5 overflow");
  return (ull)(y/2);
}
struct UF {
 vector<int> parent,sz;
 vector<unsigned char> seeded;
 UF(int N):parent(N+1),sz(N+1,1),seeded(N+1,0) {
   iota(parent.begin(),parent.end(),0);
 }
 int root(int n) {
   while(parent[n]!=n) {parent[n]=parent[parent[n]];n=parent[n];}
   return n;
 }
 void join(int a,int b) {
   a=root(a);b=root(b); if(a==b)return;
   if(sz[a]<sz[b])swap(a,b);
   parent[b]=a;sz[a]+=sz[b];seeded[a]|=seeded[b];
 }
 bool good(int n){return seeded[root(n)]!=0;}
 void mark(int n){seeded[root(n)]=1;}
};
int main(int argc,char**argv) {
 if(argc!=3) {cerr<<"usage: c5-component <k> <H>\n"; return 2;}
 int k=atoi(argv[1]),H=atoi(argv[2]);
 if(k<6||k>22||H<0||H>512)return 2;
 int N=(1<<k)-1;
 // Exact authentic positive 3-cycle: 1 -> 4 -> 2 -> 1.
 if(T5(1)!=4||T5(4)!=2||T5(2)!=1)abort();
 UF d(N);
 d.join(1,4);d.join(1,2);d.mark(1);
 unordered_map<ull,int> owner;owner.reserve((size_t)N*2);
 owner.max_load_factor(.8f);
 long long clocks=0,joins=0,terminal=0;
 for(int n=1;n<=N;n++) {
   ull x=(ull)n;
   for(int j=0;j<=H;j++) {
     clocks++;
     if(x==1||x==2||x==4) {
       d.join(n,(int)x);d.mark(n);terminal++;break;
     }
     auto it=owner.emplace(x,n);
     if(!it.second) {
       int a=d.root(n),b=d.root(it.first->second);
       if(a!=b){d.join(a,b);joins++;}
       if(d.good(n))break;
     }
     if(j<H)x=T5(x);
   }
 }
 long long badMass=0;
 vector<pair<int,int>> sizes;
 for(int n=1;n<=N;n++) {
   if(d.root(n)==n&&!d.seeded[n]) {
     sizes.emplace_back(d.sz[n],n);badMass+=d.sz[n];
   }
 }
 sort(sizes.rbegin(),sizes.rend());
 cout<<"{\"schema\":\"COLLATZ_V169_G5_NON_GCD_COMPONENT_CONTROL\""
     <<",\"k\":"<<k<<",\"H\":"<<H<<",\"positive_sources\":"<<N
     <<",\"unseeded_sources\":"<<badMass
     <<",\"unseeded_components\":"<<sizes.size()
     <<",\"max_unseeded_component\":"<<(sizes.empty()?0:sizes.front().first)
     <<",\"two_clock_mergers\":"<<joins<<",\"clock_checks\":"<<clocks
     <<",\"root_cycle\":[1,4,2]"
     <<",\"top_source_components\":[";
 for(size_t i=0;i<sizes.size()&&i<8;i++) {
   if(i)cout<<",";
   cout<<"["<<sizes[i].second<<","<<sizes[i].first<<"]";
 }
 cout<<"],\"global_collatz\":\"UNKNOWN\",\"qed\":false}\n";
}
