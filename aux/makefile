.PHONY: clean

all: chk uat


chk: chk.cpp
	$(CXX) -O2 -Wall $^ -o $@

uat: uat.cpp
	$(CXX) -O2 -Wall $^ -o $@ -lboost_serialization -lboost_iostreams

clean:
	rm -rf chk uat
