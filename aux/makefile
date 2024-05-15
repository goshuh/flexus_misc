.PHONY: clean

all: chk uat


chk: chk.cpp
	$(CXX) -O2 -Wall $^ -o $@

uat: uat.cpp
	$(CXX) -O2 -Wall $^ -o $@ -lboost_serialization

clean:
	rm -rf chk uat
