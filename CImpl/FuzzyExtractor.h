#ifndef IRISFE_FUZZYEXTRACTOR
#define IRISFE_FUZZYEXTRACTOR
#include <stdio.h>
#include <stdlib.h>

typedef struct{
    float highpos;
    float lowpos;
    float highneg;
    float lowneg;
} Confidence;

typedef struct{
    int *vector;
    int *conf;
    int length;
    int enough;
    //This variable is unused at least in this file
} iris_array_input;

int within_range(float, Confidence);
iris_array_input readArray(char*, Confidence);

#endif /* !IRISFE_FUZZYEXTRACTOR */
