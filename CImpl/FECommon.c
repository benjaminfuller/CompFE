#include "FECommon.h"
#include <sodium.h>
#include <pthread.h>
#include <time.h>
//#include <stdlib.h>
#include <inttypes.h>
//#define _POSIX_C_SOURCE >= 199309L
#define NUM_SLACK 1000
#define NUM_THREADS 32

//int * array=NULL;

typedef struct
{
	int * index;
	iris * iris_data;
	int * return_code;
	uint16_t numbers_to_gen;
	uint16_t bit_len_num ;
} t_args;


void read_pub_file(iris * iris_data, iris_array_input data,FILE * fd_p);
uint8_t * FEreproduce(iris *, int);
int rep_and_serialize(iris* iris_data, FILE* fd_p,iris_array_input * data, uint8_t ** key, int choice_num);
int gen_and_serialize(iris * iris_data,iris_array_input * data,FILE *fw, uint8_t ** key);


int intcmp(const void *aa, const void *bb)
{
	const uint64_t *a = aa, *b = bb;
	return (*a < *b) ? -1 : (*a > *b);
}



int Check_fseek(int sz){
	if(sz!=0){
		verbose("Fseek Failed.\n");
		return -1;
	}
	return 0;
}

//TODO:renable prioritization of subsets
//// function needed to compare the priority level (descending order)
//int cmp(const void *a,const void *b){
//	int ia=*(int *) a;
//	int ib = *(int *) b;
//	return array[ia] >array[ib] ? -1 : array[ia] < array[ib];
//}

int  gen_and_serialize(iris * iris_data,iris_array_input * data,FILE *fw,uint8_t ** key ){
	//check if the iris data is not NULL
	if(iris_data==NULL){
		verbose("Calling with uninitialized Data structure\n");
		return NULL;
	}

	int i,j;
	//get the key returned by FEgenerate and check if it's not NULL

	if(FEgenerate(iris_data, key)!=0){
		verbose("Error in generation process");
		return -1;
	}
	if(*key==NULL){
		verbose("Failed to Generate in gen and serialize\n");
		return -1;
	}
	printf("The produced key is %x\n",*key);

	int conf_levels[iris_data->num_filters];

	//check the locker num and its priority
	// verbose("The confidence levels:\n");
	for(int i=0;i<iris_data->num_filters;i++){
		conf_levels[i]=iris_data->priority_level[i];
		//   verbose("locker_num[%d]= %d\n ",i,conf_levels[i]);
	}

	/*
	 * TODO: this code was being used to set priority but doesn't work, redesign
	 * priority
	*/
//	int index[iris_data->num_filters];
//	for(i=0;i<iris_data->num_filters;i++){index[i]=i;}
//	array=conf_levels;
//	qsort(index,iris_data->num_filters,sizeof(*index),cmp);

	/*To check the result of sorting lockers depending on the confidence level
    verbose("data is \n");
    for(i=0;i<size;i++) verbose("%d\t%d\n", conf_levels[index[i]],index[i]);
	 */


	//Save the iris data needed for rep in the public file
	//Line 1: subset size
	if(fprintf(fw, "Subset_size: %llu", iris_data->sub_len)<=strlen("Subset_size: ")){
		verbose("Failed to save the subset size!\n");
		return -1;
	}
	fprintf(fw,"\n");
	//Line 2: number of digital lockers
	if(fprintf(fw, "Number_of_lockers: %llu", iris_data->num_filters)<=strlen("Number_of_lockers: ")){
		verbose("Failed to save the number of lockers!\n");
		return -1;

	}
	fprintf(fw,"\n");
	//Line 3: locker check order
	if(fprintf(fw, "Lockers_order: ")!=strlen("Lockers_order: ")){
		verbose("Failed to save Sorted Lockers!\n");
		return -1;
	}
	for(i=0;i<iris_data->num_filters;i++){
		if (fprintf(fw,"%d ", i)<=0){
			verbose("Failed to save the locker num[%d].\n",i);
			return -1;
		}
	}
	fprintf(fw,"\n");
	//Line 4: confidence vector
	if(fprintf(fw, "Confidence_Vector: ")!=strlen("Confidence_Vector: ")){
		verbose("Failed to save the Confidence Vector!\n");
		return -1;
	}
	for(i=0;i<data->length;i++){
		if(fprintf(fw,"%d ",data->conf[i])<=0){
			verbose("Failed to save the confidence vector[%d]\n",i);
			return -1;
		}
	}

	//Line 5: Master subset (used to generate other subsets)
	fprintf(fw,"\n");
	if(fprintf(fw, "Filter_Preimage: ")!=strlen("Filter_Preimage: ")){
		verbose("Failed to save the filter preimage!\n");
		return -1;
	}
	for(i=0;i<iris_data->sub_len;i++){
		if(fprintf(fw, " %llu ", iris_data->filter_preimage[i])<=0){
			verbose("Failed to save filter preimage[%d]!\n",i);
			return -1;
		}
	}
	fprintf(fw,"\n");
	//Line 6: Cryptographic key to convert master subset to all subset selectors and then outputs
	//of each locker
	if(fprintf(fw, "Populator_and_Lockers: ")!=strlen("Populator_and_Lockers: ")){
		verbose("Failed to save the filter populator and lockers!\n");
		return -1;
	}
	printf("First byte of populator 0x%x\n",iris_data->filter_populator[0]);
	if(fwrite(iris_data->filter_populator, sizeof(unsigned char), crypto_secretstream_xchacha20poly1305_KEYBYTES, fw)!=crypto_secretstream_xchacha20poly1305_KEYBYTES){
		verbose("Failed to save filter populator!\n");
		return -1;
	}
	for(i=0; i<iris_data->num_filters;i++){
		if(i==0){verbose("First byte of first locker 0x%x\n",iris_data->lockers[i][0]);}
		if((fwrite(iris_data->lockers[i],sizeof(uint8_t),crypto_auth_hmacsha512_BYTES+crypto_auth_hmacsha512_KEYBYTES,fw))!=crypto_auth_hmacsha512_BYTES+crypto_auth_hmacsha512_KEYBYTES){
			verbose("Failed to write locker number %d\n",i);
			return -1;
		}
	}
	verbose("Saving Iris Data in the Public File was Successful.\n");
	return 0;
}




int rep_and_serialize(iris* iris_data, FILE* fd_p,iris_array_input *data, uint8_t ** key, int choice_num){
	//check the availability of the iris data
	if(iris_data==NULL){
		verbose("Calling with uninitialized Data structure\n");
		return -1;
	}
	read_pub_file(iris_data,* data,fd_p);
	//get the key returned from FEReproduce
	verbose("data length is %d\n", data->length);
	*key=FEreproduce(iris_data,choice_num);
	return 0;
}


void read_confvec( FILE * fd_p, iris_array_input data){

	int temp, fseek_ret, i, size=0;
	char * line=NULL;
	size_t len=0;
	char conf[]="Confidence_Vector: ";

	size+=getline(&line,&len,fd_p);
	size+=getline(&line,&len,fd_p);
	size+=getline(&line,&len,fd_p);
	fseek_ret=fseek(fd_p,size,SEEK_SET);
	Check_fseek(fseek_ret);
	fseek_ret=fseek(fd_p, sizeof(conf)-1,SEEK_CUR);
	Check_fseek(fseek_ret);

	for(i=0;i<data.length;i++){
		if(fscanf(fd_p,"%d ",&temp)!=1){
			verbose("Failed to save the confidence vector[%d]\n",i);
			return;
		}

		data.conf[i]=temp;
	}
	rewind(fd_p);
	free(line);
}






void read_pub_file(iris * iris_data,iris_array_input data, FILE * fd_p){

	//Read the public file and save the information in the iris data

	int size=0, i=0;
	char * line=NULL;
	size_t len=0;
	char fpre[]="Filter_Preimage: ";
	char fpop[]="Populator_and_Lockers: ";
	char lok[]= "Lockers: ";
	int fseek_ret;
	//create a buffer for the filter populator values
	unsigned char pop_buff[crypto_secretstream_xchacha20poly1305_KEYBYTES];



	// set the pointer at the beginning of the file
	rewind(fd_p);
	//Line 1: get subsetsize
	//get sub len line and assign the value to iris_data->sublen
	size+=getline(&line,&len,fd_p);
	//    iris_data->sub_len=0;
	//    verbose("More bad things: %u\n",iris_data->sub_len);
	sscanf(line,"%*s %llu",&(iris_data->sub_len));
	verbose("The subset size is %u\n", iris_data->sub_len);
	if(line){ free(line);}
	line=NULL;
	//Line 2: get the number of lockers
	//get the numfilters line and assign it to iris_data->numfilters
	size+=getline(&line,&len,fd_p);
	sscanf(line,"%*s %llu", &(iris_data->num_filters));
	if(line){    free(line);}
	line=NULL;
	verbose("The number is lockers is %u\n",iris_data->num_filters);
	fseek_ret=fseek(fd_p,size,SEEK_SET);
	if(iris_data->num_filters==0){
		verbose("Running rec with no filters");
		exit(1);
	}
	//Line 3: get the order of lockers
	size+=getline(&line, &len, fd_p);
	uint64_t k =0;
	char * line_orig= line;
	int read_chars = 0;
	sscanf(line, "%*s %llu%n",&k,&read_chars);
	iris_data->locker_order[0]=k;
	for(int j=1;j<iris_data->num_filters;j++){
		k = 0;
		line+=(read_chars*sizeof(char));
		sscanf(line, "%*c%llu%n",&k, &read_chars);
		iris_data->locker_order[j]=k;
	}
	if(line_orig){ free(line_orig); line=NULL; line_orig=NULL;}

	//Line 4: The confidence information from gen, not current used
	//TODO: should just seek over the line
	size+=getline(&line, &len, fd_p);
	if(line){free(line); line=NULL;}

	//set the pointer in the right place to get the filter preimage values
//	fseek_ret=fseek(fd_p,size,SEEK_SET);
	fseek_ret=fseek(fd_p, sizeof(fpre),SEEK_CUR);
	Check_fseek(fseek_ret);

	//Line 5: the master subset
	//create a buffer for the preimage values and initialize it
	uint64_t pre_buff[iris_data->sub_len];
	for(int i=0;i<iris_data->sub_len;i++){
		pre_buff[i]=0;
	}

	//assign the filter preimage values to iris_data-filter_preimage
	for(int i=0;i<iris_data->sub_len;i++){
		unsigned int temp=0;
		int c;
		if((c=fscanf(fd_p, "%u ",&temp))!=1){
			verbose("Error in file parsing and c is %d\n",c);
			return;
		}
		pre_buff[i] = temp;
		iris_data->filter_preimage[i]=pre_buff[i];
	}
	//Line 6: reading the cryptographic materials
	fseek_ret=fseek(fd_p,strlen(fpop),SEEK_CUR);
	Check_fseek(fseek_ret);

	if(fread(&pop_buff, sizeof(unsigned char), crypto_secretstream_xchacha20poly1305_KEYBYTES, fd_p)!=crypto_secretstream_xchacha20poly1305_KEYBYTES){
		verbose("Failed to read the filter populator characters\n");
		return;
	}
	verbose("First byte of populator 0x%x\n",pop_buff[0]);
	//The actual cryptographic outputs of the digital lockers
	for(int i=0; i<iris_data->num_filters;i++){
		if(iris_data->lockers[i]!=NULL){
			free(iris_data->lockers[i]);
			iris_data->lockers[i]=NULL;
		}
		iris_data->lockers[i]=malloc(sizeof(uint8_t)*(crypto_auth_hmacsha512_KEYBYTES+crypto_auth_hmacsha512_BYTES));
		if(iris_data->lockers[i]==NULL){
			verbose("Failed to allocate memory for iris lockers!\n");
			return;
		}
		int c;
		if((c=fread(iris_data->lockers[i],sizeof(uint8_t),crypto_auth_hmacsha512_BYTES+crypto_auth_hmacsha512_KEYBYTES,fd_p))!=96){
			verbose("Failed to read the locker[%d] and c is \n",i,c);
			return;
		}
		if(i==0){verbose("First byte of first locker 0x%x\n",iris_data->lockers[i][0]);}
	}

	//Force regeneration of the filters, this is intentionally slow
	//when both gen and rep are being run together to test
	//functionality
	if(iris_data->filter_populator !=NULL){
		free(iris_data->filter_populator);
		iris_data->filter_populator=NULL;
	}


	iris_data->filter_populator=malloc(sizeof(unsigned char)*crypto_secretstream_xchacha20poly1305_KEYBYTES);
	if(iris_data->filter_populator==NULL){
		verbose("Failed to allocate space");
		return;
	}

	for(i=0;i<crypto_secretstream_xchacha20poly1305_KEYBYTES;i++){
		iris_data->filter_populator[i]=pop_buff[i];
	}
	verbose("Done reading from the public file.\n");

}



void prepopulate_filters(iris * iris_data){
	unsigned int i=0;
	if(iris_data==NULL){
		verbose("Calling with unitialized data structure\n");
		return;
	}


	if(iris_data->filter_populator !=NULL){
		free(iris_data->filter_populator);
		iris_data->filter_populator=NULL;
	}
	iris_data->filter_populator = malloc(sizeof(unsigned char)*crypto_secretstream_xchacha20poly1305_KEYBYTES);
	if(iris_data->filter_populator==NULL){
		verbose("Failed to allocate space");
		return;
	}

	randombytes(iris_data->filter_populator,crypto_secretstream_xchacha20poly1305_KEYBYTES);
	verbose("Subset size: %i\n",iris_data->sub_len);
	verbose("Size of confident bits %u\n",iris_data->locs_len);
	if(iris_data->locs_len>0xFFFF){
		verbose("Too many confident bits for data structure\n");
		return;
	}
	for(i=0;i<iris_data->sub_len;i++){
		(iris_data->filter_preimage)[i] = randombytes_uniform(iris_data->locs_len);
	}
	qsort(iris_data->filter_preimage,iris_data->sub_len, sizeof(uint64_t), intcmp);

	verbose("Filter preimage:");
	for(i=0;i<iris_data->sub_len;i++){
		verbose("%u ",	(iris_data->filter_preimage)[i] );
	}
	verbose("\n");
	/*	verbose("\nFilter populator:\n");
		for(int i=0;i<crypto_secretstream_xchacha20poly1305_KEYBYTES;i++){
			verbose("%u\n",(unsigned int ) iris_data->filter_populator[i]);
		}*/
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


void * parallel_filter_pop(t_args * argument) {
	int index=0 ;
	uint64_t start_filter = 0 ;
	uint64_t stop_filter = 0 ;
	unsigned char nonce[crypto_stream_chacha20_NONCEBYTES];
	int numbers_to_gen = argument->numbers_to_gen;
	iris * iris_d = argument->iris_data;
	int bit_len_num = argument->bit_len_num;
	uint16_t ciphertext[numbers_to_gen];//These are 16 bit chunks
	uint64_t filter_num = 0;
	uint64_t cur_loc = 0;
	uint64_t filter_loc =0 ;
	uint64_t num_matches = 0;
	uint64_t trunc_num =0;
	uint64_t curr_val = 0;
	uint64_t output_len = 0;

	index= *(argument->index);
	*(argument->return_code)= -1;

	start_filter = (index)*iris_d->num_filters/NUM_THREADS;
	stop_filter = (index+1)*iris_d->num_filters/NUM_THREADS -1;
	if(stop_filter>iris_d->num_filters){
		verbose("Would exceed bounds End filter %u Num filter %u\n", stop_filter, iris_d->num_filters);
		return NULL;
	}
	//	printf("I should process filters between %u %u and %u\n", passed_in_value, start_filter, stop_filter);


	memset(nonce,0,crypto_stream_chacha20_NONCEBYTES);

	//	uint16_t output_len = 2*(iris_d->locs_len * iris_d->locs_len ) / (0xFFFF);
	output_len = numbers_to_gen;

	//	printf("The output len is %u\n", output_len);
	if(iris_d->locs_len>numbers_to_gen){
		verbose("Input data structure too long\n");
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
			if(trunc_num<(iris_d->locs_len)){
				num_matches++;
				//				printf("Filter preimage %d %d %d\n", (iris_d->filter_preimage)[filter_loc], num_matches, filter_loc);
				//TODO: the program had a serious problem when there was a repeat in the preimage list
				//right now this just puts another random match in the place which
				//may or may not be the right behavior, have to think about this
				//long term
				if(num_matches>=((iris_d->filter_preimage)[filter_loc])){
					iris_d->filters[filter_num][filter_loc] = trunc_num;
					filter_loc++;
				}
			}
			cur_loc++;
		}
		/*
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
		}*/
	}
	*(argument->return_code) = 0;
	return NULL;
}


//The purpose of this function is to repopulate the filters based on the actual random
//ness and the shared  key
int populate_filters_crypto(iris * iris_data){
	pthread_t threads[NUM_THREADS];
	int index_arr[NUM_THREADS];
	int result_code_arr[NUM_THREADS];
	int result_code = 0;
	unsigned int index;
	struct timespec start_time, stop_time;

	if(iris_data==NULL){
		verbose("Calling with uninitialized data structure\n");
		return -1;
	}
	if(iris_data->filter_populator==NULL || iris_data->filter_preimage== NULL){
		verbose("Calling out of order, unable to populate filters\n");
		return -1;
	}
	//	printf("Nonce size %u\n",crypto_stream_chacha20_NONCEBYTES);


	clock_gettime(CLOCK_REALTIME, &start_time);
	int bit_len_num = next_pow_2(iris_data->locs_len);
	int numbers_to_gen = (1<<bit_len_num) + NUM_SLACK;

	//Creating each filter individually
	unsigned int filter_num = 0;
	////	printf("The number of filters is %u\n",iris_data->num_filters);
	for(;filter_num<iris_data->num_filters;filter_num++){
		iris_data->filters[filter_num] = (uint64_t * ) calloc(iris_data->sub_len,sizeof(uint64_t*));
		if(!(iris_data->filters[filter_num])){
			verbose("Unable to allocate memory.\n");
			return -1;
		}

	}
	//	pthread_attr_t attr;
	//	unsigned int stacksize = 0;
	//	pthread_attr_init(&attr);
	//	pthread_attr_getstacksize(&attr, &stacksize);
	//	printf("Thread stack size = %d bytes \n", stacksize);

	// create all threads one by one
	t_args arguments[NUM_THREADS];
	for (index = 0; index < NUM_THREADS; ++index) {
		index_arr[index] = index;
		arguments[index].index = &(index_arr[index]);
		arguments[index].return_code = &(result_code_arr[index]);
		arguments[index].iris_data = iris_data;
		arguments[index].numbers_to_gen = numbers_to_gen;
		arguments[index].bit_len_num = bit_len_num;
		if(pthread_create(&(threads[index]), NULL, &parallel_filter_pop, &(arguments[index]))!=0){
			verbose("Thread returned with problem %u\n", index);
		}
	}
	// wait for each thread to complete
	for (index = 0; index < NUM_THREADS; ++index) {
		// block until thread 'index' completes
		pthread_join(threads[index],NULL);
		//printf("Result is %d\n",result_code_arr[index]);
	}
	for (index = 0; index < NUM_THREADS; ++index) {
		// block until thread 'index' completes
		if(result_code_arr[index]!=0){
			verbose("Return Code: %d\n",result_code_arr[index]);
			return -1;
		}
		//		printf("In main: thread %d has completed\n", index);
	}
	clock_gettime(CLOCK_REALTIME, &stop_time);
	verbose("Total time elapsed for filter creation: %u.%3u s\n", stop_time.tv_sec - start_time.tv_sec, stop_time.tv_nsec - start_time.tv_nsec);

	return 0;
}
int populate_filters(iris * iris_data){ return populate_filters_crypto(iris_data);}

