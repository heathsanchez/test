// P-256 base-point FreeLIP bounded search; uses exact integer operations only.
// No general nonexistence or historical-provenance claim follows from no match.
#include <boost/multiprecision/cpp_int.hpp>
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>
using namespace boost::multiprecision;
using u128 = number<cpp_int_backend<128,128,unsigned_magnitude,unchecked,void>>;
using u256 = number<cpp_int_backend<256,256,unsigned_magnitude,unchecked,void>>;
using u320 = number<cpp_int_backend<320,320,unsigned_magnitude,unchecked,void>>;

int main(int argc, char **argv) {
    uint32_t max_seed = argc>=2 ? (uint32_t)std::stoul(argv[1]) : 65536;
    uint64_t seed_start = argc>=5 ? std::stoull(argv[4]) : 0;
    int draws = argc>=3 ? std::stoi(argv[2]) : 192;
    if (max_seed > 1048576 || draws < 12 || draws > 8192) { std::cerr << "invalid bounds\n"; return 2; }
    const u256 MOD = (u256(1)<<107)-1;
    const u256 AA = powm(u256(3),u256(121),MOD);
    const u320 P = argc>=6 ? u320(std::string(argv[5])) : u320("0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF");
    const u320 TARGET = argc>=4 ? u320(std::string(argv[3])) : u320("0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296");
    const u320 MASK26 = (u320(1)<<26)-1;
    std::array<int,2> lengths={10,11};
    std::array<std::string,2> modes={"low26", "high26"};
    std::array<std::string,2> orders={"msf", "lsf"};
    uint64_t checked=0;
    std::array<uint64_t,8> shapes{};
    std::vector<std::string> hits;
    auto t0=std::chrono::steady_clock::now();
    std::vector<uint32_t> low(draws),high(draws);
    for (uint32_t index=0;index<max_seed;index++) {
        uint64_t seed=seed_start+index;
        u128 state(seed);
        for(int j=0;j<draws;j++){
            u256 prod=u256(state)*AA;
            u256 s=(prod & MOD) + (prod>>107);
            s=(s & MOD)+(s>>107);
            if(s>=MOD) s-=MOD;
            state=u128(s);
            low[j]= (uint32_t)(state & u128((1<<26)-1));
            high[j]= (uint32_t)(state>>81);
        }
        for(int mode=0;mode<2;mode++){
            const std::vector<uint32_t>& v=mode==0?low:high;
            for(int li=0;li<2;li++){
                int L=lengths[li];
                u320 vm=0,vl=0;
                for(int j=0;j<L;j++){
                    vm=(vm<<26)|v[j];
                    vl |= u320(v[j])<<(26*j);
                }
                const u320 mask=(u320(1)<<(26*L))-1;
                const int n=draws-L+1;
                for(int j=0;j<n;j++){
                    // The exact candidate is obtained by reducing each 10- or 11-limb
                    // integer modulo the NIST prime; checks both limb endiannesses.
                    if(vm % P == TARGET){
                        hits.push_back(std::to_string(seed)+" "+modes[mode]+" "+std::to_string(L)+" msf "+std::to_string(j));
                    }
                    if(vl % P == TARGET){
                        hits.push_back(std::to_string(seed)+" "+modes[mode]+" "+std::to_string(L)+" lsf "+std::to_string(j));
                    }
                    shapes[mode*4+li*2]+=1;
                    shapes[mode*4+li*2+1]+=1;
                    checked+=2;
                    if(j+L<draws){
                        vm=((vm<<26)&mask)|v[j+L];
                        vl=(vl>>26)|(u320(v[j+L])<<(26*(L-1)));
                    }
                }
            }
        }
    }
    auto t1=std::chrono::steady_clock::now();
    std::chrono::duration<double> elapsed=t1-t0;
    std::cout << "{\"seed_count\":" << max_seed << ",\"seed_start\":" << seed_start << ",\"seed_end_inclusive\":" << (seed_start+max_seed-1) << ",\"first_prng_outputs\":" << draws
              << ",\"checked_windows\":" << checked << ",\"elapsed_seconds\":" << std::setprecision(7) << elapsed.count()
              << ",\"hits\":[";
    for(size_t j=0;j<hits.size();j++){
        if(j)std::cout<<",";
        std::cout<<"\""<<hits[j]<<"\"";
    }
    std::cout << "],\"shape_counts\":[";
    for(size_t j=0;j<shapes.size();j++){if(j)std::cout<<",";std::cout<<shapes[j];}
    std::cout << "]}\n";
    return 0;
}
