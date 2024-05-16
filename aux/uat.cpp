#include <stdio.h>

#include <fstream>
#include <string>
#include <vector>

#include <boost/archive/binary_iarchive.hpp>

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

static int load_l1d(
    const std::string &file,
    uint64_t base,
    uint64_t bound,
    uint64_t shift) {
  std::ifstream ifs(file);

  if (!ifs.good())
    return -1;

  int ret = 0;

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
          auto addr = std::stoul(s, nullptr, 16) << shift;

          if (st && (addr >= base) && (addr < bound))
            ret++;
          break;
      }
    }
  }

  return ret;
}

struct Block {
  uint64_t tag;
  uint8_t state;

  friend class boost::serialization::access;

  template <class Archive>
  void serialize(Archive &ar, const uint32_t version) {
    ar &tag;
    ar &state;
  }
};

static int load_llc(
    const std::string &file,
    uint64_t base,
    uint64_t bound) {
  std::ifstream ifs(file);

  if (!ifs.good())
    return -1;

  boost::archive::binary_iarchive ia(ifs);

  uint64_t sets;
  uint64_t ways;

  ia >> sets;
  ia >> ways;

  int ret = 0;

  for (auto i = 0u; i < sets; i++) {
    for (auto j = 0u; j < ways; j++) {
      Block bs;

      ia >> bs;

      if ((bs.state != 'I') && (bs.tag >= base) && (bs.tag < bound))
        ret++;
    }
  }

  return ret;
}

int main(int argc, char **argv) {
  uint64_t base  = 0;
  uint64_t bound = 0;
  uint64_t shift = 0;

  if (argc > 2) {
    auto sp = split(argv[2], '-');

    if (sp.size() > 0)
      base  = std::stoul(sp[0], nullptr, 16);
    if (sp.size() > 1)
      bound = std::stoul(sp[1], nullptr, 16);
    if (sp.size() > 2)
      shift = std::stoul(sp[2], nullptr, 10);
  }

  base  = base  ?: 0x800000000lu;
  bound = bound ?: 0x803fffffflu;
  shift = shift ?: 12;

  std::string l1d(argv[1]);
  std::string llc(argv[1]);

  l1d.append("/sys-L1d");
  llc.append("/sys-L2-cache.gz");

  printf("l1d: %d\n", load_l1d(l1d, base, bound, shift));
  printf("llc: %d\n", load_llc(llc, base, bound));

  return 0;
}
