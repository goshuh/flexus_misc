#include <fstream>
#include <list>
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>

#include <stdio.h>
#include <stdlib.h>

class VMA {
 public:
  unsigned long base, bound, attr;

  VMA(unsigned long base, unsigned long bound, unsigned long attr)
      : base(base),
        bound(bound),
        attr(attr) {
  }

  bool hit(unsigned long addr) const {
    return addr >= base && addr <= bound;
  }

  void str() const {
    printf("VMA(%lx, %lx, %lx)\n", base, bound, attr);
  }
};

class VLB {
 public:
  unsigned long base, bound, csid;
  bool glb;

  VLB(unsigned long base,
      unsigned long bound,
      unsigned long csid,
      unsigned long attr)
      : base(base),
        bound(bound),
        csid(csid),
        glb(!!(attr & 0x20)) {
  }

  bool hit(unsigned long addr, unsigned long csid) const {
    return addr >= base && addr <= bound && (glb || this->csid == csid);
  }

  void str() const {
    printf(
        "VLB(%lx, %lx, %lx, %s)\n",
        base,
        bound,
        csid,
        glb ? "true" : "false");
  }
};

static unsigned long to_int(const std::string &s) {
  return strtoul(s.c_str(), NULL, 16);
}

static unsigned long to_int(const std::string &s, int begin, int end) {
  return strtoul(
      s.substr(begin, s.length() - begin + end).c_str(),
      NULL,
      16);
}

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

class Run {
 public:
  std::vector<VMA> vmas;
  std::list<VLB> vlbs;
  unsigned long csid;
  const size_t lens = 4096;

  Run()
      : csid(0) {
  }

  bool handle_rst(const std::vector<std::string> &sp) {
    vmas.clear();

    return false;
  }

  bool handle_vma(const std::vector<std::string> &sp) {
    auto base = to_int(sp[3], 1, -1);
    auto bound = to_int(sp[4], 0, -1);
    auto offs = to_int(sp[5]);

    vmas.emplace_back(base, bound, offs);

    return false;
  }

  bool handle_pre(const std::vector<std::string> &sp) {
    auto base = to_int(sp[3], 1, -1);
    auto bound = to_int(sp[4], 0, -1);
    auto attr = to_int(sp[5]);
    auto ocid = to_int(sp[6]);

    for (const auto &v: vlbs)
      if (v.hit(base, ocid))
        return true;

    vlbs.emplace_back(base, bound, ocid, attr);
    return false;
  }

  bool handle_hit(const std::vector<std::string> &sp) {
    auto addr = to_int(sp[3].substr(2));

    for (auto i = vlbs.begin(); i != vlbs.end(); i++)
      if (i->hit(addr, csid)) {
        auto base = to_int(sp[4], 1, -1);
        auto bound = to_int(sp[5], 0, -1);

        if (i->base != base || i->bound != bound)
          return true;

        if (i != vlbs.begin()) {
          auto v = *i;

          vlbs.erase(i);
          vlbs.push_front(v);
        }

        return false;
      }

    return false;
  }

  bool handle_mis(const std::vector<std::string> &sp) {
#ifdef REAL
    auto addr = to_int(sp[3].substr(2));

    for (const auto &v: vlbs)
      if (v.hit(addr, csid))
        return true;
#endif

    return false;
  }

  bool handle_ev(const std::vector<std::string> &sp) {
    if (vlbs.empty())
      return true;

#ifdef REAL
    auto base = to_int(sp[4], 1, -1);
    auto csid = to_int(sp[7]);

    auto v = vlbs.begin();

    if (v->base != base || v->csid != csid)
      return true;

    vlbs.erase(v);
#endif

    return false;
  }

  bool handle_add(const std::vector<std::string> &sp) {
    auto addr = to_int(sp[3].substr(2));
    auto base = to_int(sp[4], 1, -1);
    auto bound = to_int(sp[5], 0, -1);
    auto attr = to_int(sp[6]);

#ifdef REAL
    if (vlbs.size() > lens)
      return true;

    for (const auto &v: vlbs)
      if (v.hit(addr, csid))
        return true;

    for (const auto &v: vlbs)
      if (v.hit(base, csid))
        return true;

    if (addr >= 0x2000000000) {
      for (const auto &v: vmas)
        if (v.hit(addr)) {
          if (v.base != base || v.bound != bound || v.attr != attr)
            return true;
          break;
        }
    }
#else
    for (const auto &v: vlbs)
      if (v.hit(addr, csid))
        return false;

    for (const auto &v: vlbs)
      if (v.hit(base, csid))
        return false;
#endif

    vlbs.emplace_front(base, bound, csid, attr);
    return false;
  }

  bool handle_clr(const std::vector<std::string> &sp) {
    auto base = to_int(sp[4], 1, -1);
    auto bound = to_int(sp[5], 0, -1);
    auto ocid = to_int(sp[7]);

    for (auto i = vlbs.begin(); i != vlbs.end(); i++)
      if (i->base == base && i->bound == bound && i->csid == ocid) {
        vlbs.erase(i);
        return false;
      }

    return true;
  }

  bool handle_inv(const std::vector<std::string> &sp) {
    auto base = to_int(sp[4], 1, -1);
    auto bound = to_int(sp[5], 0, -1);

    for (auto i = vlbs.begin(); i != vlbs.end(); i++)
      if (i->base == base && i->bound == bound) {
        vlbs.erase(i);
        return false;
      }

    return true;
  }

  bool handle_cid(const std::vector<std::string> &sp) {
    csid = to_int(sp[3]);

    return false;
  }

  void report() {
    std::unordered_map<unsigned long, std::unordered_set<unsigned long>> maps;

    for (const auto &v: vlbs)
      maps[v.csid].insert(v.base);

    printf("vlbs: %ld\n", vlbs.size());

    for (const auto &m: maps) {
      printf(" csid: %lx\n", m.first);

      for (const auto &s: m.second)
        printf("  %lx\n", s);
    }
  }
};

static void parse(const std::string &filename) {
  std::ifstream file(filename);
  if (!file.is_open())
    return;

  Run run;
  size_t nr = 0;

  std::string line;
  while (std::getline(file, line)) {
    auto sp = split(line, ' ');
    auto ch = false;

    if (sp.size() < 1)
      printf("%ld:%s\n", nr + 1, line.c_str());

    else if (sp[0].substr(0, 8) == "PageWalk") {
      if (sp.size() < 3)
        printf("%ld:%s\n", nr + 1, line.c_str());
      else if (sp[2] == "rst")
        ch = run.handle_rst(sp);
      else if (sp[2] == "vma")
        ch = run.handle_vma(sp);

    } else if (sp[0].substr(0, 7) == "MMUImpl") {
      if (sp.size() < 3)
        printf("%ld:%s\n", nr + 1, line.c_str());
      else if (sp[2] == "pre")
        ch = run.handle_pre(sp);
      else if (sp[2] == "hit")
        ch = run.handle_hit(sp);
      else if (sp[2] == "mis")
        ch = run.handle_mis(sp);
      else if (sp[2] == "ev")
        ch = run.handle_ev (sp);
      else if (sp[2] == "add")
        ch = run.handle_add(sp);
      else if (sp[2] == "clr")
        ch = run.handle_clr(sp);
      else if (sp[2] == "inv")
        ch = run.handle_inv(sp);
      else if (sp[2] == "cid")
        ch = run.handle_cid(sp);

    } else
      printf("%ld:%s\n", nr + 1, line.c_str());

    if (ch) {
      printf("%lu FAILED\n", nr + 1);
      break;
    }

    nr++;
  }

  run.report();
}

int main(int argc, char **argv) {
  for (int i = 1; i < argc; ++i)
    parse(argv[i]);

  return 0;
}