#ifndef IRISFE_FUZZYEXTRACTOR
#define IRISFE_FUZZYEXTRACTOR
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#define LENGTH 32768

int verbose(const char * restrict, ...);
void setVerbose(bool);




typedef struct{
    float highpos;
    float lowpos;
    float highneg;
    float lowneg;
} Confidence;

typedef struct iris_array_struct{
    int vector[LENGTH];
    int conf[LENGTH];
    int conf_level[LENGTH];
    int length;
} iris_array_input;

int within_range(float, Confidence);
iris_array_input * readArray(FILE*, Confidence);
#endif /* !IRISFE_FUZZYEXTRACTOR */
