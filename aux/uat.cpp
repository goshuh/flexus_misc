#include <stdio.h>

#include <fstream>
#include <string>
#include <vector>

#include <boost/archive/binary_iarchive.hpp>
#include <boost/iostreams/categories.hpp>
#include <boost/iostreams/filtering_stream.hpp>
#include <boost/iostreams/filter/gzip.hpp>

#define PL_BASE  0x800000000lu
#define PL_BOUND 0x803fffffflu
#define BT_BASE  0x808000000lu
#define BT_BOUND 0x80bfffffflu

static std::vector<std::string> split(
    const std::string &str,
    char delim) {
  size_t old = 0;
  size_t pos;

  std::vector<std::string> sp;

  while ((pos = str.find(delim, old)) != std::string::npos) {
    if (old < pos)
      sp.emplace_back(str.substr(old, pos - old));

    old = pos + 1;
  }

  if (old < str.length())
    sp.emplace_back(str.substr(old));

  return sp;
}

static void load_l1d(const std::string &file) {
  std::ifstream ifs(file);

  if (!ifs.good())
    return;

  int pl = 0;
  int bt = 0;

  std::string str;

  while (std::getline(ifs, str)) {
    auto sp = split(str, ' ');
    auto sn = 0;
    auto st = 0;

    for (const auto& s: sp) {
      if (s.length() == 0)
        continue;

      if (s[0] == '<')
        break;

      if (s[0] == ']') {
        sn = 1;
        continue;
      }

      sn++;

      switch (sn) {
        case 2:
          st = std::stoi(s);
          break;
        case 3:
          auto addr = std::stoul(s, nullptr, 16) << 8;

          if (st) {
            if ((addr >= PL_BASE) & (addr < PL_BOUND))
              pl++;
            if ((addr >= BT_BASE) & (addr < BT_BOUND))
              bt++;
          }
          break;
      }
    }
  }

  printf("l1d: %d %d\n", pl, bt);
}

static void load_llc(const std::string &file) {
  std::ifstream ifs(file, std::ios::binary);

  if (!ifs.good())
    return;

  boost::iostreams::filtering_stream<boost::iostreams::input> in;

  in.push(boost::iostreams::gzip_decompressor());
  in.push(ifs);

  boost::archive::binary_iarchive ia(in);

  uint64_t sets;
  uint64_t ways;

  ia >> sets;
  ia >> ways;

  int pl = 0;
  int bt = 0;

  // i have no idea wtf is this
  uint8_t pad;

  ia >> pad;

  for (auto i = 0u; i < sets; i++) {
    for (auto j = 0u; j < ways; j++) {
      uint64_t tag;
      uint8_t state;

      ia >> tag;
      ia >> state;

      if (state != 'I') {
        if ((tag >= PL_BASE) & (tag < PL_BOUND))
          pl++;
        if ((tag >= BT_BASE) & (tag < BT_BOUND))
          bt++;
      }
    }
  }

  printf("llc: %d %d\n", pl, bt);
}

int main(int argc, char **argv) {
  std::string l1d(argv[1]);
  std::string llc(argv[1]);

  l1d.append("/sys-L1d");
  llc.append("/sys-L2-cache.gz");

  load_l1d(l1d);
  load_llc(llc);

  return 0;
}
