#include "FEGen.h"
#include "FECommon.h"
#include <time.h>
#include <sodium.h>
#include <pthread.h>


#define NUM_THREADS 32

int found=0;



struct arg_struct{
	iris * iris_rep;
	unsigned int arg;
	uint8_t * key;
};


uint8_t * FEreproduce(iris*, int);
void * parallel_hmac_recover(struct arg_struct* args);


//int create_hmac_key(iris * iris_data){
//	if(!iris_data){ return -1; }
//	iris_data->hmac_key_len = crypto_auth_hmacsha512_KEYBYTES;
//	iris_data->hmac_key = malloc(crypto_auth_hmacsha512_KEYBYTES);
//	if(!(iris_data->hmac_key)){ return -1;}
//
//	crypto_auth_hmacsha512_keygen((iris_data->hmac_key));
//	return 0;
//}

uint8_t * FEreproduce(iris * iris_data, int choice_num){
	struct timespec start_time, stop_time;
	struct arg_struct args[NUM_THREADS];

	//create_filters(iris_data);
	unsigned int i=0;

	//for(;i<crypto_auth_hmacsha512_BYTES/2;i++){
	//	locker_padding[i] = 0;
	//}
	//randombytes_buf(&(locker_padding[crypto_auth_hmacsha512_BYTES/2]), crypto_auth_hmacsha512_BYTES/2);
	//args.iris_rep = iris_data;


	if(!(iris_data->filters)){
		verbose("Calling with unitialized data.\n");
		return NULL;
	}
	if(!(iris_data->filters[0])){
		verbose("Need to repopulate filters for some reason\n");
		populate_filters(iris_data);
	}

	verbose("Starting Reproduce...\n");
	//	unsigned int filter_num = 0;
	//printf("The number of HMAC outputs is %u\n",iris_data->num_filters);
	/*	for(;filter_num<iris_rep_global->num_filters;filter_num++){
			iris_data->lockers[filter_num] = (uint8_t * ) malloc((crypto_auth_hmacsha512_KEYBYTES+crypto_auth_hmacsha512_BYTES)* sizeof(uint8_t));
			if(!(iris_data->lockers[filter_num])){
				printf("Unable to allocate memory.\n");
				return;
			}

		}*/

	pthread_t threads[NUM_THREADS];
	uint8_t * result_code;
	uint8_t temp_pointer= NULL;
	unsigned int index;


	clock_gettime(CLOCK_REALTIME, &start_time);

	for (index = 0; index < NUM_THREADS; ++index) {
		args[index].arg=index;
		args[index].iris_rep=iris_data;
		args[index].key=NULL;
		//printf("In main: creating thread %d\n", index);
		result_code = pthread_create(&threads[index], NULL, parallel_hmac_recover, &args[index]);
		if(result_code){ verbose("Thread returned with problem %u\n", index);}
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
			verbose("Found a match at locker number %u\n",index);

		}
		//			printf("In main: thread %d has completed\n", index);
	}
	clock_gettime(CLOCK_REALTIME, &stop_time);

	uint8_t * keyX=NULL;// (uint8_t *) calloc(crypto_auth_hmacsha512_BYTES/2, sizeof(uint8_t));
	// getting the key once it's not null
	int keyFound=0;
	for(int o=0;o<NUM_THREADS;o++){
		if(keyFound && args[o].key!=NULL){
			free(args[o].key);
		}
		else if(args[o].key!=NULL){
			keyFound=1;
			keyX=args[o].key;
		}
	}
	if(keyX ==NULL) verbose("Rep key in FERep is null\n");

	verbose("Total time elapsed for reconstruction: %u.%3u s\n", stop_time.tv_sec - start_time.tv_sec, stop_time.tv_nsec - start_time.tv_nsec);
	verbose("%u.%3u\n", stop_time.tv_sec - start_time.tv_sec, stop_time.tv_nsec - start_time.tv_nsec);


	//////The purpose of this part is to save the time of rep to create the graphs
	if (choice_num==4){
		/*
 	    /////This saves the time only when rep unlocks
	    if(found){
	    FILE * un_data_file;
            un_data_file=fopen("/home/mariem/IrisFe/data/unlocking_dist_rep_time.txt","a");
	    if((fprintf(un_data_file,"%u.%3u\n", stop_time.tv_sec - start_time.tv_sec, stop_time.tv_nsec - start_time.tv_nsec) <=0)){
	        verbose("Saving Rep time Failed\n");
	    }

            fclose(un_data_file);   
	}

	    //this saves all rep time
	    FILE * data_file;
            data_file=fopen("/home/mariem/IrisFe/data/dist_rep_time.txt","a");
	    if((fprintf(data_file,"%u.%3u\n", stop_time.tv_sec - start_time.tv_sec, stop_time.tv_nsec - start_time.tv_nsec) <=0)){
	        verbose("Saving Rep time Failed\n");
	    }

            fclose(data_file);   
		 */
		/////////////////////
	}
	return keyX;
}


void * parallel_hmac_recover(struct arg_struct * args){
	int passed_in_value;
	unsigned int i= 0;
	unsigned int match = 0;
	unsigned int  locker_num;
	uint8_t condensedlen = args->iris_rep->sub_len/8+1;
	int key_copied=0;

	uint8_t condensedvector[condensedlen];

	for (i=0;i<condensedlen;i++){
		condensedvector[i]=0;
	}

	uint8_t hmacoutput[crypto_auth_hmacsha512_BYTES];
	uint8_t unpadded[crypto_auth_hmacsha512_BYTES] ={0};

	//	printf("Length of condensed vector %u\n",iris_rep_global->sub_len/8+1);
	passed_in_value = args->arg;


	////start and stop lockers without priority queue
	unsigned int start_locker= (passed_in_value)*args->iris_rep->num_filters/NUM_THREADS;
	unsigned int stop_locker = (passed_in_value+1)*args->iris_rep->num_filters/NUM_THREADS -1;

	//start and stop lockers with priority queue
	//	unsigned int start_locker= passed_in_value;
	//	unsigned int stop_locker = passed_in_value+ (args->iris_rep->num_filters-NUM_THREADS);

	if(stop_locker>args->iris_rep->num_filters){
		verbose("Would exceed bounds End filter %u Num filter %u\n", stop_locker, args->iris_rep->num_filters);
		return -1;
	}


	//	printf("HMAC passed in value %u\n", passed_in_value);
	//start and stop locker when using 1 thread to test
	//locker_num = 0;
	//stop_locker=1000000;
	locker_num=start_locker;
	for(;locker_num < stop_locker;locker_num++){
		//		printf("Locker num %u\n",locker_num);

		//locker_num=sorted_lockers[locker_num_index];
		condense_iris(&condensedvector, args->iris_rep->sub_len,args->iris_rep->eye_vec, args->iris_rep->filters[locker_num]);

		//crypto_auth_hmacsha512_keygen(&hmackey);
		//		for(i=0;i<crypto_auth_hmacsha512_KEYBYTES;i++){
		//			iris_rep_global->lockers[locker_num][i] = hmackey[i];
		//		}

		crypto_auth_hmacsha512(&hmacoutput, &condensedvector, condensedlen, args->iris_rep->lockers[locker_num]);
		for(i=0;i<crypto_auth_hmacsha512_BYTES;i++){
			unpadded[i] = hmacoutput[i] ^ args->iris_rep->lockers[locker_num][i+crypto_auth_hmacsha512_KEYBYTES];

			//args->iris_rep->lockers[locker_num][i+crypto_auth_hmacsha512_KEYBYTES] = hmacoutput[i] ^ locker_padding[i];
		}
		if(locker_num==0){
			verbose("HMAC Key\n");
			for(unsigned int j=0;j<crypto_auth_hmacsha512_KEYBYTES;j++){
				verbose("%x ", args->iris_rep->lockers[locker_num][j]);
			}
			verbose("\nCondensed Vector 0x");
			for(unsigned j=0;j<condensedlen;j++){
				verbose("%x",condensedvector[j]);
			}
			printf("\n");
		}
		match = 1;
		for(i=0;i<crypto_auth_hmacsha512_BYTES /2;i++){
			if(unpadded[i]!=0){
				match = 0;
			}
		}


		found=0;	

		if(match==1){
			verbose("Found a match at locker_num: %u\n", locker_num);
			//			for(i=0;i<crypto_auth_hmacsha512_BYTES ;i++){
			//				printf("%x ",unpadded[i]);
			//			}printf("\n");
			//			for(i=0;i<iris_rep_global->sub_len ;i++){
			//				printf("%u ",iris_rep_global->filters[locker_num][i]);
			//			}printf("\n");
			//////////////////////////////////////////////////////////////////////////////////////////////////////////
			//			//////I have a memory leak when I uncomment out this and I couldn't fix it
			//			//////in order to avoid getting a killed process when running the program on all json files, I commented out for now
			//			/////we also needed to get the key and return it in FEGenerate in order to check if the key returned from the rep is				////// the same (check done in FuzzyExtractor)
			//
			//		if (args->key==NULL){

			uint8_t* key = (uint8_t *) malloc(crypto_auth_hmacsha512_BYTES/2* sizeof(uint8_t));
			for(i=crypto_auth_hmacsha512_BYTES /2;i<crypto_auth_hmacsha512_BYTES;i++){
				key[i-crypto_auth_hmacsha512_BYTES /2] = unpadded[i];
			}
			args->key=key;

			/////////////////////////////////////////////////////////////////////////////

			//		if(found==0){
			//////saving the first unlocked locker, should be changed to only with option 4
			/*    		    FILE * lockers_file;
            		    lockers_file=fopen("/home/mariem/IrisFe/data/locker_vs_prob.txt","a");
	    		    if((fprintf(lockers_file,"%u\n", locker_num) <=0)){
	        	         verbose("Saving unlocked locker Failed\n");
	    		    }
			    verbose("locker num %u\n",locker_num);	
            		    fclose(lockers_file);   
			    found=1;
			 // }*/
			// checking the condensed vector from locker_num 0 to compare it with the condensed vector of locker_num 0 in gen
			if(locker_num==0){
				verbose("Condensed Vector: 0x");
				for(i=0;i<condensedlen;i++){
					verbose("%x ",condensedvector[i]);

				}
				verbose("\n");
			}

			return match;
		}

		//	for(i=0;i<crypto_auth_hmacsha512_BYTES;i++){
		//		printf("%x ",locker_padding[i]);
		//	}
		//	printf("\n");
	}
	//	printf("Successfully created lockers %u through %u\n",start_locker,locker_num);
	return 0;
}

