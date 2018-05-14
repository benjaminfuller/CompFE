#include "FECommon.h"
#include <sodium.h>
#include <pthread.h>
#include <time.h>
//#include <stdlib.h>
#include <inttypes.h>


iris * iris_d= NULL;
unsigned int numbers_to_gen =0;
unsigned int bit_len_num = 0;

#define NUM_SLACK 1000
#define NUM_THREADS 32

int intcmp(const void *aa, const void *bb)
{
	const uint64_t *a = aa, *b = bb;
	return (*a < *b) ? -1 : (*a > *b);
}


void prepopulate_filters(iris * iris_data){
	unsigned int i=0;
	if(iris_data==NULL){
		printf("Calling with unitialized data structure\n");
		return;
	}

	if(iris_data->filter_populator !=NULL){
		free(iris_data->filter_populator);
		iris_data->filter_populator=NULL;
	}
	iris_data->filter_populator = malloc(sizeof(unsigned char)*crypto_secretstream_xchacha20poly1305_KEYBYTES);
	if(iris_data->filter_populator==NULL){
		printf("Failed to allocate space");
	}
	randombytes(iris_data->filter_populator,crypto_secretstream_xchacha20poly1305_KEYBYTES);
	printf("Subset size: %i\n",iris_data->sub_len);
	printf("Size of confident bits %u\n",iris_data->locs_len);
	if(iris_data->locs_len>0xFFFF){
		printf("Too many confident bits for data structure\n");
		return;
	}
	for(i=0;i<iris_data->sub_len;i++){
		(iris_data->filter_preimage)[i] = randombytes_uniform(iris_data->locs_len);
	}
	qsort(iris_data->filter_preimage,iris_data->sub_len, sizeof(uint64_t), intcmp);
	for(i=0;i<iris_data->sub_len;i++){
		printf("%u ",	(iris_data->filter_preimage)[i] );
	}

	printf("\n");
	//	for(int i=0;i<crypto_secretstream_xchacha20poly1305_KEYBYTES;i++){
	//		printf("%u\n",(unsigned int ) iris_data->filter_populator[i]);
	//	}
	return;
}

void condense_iris(uint8_t * condensedvector, uint64_t sublen, const uint64_t * eye_vector, const uint64_t * filter){
	uint64_t i=0;
	uint64_t temp=0;
	uint64_t temp2=0;

	for(i=0; i<sublen/8;i++){
		condensedvector[i]=0;
	}
	for(i=0; i<sublen; i++){
			uint64_t temp = 0;
			uint64_t temp2 = 0;
			temp2 = 1<<(filter[i]%64);
			temp = eye_vector[filter[i]/64];

			if((temp& temp2)!=0){condensedvector[i/8] = condensedvector[i/8] | (1<<(i%8));}
	}

	return;
}


unsigned int next_pow_2(unsigned int n){
	unsigned int count =0 ;
	while( n != 0)
	{
		n  >>= 1;
		count += 1;
	}

	return  count;
}


void * parallel_filter_pop(void* argument) {
	uint64_t passed_in_argument=0 ;
	uint64_t start_filter = 0 ;
	uint64_t stop_filter = 0 ;
	unsigned char nonce[crypto_stream_chacha20_NONCEBYTES];
	uint16_t ciphertext[numbers_to_gen];//These are 16 bit chunks
	uint64_t filter_num = 0;
	uint64_t cur_loc = 0;
	uint64_t filter_loc =0 ;
	uint64_t num_matches = 0;
	uint64_t trunc_num =0;
	uint64_t curr_val = 0;
	uint64_t output_len = 0;

	passed_in_argument= *((int*) argument);

	start_filter = (passed_in_argument)*iris_d->num_filters/NUM_THREADS;
	stop_filter = (passed_in_argument+1)*iris_d->num_filters/NUM_THREADS -1;
	if(stop_filter>iris_d->num_filters){
		printf("Would exceed bounds End filter %u Num filter %u\n", stop_filter, iris_d->num_filters);
		return NULL;
	}
	//	printf("I should process filters between %u %u and %u\n", passed_in_value, start_filter, stop_filter);


	memset(nonce,0,crypto_stream_chacha20_NONCEBYTES);

	//	uint16_t output_len = 2*(iris_d->locs_len * iris_d->locs_len ) / (0xFFFF);
	output_len = numbers_to_gen;

	//	printf("The output len is %u\n", output_len);
	if(iris_d->locs_len>numbers_to_gen){
		printf("Input data structure too long\n");
		return NULL;
	}
	//These are 16 bit chunks
	//Clear the member to start;
	memset(ciphertext, 0, output_len);

	//Main parallel loop, use ChaCha to generate a bunch of numbers
	//Split these numbers into chunks and count the number that are below
	//Confidence threshold and pull the preimage into the new filter
	filter_num = start_filter;
	for(;filter_num < stop_filter; filter_num++){
		cur_loc = 0;
		filter_loc =0 ;
		num_matches = 0;
		nonce[0]= filter_num/256;
		nonce[1]=filter_num%256;
		crypto_stream_chacha20(&ciphertext, output_len*2, &nonce, iris_d->filter_populator);

		while(cur_loc < output_len && (num_matches <iris_d->locs_len)
				&& (filter_loc< iris_d->sub_len)){
			curr_val = ciphertext[cur_loc];
			trunc_num = curr_val - ((curr_val>>bit_len_num)<<bit_len_num);
//			printf("Number and truncated %u %u %u %u\n", curr_val,trunc_num, iris_d->locs_len, bit_len_num);
			if(trunc_num<iris_d->locs_len){
				num_matches++;
				if(num_matches==(iris_d->filter_preimage)[filter_loc]){
					iris_d->filters[filter_num][filter_loc] = trunc_num;
					filter_loc++;
				}
			}
			cur_loc++;
		}
//		printf("Length of output %u %u\n", output_len, iris_d->locs_len);
//		printf("Found %u %u matches\n", num_matches,iris_d->sub_len);
//		printf("Filter location %u\n",filter_loc);
//		for(unsigned int i=0;i<iris_d->sub_len;i++){
//			printf("%u ", (iris_d->filters)[filter_num][i] );
//		}
//		printf("\n");
		if(filter_loc!=iris_d->sub_len){
			printf("Did not get enough matches, can't work\n");
			printf("Cur loc %u Output len %u\n", cur_loc, output_len);
			printf("Num Match %u Num needed %u matches\n", num_matches,iris_d->locs_len);
			printf("Filter loc %u Sub len %u\n",filter_loc, iris_d->sub_len);
			for(unsigned int i=0;i<iris_d->sub_len;i++){
				printf("%u ", (iris_d->filters)[filter_num][i] );
			}
			printf("\n");

			return NULL;
		}
	}
	return NULL;
}


//The purpose of this function is to repopulate the filters based on the actual random
//ness and the shared  key
void populate_filters_crypto(iris * iris_data){
	pthread_t threads[NUM_THREADS];
	uint64_t thread_args[NUM_THREADS];
	int result_code;
	unsigned int index;
	iris_d= iris_data;
	struct timespec start_time, stop_time;

	if(iris_data==NULL){
		printf("Calling with uninitialized data structure\n");
		return;
	}
	if(iris_data->filter_populator==NULL || iris_data->filter_preimage== NULL){
		printf("Calling out of order, unable to populate filters\n");
		return;
	}
	//	printf("Nonce size %u\n",crypto_stream_chacha20_NONCEBYTES);


	clock_gettime(CLOCK_REALTIME, &start_time);
	bit_len_num = next_pow_2(iris_data->locs_len);
	numbers_to_gen = (1<<bit_len_num) + NUM_SLACK;

	//Creating each filter individually
	unsigned int filter_num = 0;
	printf("The number of filters is %u\n",iris_d->num_filters);
	for(;filter_num<iris_d->num_filters;filter_num++){
		iris_d->filters[filter_num] = (uint64_t * ) calloc(iris_d->sub_len,sizeof(uint64_t));
		if(!(iris_d->filters[filter_num])){
			printf("Unable to allocate memory.\n");
			return;
		}

	}
//	pthread_attr_t attr;
//	unsigned int stacksize = 0;
//	pthread_attr_init(&attr);
//	pthread_attr_getstacksize(&attr, &stacksize);
//	printf("Thread stack size = %d bytes \n", stacksize);

	// create all threads one by one
	for (index = 0; index < NUM_THREADS; ++index) {
		thread_args[ index ] = index;
		//		printf("In main: creating thread %d\n", index);
		result_code = pthread_create(&(threads[index]), NULL, &parallel_filter_pop, &thread_args[index]);
		if(result_code!=0){ printf("Thread returned with problem %u\n", index);}
	}

	// wait for each thread to complete
	for (index = 0; index < NUM_THREADS; ++index) {
		// block until thread 'index' completes
		result_code = pthread_join(threads[index], NULL);
//		printf("In main: thread %d has completed\n", index);
	}
	clock_gettime(CLOCK_REALTIME, &stop_time);
	printf("Total time elapsed for filter creation: %u.%3u s\n", stop_time.tv_sec - start_time.tv_sec, stop_time.tv_nsec - start_time.tv_nsec);
	//	printf("Number of filters filled %u\n",filter_num);
	//	printf("Sampling of filters: %u %u %u %u %u\n", iris_data->filters[0][31], iris_data->filters[68173][2],
	//			iris_data->filters[618279][15], iris_data->filters[10000][21], iris_data->filters[900623][0]);

	return;
}

void populate_filters(iris * iris_data){ populate_filters_crypto(iris_data);}
