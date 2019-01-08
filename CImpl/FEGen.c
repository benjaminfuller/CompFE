#include "FEGen.h"
#include "FECommon.h"
#include "FuzzyPack.h"
#include <time.h>
#include <stdio.h>
#include <math.h>
#include <sodium.h>
#include <pthread.h>
#define NUM_THREADS 32


struct arg_struct{
	int arg;
	uint8_t* pad;
	iris * iris_gen;
};


//////////////////////////////////////////////////
//./////////////PREVIOUS WAY OF CALCULATION PRIORITIES/////
//////////////////////////////////////////////////////////////
//////////////////START HERE////////////////////////////////
/*
typedef struct  subset_struct{
    int*  subset_num[1000000];
    int* priority_level[1000000];
};
 */
/*
int calc_priority(int * num_conf,double* level, int norm);
int l_inf(int * num_conf,int *level);
int l_2(int * num_conf,double *level);
int l_1(int * num_conf,double *level);

//the 3  different norms to calculate the subset priorities with

int l_1(int * num_conf,double *level){
    double sum=0;
    for(int i=0;i<5;i++){
        sum=sum+(num_conf[i]*(i+1));
    }
    return sum;

}

int l_2(int * num_conf,double *level){

    int sum=0; 
    for(int i=0;i<5;i++){
        sum+=num_conf[i]*((i+1)*(i+1));
    }
    sum=sqrt(sum);
    return sum;
}

int l_inf(int * num_conf,int *level){
    int max=0;
    for (int i=0;i<5;i++){
	if((num_conf[i]*(i+1))>max){
	    max=num_conf[i]*(i+1);
	}
    }
    return max;
}






int calc_priority(int * num_conf,double* level, int norm){
    double conf_level;
    switch(norm){
	case(1):
 *level=l_1(num_conf,&conf_level);
	    break;
	case(2):
	    l_2(num_conf,&conf_level);
 *level=conf_level;
	    break;
	case(3):
	    l_inf(num_conf,&conf_level);
 *level=conf_level;
	    break;
	default:
	    verbose("'1' for l_1, '2' for l_2, and '3' for l_inf.\n");
            break;
    }
printf("the priority level is %d\n", level);
return 0;
}	
 */

//////////////////////////////////////////////////////////////
/////////////////////////////////END HERE///////////////////////////
////////////////////////////////////////////////////////////




void * parallel_hmac_perform(struct arg_struct* argument);

int  create_filters(iris * iris_data){
	int ret_code = 0;
	verbose("Number of filters %u\n",iris_data->num_filters);
	prepopulate_filters(iris_data);
	ret_code = populate_filters(iris_data);
	if(ret_code!=0){
		verbose("Populate filters failed %d\n", ret_code);
		return -1;
	}

	return 0;
}

//int create_hmac_key(iris * iris_data){
//	if(!iris_data){ return -1; }
//	iris_data->hmac_key_len = crypto_auth_hmacsha512_KEYBYTES;
//	iris_data->hmac_key = malloc(crypto_auth_hmacsha512_KEYBYTES);
//	if(!(iris_data->hmac_key)){ return -1;}
//
//	crypto_auth_hmacsha512_keygen((iris_data->hmac_key));
//	return 0;
//}

int FEgenerate(iris * iris_data, uint8_t ** gen_key){
	struct timespec start_time, stop_time;
	struct arg_struct args[NUM_THREADS];

	printf("Calling FE Generate\n");

	if(create_filters(iris_data)!=0){
		verbose("Create filters failed\n");
		return -1;
	}
	unsigned int i=0;
	//	if(create_hmac_key(iris_data)!=0){ return ;}

	uint8_t * locker_padding=(uint8_t *)malloc((crypto_auth_hmacsha512_BYTES)*sizeof(uint8_t));
	printf("Pointer for locker padding %x\n",locker_padding);
	if(locker_padding==NULL){
		verbose("Failed to allocate memory\n");
		return -1;
	}
	for(;i<crypto_auth_hmacsha512_BYTES/2;i++){
		locker_padding[i] = 0;
	}
	randombytes_buf(&(locker_padding[crypto_auth_hmacsha512_BYTES/2]), crypto_auth_hmacsha512_BYTES/2);


	if((gen_key)==NULL){
		verbose("No pointer provided");
		return -1;
	}
	(*gen_key)=(uint8_t *)malloc((crypto_auth_hmacsha512_BYTES/2)*sizeof(uint8_t));
	verbose("Key pointer is %x\n",*gen_key);
	for(int i=0;i<crypto_auth_hmacsha512_BYTES/2;i++){
		(*gen_key)[i]=locker_padding[i+(crypto_auth_hmacsha512_BYTES/2)];
		verbose("0x%x ",(*gen_key)[i]);
	}
	verbose("\n");
	unsigned int filter_num = 0;
	printf("The number of HMAC outputs is %u\n",iris_data->num_filters);
	for(;filter_num<iris_data->num_filters;filter_num++){
		iris_data->lockers[filter_num] = (uint8_t * ) malloc((crypto_auth_hmacsha512_KEYBYTES+crypto_auth_hmacsha512_BYTES)* sizeof(uint8_t));
		if(!(iris_data->lockers[filter_num])){
			verbose("Unable to allocate memory.\n");
			return -1;
		}

	}
	pthread_t threads[NUM_THREADS];
	int result_code;
	unsigned int index;

	printf("Starting thread spawning\n");
	clock_gettime(CLOCK_REALTIME, &start_time);

	for (index = 0; index < NUM_THREADS; ++index) {

		args[index].arg=index;
		args[index].pad=locker_padding;
		args[index].iris_gen=iris_data;
		//printf("In main: creating thread %d\n", index);
		result_code = pthread_create(&threads[index], NULL, parallel_hmac_perform,  &args[index]);
		if(result_code){ verbose("Thread returned with problem %u\n", index);}
	}
	// wait for each thread to complete
	for (index = 0; index < NUM_THREADS; ++index) {
		// block until thread 'index' completes
		result_code = pthread_join(threads[index],NULL);
		if(result_code!=0) {
			//printf("In main: thread %d has completed\n", index);
			verbose("The return code is %d\n",result_code);
			return -1;
		}
	}
	clock_gettime(CLOCK_REALTIME, &stop_time);
	verbose("Total time elapsed for locker creation: %u.%3u s\n", stop_time.tv_sec - start_time.tv_sec, stop_time.tv_nsec - start_time.tv_nsec);
	//	for(unsigned int i=0; i<crypto_auth_hmacsha512_KEYBYTES+ crypto_auth_hmacsha512_BYTES;i++){
	//		printf("%x ",iris_data->lockers[0][i]);
	//	}
	printf("The final locker padding is %x\n",locker_padding);
	free(locker_padding);
	return 0;
}

void * parallel_hmac_perform(struct arg_struct* args){

	//	struct subset_struct subset_pack;
	int passed_in_value;
	unsigned int i= 0;
	unsigned int locker_num;
	uint8_t condensedlen = args->iris_gen->sub_len/8+1;

	uint8_t condensedvector[condensedlen];
	for(i =0;i<condensedlen;i++){
		condensedvector[i] = 0;
	}
	uint8_t hmackey[crypto_auth_hmacsha512_KEYBYTES];
	uint8_t hmacoutput[crypto_auth_hmacsha512_BYTES];
	//               printf("Length of condensed vector %u\n",iris_global->sub_len/8+1);
	passed_in_value =  args->arg;
	unsigned int start_locker= (passed_in_value)*args->iris_gen->num_filters/NUM_THREADS;
	unsigned int stop_locker = (passed_in_value+1)*args->iris_gen->num_filters/NUM_THREADS;
//	printf("Thread %u %u %u\n", passed_in_value, start_locker, stop_locker);
	if(stop_locker>args->iris_gen->num_filters){
		verbose("Would exceed bounds End filter %u Num filter %u\n", stop_locker, args->iris_gen->num_filters);
		return -1;
	}

	//               printf("HMAC passed in value %u\n", passed_in_value);
	locker_num = start_locker;
	crypto_auth_hmacsha512_keygen(&hmackey);
	for(;locker_num < stop_locker;locker_num++){
		condense_iris(&condensedvector, args->iris_gen->sub_len, args->iris_gen->eye_vec,args->iris_gen->filters[locker_num]);
		if(locker_num==0){
			verbose("HMAC Key\n");
			for(unsigned int j=0;j<crypto_auth_hmacsha512_KEYBYTES;j++){
				verbose("%x ", hmackey[j]);
			}
			verbose("\nCondensed Vector 0x");
			for(unsigned j=0;j<condensedlen;j++){
				verbose("%x",condensedvector[j]);
			}
			printf("\n");
		}

		args->iris_gen->priority_level[locker_num]=0;
		for(i=0;i<crypto_auth_hmacsha512_KEYBYTES;i++){
			args->iris_gen->lockers[locker_num][i] = hmackey[i];
			//		printf("priority level of locker %d is %d\n",locker_num,subset_pack[locker_num].priority_level);
		}
		//		int priority;
		//
		//		int  priority_array[5];
		//		for (int i=0;i<5;i++) {priority_array[i]=0;}
		//		for(i=0;i<args->iris_gen->sub_len;i++){
		//
		//			switch(args->iris_gen->conf_level_vec[args->iris_gen->filters[locker_num][i]]){
		//			case(1):
		//			    		priority_array[0]+=1;
		//			break;
		//			case(2):
		//			    		priority_array[1]+=1;
		//			break;
		//			case(3):
		//			    		priority_array[2]+=1;
		//			break;
		//			case(4):
		//			    		priority_array[3]+=1;
		//			break;
		//			case(5):
		//			    		priority_array[4]+=1;
		//			break;
		//			default:
		//				break;
		//			}
		//		}
		//
		//		////PREVIOUS WAY///
		//		//for (int j=0;j<5;j++) printf("%d ",priority_array[j]);
		//		//calc_priority(priority_array,&priority,1);
		//		///////////////
		//
		//
		//		/////DIFFERENT NORMS
		//
		//		int sum=0;
		//		// l_1
		//		for(int i=0;i<5;i++){
		//			//  	            sum=sum+(priority_array[i]*(i+1));
		//		}
		//		// l_2
		//		for(int i=0;i<5;i++){
		//			sum+=priority_array[i]*((i+1)*(i+1));
		//		}
		//		double dsum = (double) sum;
		//		double stdev=sqrt(dsum);
		//		//l_3
		//		for (int i=0;i<5;i++){
		//			//	            if((num_conf[i]*(i+1))>sum){
		//			//          		sum=num_conf[i]*(i+1);
		//			//	    }
		//		}

		//		args->iris_gen->priority_level[locker_num]=sum;

		//		printf("priority level of locker# %d is %d\n  %d  %d  %d  %d  %d\n",locker_num,args->iris_gen->priority_level[locker_num], priority_array[0],priority_array[1],priority_array[2],priority_array[3],priority_array[4]);
		//		printf("\n");
		crypto_auth_hmacsha512(&hmacoutput, &condensedvector, condensedlen, &hmackey);
		for(i=0;i<crypto_auth_hmacsha512_BYTES;i++){
			args->iris_gen->lockers[locker_num][i+crypto_auth_hmacsha512_KEYBYTES] = hmacoutput[i] ^ args->pad[i];
		}
	}
	return 0;
}




////////////////////////////////////////////////////////////
////////THE OLD VERSION///////////////////////////////////
///////////////////////////////////////////////////////////
/*
void * parallel_vimhmac_perform(struct arg_struct* args){

	int passed_in_value;
	unsigned int i= 0;
	unsigned int locker_num;
	uint8_t condensedlen = args->iris_gen->sub_len/8+1;

	uint8_t condensedvector[condensedlen];
	for(i =0;i<condensedlen;i++){ condensedvector[i] = 0;}
	uint8_t hmackey[crypto_auth_hmacsha512_KEYBYTES];
	uint8_t hmacoutput[crypto_auth_hmacsha512_BYTES];

//	verbose("Length of condensed vector %u\n",args->iris_gen->sub_len/8+1);
	passed_in_value =  args->arg;
	unsigned int start_locker= (passed_in_value)*args->iris_gen->num_filters/NUM_THREADS;
	unsigned int stop_locker = (passed_in_value+1)*args->iris_gen->num_filters/NUM_THREADS;
	//TODO: should the above be -1 at the end?
//	printf("Thread %u %u %u\n", passed_in_value, start_locker, stop_locker);
	if(stop_locker>args->iris_gen->num_filters){
       	    verbose("Would exceed bounds End filter %u Num filter %u\n", stop_locker, args->iris_gen->num_filters);
	    return -1;
	}


//		printf("HMAC passed in value %u\n", passed_in_value);
	locker_num = start_locker;
	for(;locker_num < stop_locker;locker_num++){
		condense_iris(&condensedvector, args->iris_gen->sub_len, args->iris_gen->eye_vec,args->iris_gen->filters[locker_num]);
		crypto_auth_hmacsha512_keygen(&hmackey);
		if(locker_num==0){

    			verbose("HMAC Key\n");
			for(unsigned int j=0;j<crypto_auth_hmacsha512_KEYBYTES;j++){
				verbose("%x ", hmackey[j]);
			}
			verbose("\nCondensed Vector: ");
			for(unsigned j=0;j<condensedlen;j++){
				verbose("%x ",condensedvector[j]);
			}
			verbose("\n");
		}
		for(i=0;i<crypto_auth_hmacsha512_KEYBYTES;i++){
			args->iris_gen->lockers[locker_num][i] = hmackey[i];
		}
		crypto_auth_hmacsha512(&hmacoutput, &condensedvector, condensedlen, &hmackey);
		for(i=0;i<crypto_auth_hmacsha512_BYTES;i++){
			args->iris_gen->lockers[locker_num][i+crypto_auth_hmacsha512_KEYBYTES] = hmacoutput[i] ^ args->pad[i];
		}

	//	if(!args->iris_gen->filters[0]) printf("\n\n\n\nnull in gen\n");
		if(locker_num==31250){
			printf("HMAC Key 2nd subset\n");
			for(unsigned int j=0;j<crypto_auth_hmacsha512_KEYBYTES;j++){
				printf("%x ", hmackey[j]);
			}
			printf("\n Condensed Vector for 2nd subset\n");
			for(unsigned j=0;j<condensedlen;j++){
				printf("%x ",condensedvector[j]);
			}
			printf("\n");
	//		return NULL;
}}

		//////////	    for(i=0;i<condensedlen;i++){
				 verbose("%x ",condensedvector[i]);
			    }
			    verbose("\n");

			    for(i=0;i<crypto_auth_hmacsha512_BYTES;i++){
				verbose("%x ",args->pad[i]);
		     	    }
	/////////////		    verbose("\n");
	}
//	verbose("Successfully created lockers %u through %u\n",start_locker,locker_num);

//	}
	return 0;
}*/
