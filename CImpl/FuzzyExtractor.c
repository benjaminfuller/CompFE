#include "FuzzyExtractor.h"
#include <stdio.h>
#include <stdlib.h>
#include <sodium.h>
#include "FuzzyPack.h"
#include "FEGen.h"
#include "FERep.h"
#define NUM_THREADS 32
#define _POSIX_C_SOURCE >= 199309L

/*typedef struct{
    float highpos;
    float lowpos;
    float highneg;
    float lowneg;
} Confidence;*/

int within_range(float val, Confidence conf){

	return ((val < conf.highpos && val > conf.lowpos) || (val < conf.highneg && val > conf.lowneg));

}

int bit_value(float val){
	if(val <= 0)
		return 0;
	else
		return 1;
}

iris_array_input readArray(char* file, Confidence conf){

	size_t length = 32964;
	float* buff = malloc(length * sizeof(float));
	//Need to be careful whenever you allocate memory, the OS is within rights not to give you any and this is a NULL
	//pointer need to abort if you don't get anything here
	float *temp;
	iris_array_input data;
	size_t i = 0;
	FILE *fp;
	fp = fopen(file, "r");
	//This is the first two brackets
	printf("%i %i %i\n", fgetc(fp), fgetc(fp), sizeof(float));
	float fptemp;
	while(0!= fscanf(fp, "%f, ", &fptemp)){
		buff[i]=fptemp;
		//   printf("got %f %i\n", buff[i], i);
		//I'm concerned about error handling when it can't find a floating point
		//Is there a reason we should be expected larger inputs?  Wouldn't it be easier to have a
		//size parameter and then know rather than realloc? puts everything on stack then
		i++;
		if(i == length) {
			printf("read too many characters %i\n", i);
			break;
			//Why create the temporary variable?  It isn't used
		}
		//if(i==2){ break;}
	}
	data.length = i;
	int* v = malloc(data.length * sizeof(int));
	int* c = malloc(data.length * sizeof(int));
	for(int j = 0; j<data.length; j++){
		v[j] = bit_value(buff[j]);
		c[j] = within_range(buff[j], conf);
	}
	data.vector = v;
	data.conf = c;
	fclose(fp);
	if(buff!=NULL){
		free(buff);
	}
	return data;

}


int main(int argc, const char* argv[]){
	Confidence conf = {20, 3, -2, -60};
	iris_array_input data = readArray("input.txt", conf);
	//    for(int i = 0; i < data.length; i++){
	//        printf("bit: %d conf_mask: %d\n", data.vector[i], data.conf[i]);
	//    }
	iris * iris_data = make_iris(&data, 1000000, 43);
	printf("made the iris\n");
	FEgenerate(iris_data);

	//Perturbing the input value with 1% prob
	printf("The input length is %u\n", iris_data->length);
	for(unsigned int i=0;i<iris_data->length/64;i++){
		for(unsigned int j=0;j<11;j++){
			unsigned int temp = randombytes_uniform(64);
			iris_data->eye_vec[i] = (iris_data->eye_vec[i]) ^ (1<<temp);
		}
	}
	uint8_t * recovered_key = FEreproduce(iris_data);
	free(recovered_key);
	free_iris(iris_data);
	free(data.conf);
	free(data.vector);
	return 0;
}
