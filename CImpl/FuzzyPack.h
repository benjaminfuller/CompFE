#ifndef FUZZY_PACK_H_
#define FUZZY_PACK_H_

#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>
#include "FuzzyExtractor.h"

/*typedef struct{
    int *vector;
    int *conf;
    int length;
    int enough;
    //This variable is unused at least in this file
} iris_array_input;*/



typedef struct {
    uint64_t * locker_order; 
    uint64_t *eye_vec;
    int *conf_vec;
    int *conf_level_vec;
    uint64_t **filters;
    int * priority_level;
    uint64_t num_filters;
    uint64_t length;
    uint64_t input_len;
    uint64_t pad_len;
    uint64_t locs_len;
    uint64_t sub_len;
    uint8_t **lockers;
    unsigned char * filter_populator;
    uint64_t * filter_preimage;
//    unsigned char *hmac_key;
//    uint64_t hmac_key_len;
    unsigned char *priv_key;
    uint64_t priv_key_len;
    struct subset_info;
} iris_pack;



typedef struct {
    char **lockers;
    char *hmac_key;
    int *conf_vec;
    uint64_t **filters;
    uint64_t num_filters;
    uint64_t hashes_count;
} iris_public;

typedef struct {
    uint64_t *bits;
    uint64_t length;
    uint64_t pad_len;
} packed_bits;

typedef iris_pack iris;


    



/*iris* alloc_iris();
packed_bits* alloc_packed_bits();
void free_packed_bits(packed_bits*);
void filter_eye(uint64_t*, uint64_t*, uint64_t*, uint64_t);
void pack_8b_segment(char*, char*);
void pack_64b_segment(char*, uint64_t*);
packed_bits* pack_bits(int *src, size_t);
uint64_t count_conf_bits(int*, int);
int* conf_condense(int *vec, int *conf, uint64_t conf_len);*/


void remake_iris(iris_array_input *src,iris_array_input* srcGen, iris * eye, uint64_t num_filters, uint64_t subsel_size);
iris * make_iris(iris_array_input *src, uint64_t num_filters, uint64_t subsel_size);

//void remake_iris(iris_array_input *src,iris_array_input* srcGen, iris * eye, uint64_t num_filters, uint64_t subsel_size);
#endif /* IRISFE_FUZZYPACK */
