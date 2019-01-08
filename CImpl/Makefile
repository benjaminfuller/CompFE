CC = cc
CFLAGS = -g -w -std=gnu99 $(pkg-config --cflags libsodium)
LDFLAGS=  $(pkg-config --libs libsodium pthread)


all: main FuzzyExtractor

main:  FuzzyPack.o FuzzyExtractor.o FECommon.o FEGen.o FERep.o
	$(CC)  $^ -o $@ $(LDFLAGS) -lsodium -lpthread -lm

FuzzyPackTesting: FuzzyPack.o FuzzyExtractor.o FECommon.o FEGen.o FERep.o
	$(CC)  $^ -o $@ $(LDFLAGS) -lsodium -lpthread -lm

FuzzyExtractor: FuzzyPack.o FuzzyExtractor.o FEGen.o FECommon.o FERep.o
	$(CC) -o FuzzyExtractor FuzzyExtractor.o FuzzyPack.o FEGen.o FERep.o FECommon.o  $(LDFLAGS) -lsodium -lpthread -lm
#	$(CC) -o FuzzyExtractor FuzzyExtractor.o FuzzyPack.o FEGen.o FECommon.o /Users/bfuller/Research/Iris/nacl-20110221/build/taranenko/lib/x86/randombytes.o -lnacl $(CFLAGS)

#FuzzyPack: FuzzyPack.o FuzzyExtractor.o
#	$(CC) $< -o $@

FuzzyExtractor.o : FuzzyExtractor.c FuzzyPack.h
	$(CC) -c FuzzyExtractor.c FuzzyPack.h FECommon.h FEGen.h FERep.h $(CFLAGS)

FuzzyPack.o : FuzzyPack.c FuzzyPack.h 
	$(CC) -c FuzzyPack.c FuzzyPack.h $(CFLAGS)

FEGen.o: FEGen.c FEGen.h FuzzyPack.h FECommon.h
	$(CC) -c FEGen.c FEGen.h FuzzyPack.h FECommon.h $(CFLAGS)

FERep.o: FERep.c FERep.h FuzzyPack.h FECommon.h
	$(CC) -c FERep.c FERep.h FuzzyPack.h FECommon.h $(CFLAGS)

FECommon.o: FECommon.h FECommon.c FuzzyPack.h
	$(CC) -c FECommon.c FECommon.h FuzzyPack.h $(CFLAGS)


clean: 
	rm -rf FuzzyPack.o FuzzyExtractor.o FERep.o FEGen.o FECommon.o FuzzyPack FuzzyExtractor main
