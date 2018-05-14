#include "FEGen.h"
#include "FECommon.h"
#include <time.h>
#include <sodium.h>
#include <pthread.h>


#define NUM_THREADS 32
iris * iris_rep_global= NULL;


void * parallel_hmac_recover(void * argument);


//int create_hmac_key(iris * iris_data){
//	if(!iris_data){ return -1; }
//	iris_data->hmac_key_len = crypto_auth_hmacsha512_KEYBYTES;
//	iris_data->hmac_key = malloc(crypto_auth_hmacsha512_KEYBYTES);
//	if(!(iris_data->hmac_key)){ return -1;}
//
//	crypto_auth_hmacsha512_keygen((iris_data->hmac_key));
//	return 0;
//}

uint8_t * FEreproduce(iris * iris_data){
	struct timespec start_time, stop_time;
	//create_filters(iris_data);
	unsigned int i=0;

	//	for(;i<crypto_auth_hmacsha512_BYTES/2;i++){
	//		locker_padding[i] = 0;
	//	}
	//	randombytes_buf(&(locker_padding[crypto_auth_hmacsha512_BYTES/2]), crypto_auth_hmacsha512_BYTES/2);
	iris_rep_global = iris_data;

	if(!iris_data->filters){
		printf("Calling with unitialized data.\n");
		return NULL;
	}
	if(!(iris_data->filters[0])){
		printf("Need to repopulate filters for some reason\n");
		populate_filters(iris_data);
	}
	printf("Starting reproduce\n");
	//	unsigned int filter_num = 0;
	//	//printf("The number of HMAC outputs is %u\n",iris_data->num_filters);
	//	for(;filter_num<iris_rep_global->num_filters;filter_num++){
	//		iris_data->lockers[filter_num] = (uint8_t * ) malloc((crypto_auth_hmacsha512_KEYBYTES+crypto_auth_hmacsha512_BYTES)* sizeof(uint8_t));
	//		if(!(iris_data->lockers[filter_num])){
	//			printf("Unable to allocate memory.\n");
	//			return;
	//		}
	//
	//	}

	pthread_t threads[NUM_THREADS];
	int thread_args[NUM_THREADS];
	uint8_t * result_code;
	uint8_t * temp_pointer= NULL;
	unsigned int index;

	clock_gettime(CLOCK_REALTIME, &start_time);

	for (index = 0; index < NUM_THREADS; ++index) {
		thread_args[ index ] = index;
		//		printf("In main: creating thread %d\n", index);
		result_code = pthread_create(&threads[index], NULL, parallel_hmac_recover, &thread_args[index]);
		if(result_code){ printf("Thread returned with problem %u\n", index);}
	}

	// wait for each thread to complete
	for (index = 0; index < NUM_THREADS; ++index) {
		// block until thread 'index' completes

		temp_pointer= pthread_join(threads[index], NULL);
		if(result_code!=NULL){
			free(temp_pointer);
		}
		else{
			result_code= temp_pointer;
		}
		if(result_code!=NULL){
			printf("Found a match at locker number %u\n",index);
		}
		//		printf("In main: thread %d has completed\n", index);
	}
	clock_gettime(CLOCK_REALTIME, &stop_time);
	printf("Total time elapsed for reconstruction: %u.%3u s\n", stop_time.tv_sec - start_time.tv_sec, stop_time.tv_nsec - start_time.tv_nsec);
	return result_code;
}


void * parallel_hmac_recover(void * argument){
	int passed_in_value;
	unsigned int i= 0;
	unsigned int match = 0;
	unsigned int locker_num;
	uint8_t condensedlen = iris_rep_global->sub_len/8+1;

	uint8_t condensedvector[iris_rep_global->sub_len/8+1];
	uint8_t hmacoutput[crypto_auth_hmacsha512_BYTES];
	uint8_t unpadded[crypto_auth_hmacsha512_BYTES];

	//	printf("Length of condensed vector %u\n",iris_rep_global->sub_len/8+1);
	passed_in_value = *((int *) argument);
	unsigned int start_locker= (passed_in_value)*iris_rep_global->num_filters/NUM_THREADS;
	unsigned int stop_locker = (passed_in_value+1)*iris_rep_global->num_filters/NUM_THREADS -1;
	if(stop_locker>iris_rep_global->num_filters){
		printf("Would exceed bounds End filter %u Num filter %u\n", stop_locker, iris_rep_global->num_filters);
		return -1;
	}


	//	printf("HMAC passed in value %u\n", passed_in_value);
	locker_num = start_locker;
	for(;locker_num < stop_locker;locker_num++){
		//		printf("Locker num %u\n",locker_num);

		condense_iris(&condensedvector, iris_rep_global->sub_len, iris_rep_global->eye_vec, iris_rep_global->filters[locker_num]);
		//		crypto_auth_hmacsha512_keygen(&hmackey);
		//		for(i=0;i<crypto_auth_hmacsha512_KEYBYTES;i++){
		//			iris_rep_global->lockers[locker_num][i] = hmackey[i];
		//		}

		crypto_auth_hmacsha512(&hmacoutput, &condensedvector, condensedlen, iris_rep_global->lockers[locker_num]);
		for(i=0;i<crypto_auth_hmacsha512_BYTES;i++){
			unpadded[i] = hmacoutput[i] ^ iris_rep_global->lockers[locker_num][i+crypto_auth_hmacsha512_KEYBYTES];
			//			iris_rep_global->lockers[locker_num][i+crypto_auth_hmacsha512_KEYBYTES] = hmacoutput[i] ^ locker_padding[i];
		}
//		if(locker_num==0){
//			printf("HMAC Key\n");
//			for(unsigned int j=0;j<crypto_auth_hmacsha512_KEYBYTES;j++){
//				printf("%x ", iris_rep_global->lockers[locker_num][j]);
//			}
//			printf("\n");
//			printf("\n Condensed Vector\n");
//			for(unsigned j=0;j<condensedlen;j++){
//				printf("%x ",condensedvector[j]);
//			}
//			printf("\n");
//			for(i=0;i<crypto_auth_hmacsha512_BYTES ;i++){
//				printf("%x ",unpadded[i]);
//			}printf("\n");
//		}
		match = 1;
		for(i=0;i<crypto_auth_hmacsha512_BYTES /2;i++){
			if(unpadded[i]!=0){
				match = 0;
			}
		}
		if(match==1){
			printf("Found a match at locker_num: %u\n", locker_num);
//			for(i=0;i<crypto_auth_hmacsha512_BYTES ;i++){
//				printf("%x ",unpadded[i]);
//			}printf("\n");
//			for(i=0;i<iris_rep_global->sub_len ;i++){
//				printf("%u ",iris_rep_global->filters[locker_num][i]);
//			}printf("\n");
//			for(i=0;i<condensedlen;i++){
//				printf("%x ",condensedvector[i]);
//			}

			uint8_t * match = malloc(sizeof(uint8_t)* crypto_auth_hmacsha512_BYTES/2);
			for(i=crypto_auth_hmacsha512_BYTES /2;i<crypto_auth_hmacsha512_BYTES;i++){
				match[i-crypto_auth_hmacsha512_BYTES /2] = unpadded[i];
			}
			return match;
		}


		//	for(i=0;i<condensedlen;i++){
		//		printf("%x ",condensedvector[i]);
		//	}
		//	printf("\n");
		////	for(i=0;i<crypto_auth_hmacsha512_BYTES;i++){
		////		printf("%x ",locker_padding[i]);
		////	}
		//	printf("\n");
	}
	//	printf("Successfully created lockers %u through %u\n",start_locker,locker_num);
	return 0;
}

