#define main original_direct_main
#include "collatz_direct_zero_tail_big.cpp"
#undef main

int main(int argc, char** argv) {
  if (argc != 2) return 2;
  const int K = std::stoi(argv[1]);
  if (K < 1 || K > 24) return 2;
  std::vector<i128> p3(K+2,1);
  for (int i=1; i<K+2; ++i) p3[i]=mulc(p3[i-1],3);
  const auto rows=build(K,p3);
  const std::map<int,uint64_t> frozen{{12,144},{16,1363},{20,15870},{24,172868}};
  if (auto it=frozen.find(K); it!=frozen.end() && rows.size()!=it->second) return 10;
  std::cout << "K,b,d,c,L\n";
  for (const auto& s: rows)
    std::cout << K << ',' << s.b << ',' << s.d << ',' << s.c << ',' << s.L << '\n';
}
