#include <bits/stdc++.h>
#include <boost/multiprecision/cpp_int.hpp>
using namespace std;
using boost::multiprecision::cpp_int;
using u64=uint64_t;
using u128=__uint128_t;

static inline u64 T(u64 x){
  if((x&1)==0) return x/2;
  u128 z=(u128)3*x+1;
  if(z>numeric_limits<u64>::max()){ cerr<<"overflow\n"; exit(3); }
  return (u64)(z/2);
}

int main(int argc,char**argv){
  u64 LIMIT=(1ULL<<24);
  unsigned H=1024;
  if(argc>1) LIMIT=strtoull(argv[1],nullptr,10);
  if(argc>2) H=(unsigned)strtoul(argv[2],nullptr,10);

  vector<unsigned> qmin(H+1);
  cpp_int p2=1,p3=1;
  unsigned qm=0;
  for(unsigned j=1;j<=H;j++){
    p2*=2;
    while(p3<p2){p3*=3;qm++;}
    qmin[j]=qm;
  }

  u64 tested=0,crossed=0,no_cross=0,highodd=0,highodd_direct_cross=0,highodd_hard_cross=0;
  unsigned max_cross_depth=0,max_highodd_wait=0;
  u64 max_cross_source=0;
  struct Row{u64 n;unsigned entry_k,entry_q,cross_k,cross_q;u64 entry_y,cross_y;};
  vector<Row> rows;
  vector<u64> unresolved;

  for(u64 n=2;n<LIMIT;n++){
    tested++;
    u64 y=n;
    unsigned q=0;
    bool entered=false;
    unsigned ek=0,eq=0;u64 ey=0;
    bool didcross=false;
    for(unsigned j=1;j<=H;j++){
      unsigned bit=(unsigned)(y&1);
      y=T(y); q+=bit;
      if(q<qmin[j]){
        crossed++; didcross=true;
        if(j>max_cross_depth){max_cross_depth=j;max_cross_source=n;}
        if(entered){
          highodd++;
          bool direct=y<n;
          if(direct) highodd_direct_cross++; else highodd_hard_cross++;
          max_highodd_wait=max(max_highodd_wait,j-ek);
          if(rows.size()<100 || !direct)
            rows.push_back({n,ek,eq,j,q,ey,y});
        }
        break;
      }
      if(!entered && q>=n){
        entered=true;ek=j;eq=q;ey=y;
      }
    }
    if(!didcross){
      no_cross++;
      if(unresolved.size()<20) unresolved.push_back(n);
      if(entered){
        highodd++;
        if(rows.size()<100) rows.push_back({n,ek,eq,0,q,ey,y});
      }
    }
  }

  cout<<"{\n";
  cout<<"  \"schema\":\"COLLATZ_HIGH_ODD_TOURNAMENT_V1\",\n";
  cout<<"  \"limit\":"<<LIMIT<<",\n";
  cout<<"  \"depth_cap\":"<<H<<",\n";
  cout<<"  \"sources_tested\":"<<tested<<",\n";
  cout<<"  \"first_crossing_found\":"<<crossed<<",\n";
  cout<<"  \"no_crossing_within_cap\":"<<no_cross<<",\n";
  cout<<"  \"high_odd_prefix_sources\":"<<highodd<<",\n";
  cout<<"  \"high_odd_then_direct_first_crossing\":"<<highodd_direct_cross<<",\n";
  cout<<"  \"high_odd_then_hard_first_crossing\":"<<highodd_hard_cross<<",\n";
  cout<<"  \"max_high_odd_wait_to_crossing\":"<<max_highodd_wait<<",\n";
  cout<<"  \"max_first_crossing_depth\":"<<max_cross_depth<<",\n";
  cout<<"  \"max_first_crossing_source\":"<<max_cross_source<<",\n";
  cout<<"  \"high_odd_rows\":[";
  for(size_t i=0;i<rows.size();i++){
    if(i) cout<<",";
    auto&r=rows[i];
    cout<<"{\"n\":"<<r.n<<",\"entry_k\":"<<r.entry_k<<",\"entry_q\":"<<r.entry_q
        <<",\"entry_y\":"<<r.entry_y<<",\"cross_k\":"<<r.cross_k<<",\"cross_q\":"<<r.cross_q
        <<",\"cross_y\":"<<r.cross_y<<"}";
  }
  cout<<"],\n";
  cout<<"  \"first_no_crossing\":[";
  for(size_t i=0;i<unresolved.size();i++){if(i)cout<<",";cout<<unresolved[i];}
  cout<<"],\n";
  cout<<"  \"bounded_conclusion\":\"exact census of coefficient-live prefixes entering q>=n; bounded only\",\n";
  cout<<"  \"universal_status\":\"UNKNOWN\",\n";
  cout<<"  \"global_collatz\":\"UNKNOWN\"\n";
  cout<<"}\n";
  return 0;
}
