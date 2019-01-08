#ifndef FECOMMON_H_
#define FECOMMON_H_
#include "FuzzyPack.h"

int populate_filters(iris * iris_data);
void prepopulate_filters(iris * iris_data);
int gen_and_serialize(iris * iris_data,iris_array_input * data, FILE* fw,uint8_t** key);
int rep_and_serialize(iris* iris_data, FILE* fd_p,iris_array_input * data, uint8_t ** key, int choice_num);

void condense_iris(uint8_t * condensedvector, uint64_t sublen, const uint64_t * eye_vector, const uint64_t * filter);

#endif
