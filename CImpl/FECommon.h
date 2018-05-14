#ifndef FECOMMON_H_
#define FECOMMON_H_

#include "FuzzyPack.h"

void populate_filters(iris * iris_data);
void prepopulate_filters(iris * iris_data);

void condense_iris(uint8_t * condensedvector, uint64_t sublen, const uint64_t * eye_vector, const uint64_t * filter);

#endif
