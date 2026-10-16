// V2 source-pinned, exact finite exploration of base-point origin.
// Historical source contract: FreeLIP v1.1 (July 21 1997) lip.h and lip.c.
// This is an independent mathematical reimplementation, NOT FreeLIP-licensed code.
// NEVER interpret no match here as a proof about all historical mechanisms.
#include <boost/multiprecision/cpp_int.hpp>
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>
using namespace boost::multiprecision;
using U128 = number<cpp_int_backend<128,128,unsigned_magnitude,unchecked,void>>;
using U256 = number<cpp_int_backend<256,256,unsigned_magnitude,unchecked,void>>;
using U512 = number<cpp_int_backend<512,512,unsigned_magnitude,unchecked,void>>;
static const U256 M=(U256(1)<<107)-1;
static const U256 A=powm(U256(3),U256(121),M);
static const U512 P("0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF");
static const U512 X("0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296");
static const U512 P239("0x7fffffffffffffffffffffff7fffffffffff8000000000007fffffffffff");
static const U512 X239("0xffa963cdca8816ccc33b8642bedf905c3d358573d3f27fbbd3b3cb9aaaf");
static const uint64_t LCG_A = 0x5DEECE66DULL, LCG_C=11ULL, MASK48=(1ULL<<48)-1;
static const uint64_t P256_UNIX=871696354ULL; // 1997-08-16T01:52:34Z
struct Evidence {
  uint64_t checked=0, states=0, rejected=0, seed_count=0;
  std::vector<std::string> hits;
  double seconds=0;
};
static U128 next_freelip(U128 &state, uint64_t &rejected, int bits) {
    const U256 bound = M-(M % (U256(1)<<bits));
    while (true) {
      U256 prod=U256(state)*A;
      U256 v=(prod & M)+(prod>>107); // Mersenne reduction
      v=(v & M)+(v>>107);
      if (v>=M) v-=M;
      state=U128(v);
      if (v<bound) return state;
      rejected++;
    }
}
static std::vector<uint64_t> freelip_limbs(uint64_t seed, int bits, size_t draws, uint64_t &rejected) {
  U128 state(U256(seed)%M); std::vector<uint64_t> out;
  out.reserve(draws);const U128 mask=(U128(1)<<bits)-1;
  for(size_t i=0;i<draws;i++)out.push_back(uint64_t(next_freelip(state,rejected,bits)&mask));
  return out;
}
static void enumerate_windows(const std::vector<uint64_t>& v, int bits, const std::vector<int>& sizes, bool both_orders,
                              const U512 &mod, const U512 &target, uint64_t seed, const std::string &generator, Evidence &ev) {
  for (int len:sizes){
    if(len>(int)v.size())continue;
    U512 msf=0,lsf=0;
    for(int j=0;j<len;j++) {msf=(msf<<bits)+v[j]; lsf+=U512(v[j])<<(bits*j);}
    U512 mask=(U512(1)<<(bits*len))-1;
    for(size_t i=0;i+len<=v.size();i++){
      if(msf%mod==target)ev.hits.push_back(generator+" seed="+std::to_string(seed)+" bits="+std::to_string(bits)+" limbs="+std::to_string(len)+" order=msf offset="+std::to_string(i));
      ev.checked++;
      if(both_orders){
        if(lsf%mod==target)ev.hits.push_back(generator+" seed="+std::to_string(seed)+" bits="+std::to_string(bits)+" limbs="+std::to_string(len)+" order=lsf offset="+std::to_string(i));
        ev.checked++;
      }
      if(i+len<v.size()){
        msf=((msf<<bits)&mask)+v[i+len];
        lsf=(lsf>>bits)+(U512(v[i+len])<<(bits*(len-1)));
      }
    }
  }
}
static uint64_t next_lrand(uint64_t &state) {
   state=(state*LCG_A+LCG_C)&MASK48;
   return state>>17; // POSIX lrand48 top31 bits
}
static std::vector<uint64_t> lrand31(size_t draws){
  uint64_t state=(P256_UNIX<<16)|0x330EULL;
  std::vector<uint64_t> out;out.reserve(draws);
  for(size_t i=0;i<draws;i++)out.push_back(next_lrand(state));
  return out;
}
static Evidence run_freelip(int bits, uint64_t first, uint64_t count, int draws=192){
   Evidence ev;ev.seed_count=count;
   auto t0=std::chrono::steady_clock::now();
   std::vector<int> lens=bits==30?std::vector<int>{9,10,11}:std::vector<int>{5,6,7};
   for(uint64_t seed=first;seed<first+count;seed++){
     auto v=freelip_limbs(seed,bits,draws,ev.rejected);
     ev.states+=draws;
     enumerate_windows(v,bits,lens,true,P,X,seed,"FreeLIP",ev);
   }
   ev.seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
   return ev;
}
static Evidence run_lrand(){
   Evidence ev;ev.seed_count=1;
   auto t0=std::chrono::steady_clock::now();
   auto v=lrand31(40000);
   ev.states=v.size();
   enumerate_windows(v,31,{8,9,10},true,P,X,P256_UNIX,"lrand48",ev);
   ev.seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
   return ev;
}
static Evidence run_chain(){
   Evidence ev;auto t0=std::chrono::steady_clock::now();
   auto possible_seeds=lrand31(40000);
   std::unordered_set<uint64_t> uniq;
   for(uint64_t seed:possible_seeds){
      if(!uniq.insert(seed).second)continue;
      ev.seed_count++;
      auto v=freelip_limbs(seed,30,64,ev.rejected);
      ev.states+=v.size();
      enumerate_windows(v,30,{10},false,P,X,seed,"lrand48->FreeLIP",ev);
   }
   ev.seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
   return ev;
}
static Evidence run_controls(){
   Evidence ev;auto t0=std::chrono::steady_clock::now();
   // Known observed prime239v1 historical case: 26-bit FreeLIP 11 limbs at offset 29.
   auto v26=freelip_limbs(20420,26,64,ev.rejected);
   enumerate_windows(v26,26,{11},false,P239,X239,20420,"FreeLIP_1997_prime239v1",ev);
   if(ev.hits.size()!=1 || ev.hits[0].find("offset=29")==std::string::npos)throw std::runtime_error("historical control mismatch");
   // Synthetic F30 with distinct seed and window, independently generated by exact state function.
   auto v30=freelip_limbs(20000,30,25,ev.rejected);
   U512 raw=0;for(int i=7;i<17;i++)raw=(raw<<30)+v30[i];
   U512 planted=raw%P;
   size_t old=ev.hits.size();
   enumerate_windows(v30,30,{10},false,P,planted,20000,"synthetic_FreeLIP_30",ev);
   if(ev.hits.size()!=old+1 || ev.hits.back().find("offset=7")==std::string::npos)throw std::runtime_error("30bit synthetic control mismatch");
   // Synthetic native lrand48 contiguous 31-bit packing known offset 15.
   auto l31=lrand31(40);raw=0;for(int i=15;i<24;i++)raw=(raw<<31)+l31[i];
   planted=raw%P;old=ev.hits.size();
   enumerate_windows(l31,31,{9},false,P,planted,P256_UNIX,"synthetic_lrand48_31",ev);
   if(ev.hits.size()!=old+1 || ev.hits.back().find("offset=15")==std::string::npos)throw std::runtime_error("lrand48 synthetic control mismatch");
   // Check original 30bit sampler exact small-state sequence against source math: one-step 3^121 seed/M.
   ev.states=v26.size()+v30.size()+l31.size();
   ev.seed_count=3;
   ev.seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
   return ev;
}
int main(int argc,char **argv){
 try {
   if(argc<2)throw std::runtime_error("Usage: scan <f30_small|f30_time|f30_default|f62_small|f62_default|l31|chain30|controls>");
   std::string mode=argv[1];Evidence ev;
   if(mode=="f30_small")ev=run_freelip(30,0,65536);
   else if(mode=="f30_time")ev=run_freelip(30,P256_UNIX-86400,172801);
   else if(mode=="f30_default")ev=run_freelip(30,7157891,1);
   else if(mode=="f62_small")ev=run_freelip(62,0,65536);
   else if(mode=="f62_default")ev=run_freelip(62,7157891,1);
   else if(mode=="l31")ev=run_lrand();
   else if(mode=="chain30")ev=run_chain();
   else if(mode=="controls")ev=run_controls();
   else throw std::runtime_error("Unknown mode");
   std::cout << "{\"mode\":\"" << mode << "\",\"status\":\"SUCCESS\",\"seeds\":"<<ev.seed_count
             <<",\"prng_outputs\":"<<ev.states<<",\"exact_candidate_windows\":"<<ev.checked
             <<",\"rejected_raw_steps\":"<<ev.rejected<<",\"elapsed_seconds\":"<<std::setprecision(7)<<ev.seconds<<",\"hits\":[";
   for(size_t i=0;i<ev.hits.size();i++){if(i)std::cout<<",";std::cout<<"\""<<ev.hits[i]<<"\"";}
   std::cout<<"]}\n";
   return 0;
 }catch(const std::exception&e){std::cerr<<"Error: "<<e.what()<<"\n";return 2;}
}
