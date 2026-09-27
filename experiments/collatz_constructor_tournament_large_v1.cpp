#include <bits/stdc++.h>
using namespace std;
using u64 = uint64_t;
using u128 = __uint128_t;

static inline u64 T(u64 x) {
  if ((x & 1) == 0) return x/2;
  u128 z = (u128)3*x + 1;
  if (z > numeric_limits<u64>::max()) {
    cerr << "overflow\n";
    exit(3);
  }
  return (u64)(z/2);
}

static string u128s(u128 x) {
  if (!x) return "0";
  string s;
  while (x) { s.push_back(char('0'+x%10)); x/=10; }
  reverse(s.begin(),s.end()); return s;
}

int main(int argc,char**argv){
  u64 LIMIT = (1ULL<<26);
  uint32_t CAP = 4096;
  if (argc>1) LIMIT=strtoull(argv[1],nullptr,10);
  if (argc>2) CAP=(uint32_t)strtoul(argv[2],nullptr,10);

  u64 tested=0, unresolved=0, record_y=0, record_p=0, max_peak_y=0;
  uint32_t record_steps=0;
  u128 total_steps=0;
  vector<tuple<u64,uint32_t,u64>> records;
  vector<u64> first_unresolved;

  for(u64 y=7; y<LIMIT; y+=12){
    tested++;
    u64 x=y, peak=y;
    bool hit=false;
    for(uint32_t a=1;a<=CAP;a++){
      x=T(x);
      peak=max(peak,x);
      total_steps++;
      // exact p <= 3y/4 test, cross-multiplied.
      if ((u128)4*x <= (u128)3*y){
        hit=true;
        if(a>record_steps){
          record_steps=a; record_y=y; record_p=x; max_peak_y=peak;
          records.emplace_back(y,a,x);
        }
        break;
      }
    }
    if(!hit){
      unresolved++;
      if(first_unresolved.size()<20) first_unresolved.push_back(y);
    }
  }

  // independent replay of the record certificate.
  u64 z=record_y;
  for(uint32_t i=0;i<record_steps;i++) z=T(z);
  if(z!=record_p || (u128)4*record_p>(u128)3*record_y) return 4;

  cout<<"{\n";
  cout<<"  \"schema\":\"COLLATZ_CONSTRUCTOR_TOURNAMENT_LARGE_V1\",\n";
  cout<<"  \"domain\":\"all positive y < limit with y mod 12 = 7\",\n";
  cout<<"  \"limit\":"<<LIMIT<<",\n";
  cout<<"  \"step_cap\":"<<CAP<<",\n";
  cout<<"  \"tested\":"<<tested<<",\n";
  cout<<"  \"unresolved\":"<<unresolved<<",\n";
  cout<<"  \"record_steps\":"<<record_steps<<",\n";
  cout<<"  \"record_y\":"<<record_y<<",\n";
  cout<<"  \"record_future\":"<<record_p<<",\n";
  cout<<"  \"record_peak\":"<<max_peak_y<<",\n";
  cout<<"  \"total_shortcut_steps\":\""<<u128s(total_steps)<<"\",\n";
  cout<<"  \"first_unresolved\":[";
  for(size_t i=0;i<first_unresolved.size();i++){if(i)cout<<",";cout<<first_unresolved[i];}
  cout<<"],\n";
  cout<<"  \"record_history\":[";
  for(size_t i=0;i<records.size();i++){
    auto [y,a,p]=records[i];
    if(i)cout<<",";
    cout<<"{\"y\":"<<y<<",\"steps\":"<<a<<",\"future\":"<<p<<"}";
  }
  cout<<"],\n";
  cout<<"  \"bounded_conclusion\":\"every tested 7 mod 12 endpoint has an exact future p with 4p <= 3y\",\n";
  cout<<"  \"universal_status\":\"UNKNOWN\",\n";
  cout<<"  \"global_collatz\":\"UNKNOWN\"\n";
  cout<<"}\n";
  return unresolved?2:0;
}
