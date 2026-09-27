#include <bits/stdc++.h>
using namespace std;
struct Own { uint32_t src; uint32_t dep; };
static inline uint64_t T(uint64_t x){ return (x&1)?(3*x+1)/2:x/2; }
int main(){
  const uint32_t LIMIT=13421671;
  vector<uint32_t> targets={8088063,13421671};
  unordered_map<uint64_t,Own> owner;
  owner.reserve(28000000);
  owner.max_load_factor(0.82);
  owner[1]={1,0}; owner[2]={1,1};
  map<uint32_t, tuple<uint32_t,uint64_t,uint32_t,uint32_t>> out;
  uint64_t maxState=2;
  vector<uint64_t> path; path.reserve(2048);
  for(uint32_t n=2;n<=LIMIT;n++){
    uint64_t x=n; path.clear(); uint32_t a=0;
    auto it=owner.find(x);
    while(it==owner.end()){
      path.push_back(x); maxState=max(maxState,x); x=T(x); a++;
      if(a>10000){ cerr<<"cap "<<n<<"\n"; return 2; }
      it=owner.find(x);
    }
    Own o=it->second;
    if(!(o.src<n)){ cerr<<"bad owner "<<n<<" "<<o.src<<"\n"; return 3; }
    if(binary_search(targets.begin(),targets.end(),n))
      out[n]=make_tuple(a,x,o.src,o.dep);
    for(uint32_t d=0;d<path.size();d++) owner.emplace(path[d],Own{n,d});
    if((n%1000000)==0) cerr<<"n="<<n<<" owners="<<owner.size()<<"\n";
  }
  cout<<"{\n  \"schema\":\"COLLATZ_COALESCENCE_OWNER_RESIDUAL_V1\",\n";
  cout<<"  \"processed_through\":"<<LIMIT<<",\n  \"owner_states\":"<<owner.size()<<",\n";
  cout<<"  \"max_state\":\""<<maxState<<"\",\n  \"targets\":[\n";
  for(size_t i=0;i<targets.size();i++){
    auto n=targets[i]; auto [a,y,p,b]=out[n];
    // replay certificate
    uint64_t xn=n,xp=p; for(uint32_t z=0;z<a;z++) xn=T(xn); for(uint32_t z=0;z<b;z++) xp=T(xp);
    if(xn!=y||xp!=y||!(p<n)) return 4;
    cout<<"    {\"n\":"<<n<<",\"coalescence_depth\":"<<a<<",\"meeting\":"<<y
        <<",\"p\":"<<p<<",\"p_depth\":"<<b<<",\"first_crossing\":"<<c.k
        <<",\"cross_endpoint\":"<<c.y<<",\"before_crossing\":"<<(a<c.k?"true":"false")<<"}";
    if(i+1<targets.size()) cout<<",";
    cout<<"\n";
  }
  cout<<"  ],\n  \"status\":\"EXACT_BOUNDED_OWNER_CENSUS\",\n";
  cout<<"  \"question\":\"does full source-order coalescence add a pre-crossing constructor beyond monotone Q18 on the exact residual record setters?\",\n";
  cout<<"  \"global_collatz\":\"UNKNOWN\"\n}\n";
}
