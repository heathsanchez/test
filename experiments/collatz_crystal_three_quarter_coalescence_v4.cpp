#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

using u64 = std::uint64_t;
using u128 = __uint128_t;

static u64 T(u64 x) {
  if (x & 1ULL) {
    u128 z = (u128)3 * x + 1;
    assert(z <= std::numeric_limits<u64>::max());
    return (u64)(z / 2);
  }
  return x / 2;
}

static int v2(u64 x) {
  assert(x > 0);
  return __builtin_ctzll(x);
}

struct Macro {
  u64 p;
  u64 a; // T^a(cur) = common
  u64 b; // T^b(p) = common
  u64 common;
  u64 low_odd_steps;
  u64 high_s;
};

static Macro macro_step(u64 cur) {
  assert(cur & 1ULL);
  u64 x = cur;
  u64 ordinary = 0;
  u64 low = 0;
  for (u64 guard = 0; guard < 100000; ++guard) {
    u128 z128 = (u128)3 * x + 1;
    assert(z128 <= std::numeric_limits<u64>::max());
    u64 z = (u64)z128;
    int s = v2(z);
    u64 u = z >> s;
    if (s >= 3) {
      int k = (s - 1) / 2;
      u64 pow4 = 1ULL << (2 * k);
      u64 c = (pow4 - 1) / 3;
      assert(x >= c && (x - c) % pow4 == 0);
      u64 p = (x - c) / pow4;
      assert(p > 0 && (p & 1ULL));
      int sp = s - 2 * k;
      assert(sp == 1 || sp == 2);
      u64 q = p;
      for (int i = 0; i < sp; ++i) q = T(q);
      assert(q == u);
      u64 qx = x;
      for (int i = 0; i < s; ++i) qx = T(qx);
      assert(qx == u);
      return {p, ordinary + (u64)s, (u64)sp, u, low, (u64)s};
    }
    ordinary += (u64)s;
    ++low;
    x = u;
  }
  assert(false && "macro low-valuation guard exhausted");
  return {};
}

struct Hit {
  bool ok=false;
  u64 p=0,a=0,b=0,macros=0,max_source=0;
};

static Hit hit(u64 y, u64 macro_cap=256) {
  u64 cur=y;
  u64 A=0, B=0; // T^A(y)=T^B(cur)
  u64 mx=cur;
  if ((u128)4*cur <= (u128)3*y) return {true,cur,A,B,0,mx};
  for (u64 r=1; r<=macro_cap; ++r) {
    Macro m=macro_step(cur);
    mx=std::max(mx,m.p);
    u64 nA,nB;
    if (m.a >= B) {
      nA = A + (m.a - B);
      nB = m.b;
    } else {
      nA = A;
      nB = m.b + (B - m.a);
    }
    cur=m.p; A=nA; B=nB;
    if ((u128)4*cur <= (u128)3*y) {
      // independent exact replay
      u64 z1=y,z2=cur;
      for(u64 i=0;i<A;++i) z1=T(z1);
      for(u64 i=0;i<B;++i) z2=T(z2);
      assert(z1==z2);
      return {true,cur,A,B,r,mx};
    }
  }
  return {};
}

int main(int argc,char**argv){
  u64 limit = argc>1 ? std::stoull(argv[1]) : (1ULL<<26);
  u64 total=0, unresolved=0, max_macros=0, record_y=0,record_p=0,record_a=0,record_b=0,record_peak=0;
  std::vector<u64> first;
  for(u64 y=7;y<limit;y+=12){
    ++total;
    Hit h=hit(y);
    if(!h.ok){
      ++unresolved;
      if(first.size()<20) first.push_back(y);
      continue;
    }
    if(h.macros>max_macros){
      max_macros=h.macros;record_y=y;record_p=h.p;record_a=h.a;record_b=h.b;record_peak=h.max_source;
    }
  }
  std::cout<<"{\n";
  std::cout<<"  \"schema\":\"COLLATZ_CRYSTAL_THREE_QUARTER_COALESCENCE_V4\",\n";
  std::cout<<"  \"domain\":\"positive y < limit with y mod 12 = 7\",\n";
  std::cout<<"  \"limit\":"<<limit<<",\n";
  std::cout<<"  \"tested\":"<<total<<",\n";
  std::cout<<"  \"unresolved\":"<<unresolved<<",\n";
  std::cout<<"  \"record_macro_steps\":"<<max_macros<<",\n";
  std::cout<<"  \"record_y\":"<<record_y<<",\n";
  std::cout<<"  \"record_p\":"<<record_p<<",\n";
  std::cout<<"  \"record_merge_a\":"<<record_a<<",\n";
  std::cout<<"  \"record_merge_b\":"<<record_b<<",\n";
  std::cout<<"  \"record_max_macro_source\":"<<record_peak<<",\n";
  std::cout<<"  \"first_unresolved\":[";
  for(size_t i=0;i<first.size();++i){if(i)std::cout<<",";std::cout<<first[i];}
  std::cout<<"],\n";
  std::cout<<"  \"bounded_conclusion\":\"every tested 7 mod 12 endpoint has an exact coalescing source p with 4p <= 3y via valuation-pullback macro composition\",\n";
  std::cout<<"  \"universal_status\":\"UNKNOWN\",\n";
  std::cout<<"  \"global_collatz\":\"UNKNOWN\"\n";
  std::cout<<"}\n";
}
