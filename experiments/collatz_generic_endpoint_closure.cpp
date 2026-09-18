#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <stdexcept>

static inline uint64_t T(uint64_t n) {
    return (n & 1ULL) ? (3ULL*n + 1ULL)/2ULL : n/2ULL;
}

int main(int argc,char**argv){
    if(argc!=4){
        std::cerr<<"usage: closure X STEPS Z\n";
        return 2;
    }
    uint64_t X=std::strtoull(argv[1],nullptr,10);
    uint64_t STEPS=std::strtoull(argv[2],nullptr,10);
    uint64_t Z=std::strtoull(argv[3],nullptr,10);

    uint64_t y=X;
    for(uint64_t i=0;i<STEPS;i++) y=T(y);
    if(y!=Z){
        std::cerr<<"tail mismatch "<<X<<" "<<STEPS<<" "<<y<<" != "<<Z<<"\n";
        return 3;
    }

    uint64_t max_steps=0,argmax=0,max_peak=0;
    for(uint64_t n=2;n<=Z;n++){
        uint64_t v=n,peak=n,steps=0;
        while(v>=n){
            v=T(v);
            if(v>peak) peak=v;
            if(++steps>10000){
                std::cerr<<"first-descent guard "<<n<<" "<<v<<"\n";
                return 4;
            }
        }
        if(steps>max_steps){
            max_steps=steps;argmax=n;max_peak=peak;
        }
    }

    std::cout<<"ENDPOINT "<<X<<"\n";
    std::cout<<"TAIL_STEPS "<<STEPS<<"\n";
    std::cout<<"TAIL_VALUE "<<Z<<"\n";
    std::cout<<"FINITE_BASE_CASES "<<(Z-1)<<"\n";
    std::cout<<"MAX_FIRST_DESCENT_STEPS "<<max_steps<<"\n";
    std::cout<<"ARGMAX "<<argmax<<"\n";
    std::cout<<"ARGMAX_PEAK "<<max_peak<<"\n";
    std::cout<<"PASS_GENERIC_ENDPOINT_LOWER_MERGE_CLOSURE\n";
    return 0;
}
