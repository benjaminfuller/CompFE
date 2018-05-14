#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>
#include "FuzzyPack.h"
#include "FuzzyExtractor.h"

/* Made from input file:
 * eye_vec, conf_vec, num_filters, length, pad_len, conf_locs, locs_len, sub_len
 * 
 * Made from gen, but in iris_public struct:
 * filters, hmac_key, conf_vec, priv_key, hmac_key_len, priv_key_len
 *
 * Made from gen, can be made using iris_public and iris_pack with same eye input and rep
 * priv_key
 */


/*typedef struct {
	char **hashes;
	char *hmac_key;
	int *conf_vec;
	uint16_t **filters;
	uint64_t num_filters;
	uint64_t hashes_count;
} iris_public;

typedef struct {
	uint64_t *bits;
	uint64_t length;
	//Length stores the total length of important information
	//pad_len stores the next multiple of 64 so pad_len/64 is the actual
	//length of bits
	uint64_t pad_len;
} packed_bits;*/


iris* alloc_iris(){
	return (iris*)calloc(1, sizeof(iris_pack));
}

void free_iris(iris *targ){
	//error checking, its a pain but important
	for(unsigned int i = 0; i < targ->num_filters; i++){
		free(targ->filters[i]);
		free(targ->lockers[i]);
	}
	free(targ->eye_vec);
	free(targ->conf_vec);
	free(targ->filters);
	free(targ->lockers);
//	free(targ->hmac_key);
	free(targ->priv_key);
	free(targ->filter_populator);
	free(targ->filter_preimage);
	free(targ);
}

packed_bits* alloc_packed_bits(){
	return (packed_bits*)calloc(1,sizeof(packed_bits));
}

void free_packed_bits(packed_bits *targ){
	free(targ->bits);
	free(targ);
}

void filter_eye(uint64_t *eye, uint64_t *filt, uint64_t *buf, uint64_t len){
	uint64_t test = 0;
	for(int i=0; i<len; i++){
		buf[i] = eye[i] & filt[i];
	}
}

uint8_t pack_8b_segment(int *src){
	uint8_t n = 0;
	for(int i = 0; i<8; i++){
		//		printf("%u", src[i]);
		n += (src[i] << (7-i));
	}
	//	printf("\n");
	//printf("n is %i\n", n);
	return n;
}

uint64_t pack_64b_segment(int *src){
	//Takes values from and array of 64 chars of either 1 or 0 and packs them into a
	//single uint64_t
	//	for(int i=0; i<64;i++){
	//		printf("%u",src[i]);
	//	}
	//	printf("\n");
	uint64_t dest = 0;
	uint8_t shift = 0;
	//	printf("printing dest\n");
	//	for(int j=0;j<64; j++){
	//		printf("%u", (dest>>(64-j))%2);
	//	}
	//	printf("\n");
	for(int i = 0; i<8; i++){
		uint8_t n= pack_8b_segment(src+(8*i));
		shift = 8*(7-i);
		dest+= ((uint64_t) n)<<shift;
		//		printf("printing dest\n");
		//		for(int j=0;j<64; j++){
		//			printf("%u", (dest>>(63-j))%2);
		//		}
		//		printf("\n");
	}
	return dest;
}

packed_bits* pack_bits(int *src, size_t src_len) {
	uint64_t *dest = (uint64_t * ) calloc((src_len/64)+1, sizeof(uint64_t));
	for(size_t i=0; i<src_len/64; i++){
		dest[i] = pack_64b_segment(src+(64*i));
		//		printf("Packed bits %u %i\n", dest[i], i);
		//		break;
	}
	uint64_t bit = 0;
	for(size_t i=64*(src_len/64); i<src_len; i++){
		bit = (uint64_t) src[i];
		bit = bit << (i % 64);
		dest[i/64] += bit;
		bit = 0;
	}
	packed_bits *pack = alloc_packed_bits();
	pack->bits = dest;
	pack->length = src_len;
	pack->pad_len = 64*((src_len/64)+1);
	//	printf("Pad Length %u\n",pack->pad_len);
	//	printf("Length%u\n",pack->length);
	return pack;

}

uint64_t count_conf_bits(int *vector, int length){
	uint64_t count = 0;
	for(size_t i = 0; i<(size_t)length; i++){
		if(vector[i])
			count++;
	}
	//printf("Num conf: %lld", count);
	return count;
}

int* conf_condense(int *vec, int *conf, uint64_t conf_len){
	int* condensed = (int*)calloc(conf_len,sizeof(int));
	int conf_found = 0;
	int weight_conf =0 ;
	for(int i = 0; i<conf_len; i++){
		if(vec[conf[i]]==1){
			condensed[conf_found] = 1;
			weight_conf++;
		}
		conf_found+=1;
	}
	printf("Weight of confident bits %i\n", weight_conf);
	return condensed;
}

iris* make_iris(iris_array_input *src, uint64_t num_filters, uint64_t subsel_size){
	uint64_t conf_len = count_conf_bits(src->conf, src->length);
	printf("Number of conf bits %i\n", conf_len);
	int *condensed = conf_condense(src->vector,src->conf,conf_len);
	//    for(int i= 0; i< conf_len; i++){
	//    		printf("Conf bits %i\n", condensed[i]);
	//    }
	packed_bits *pack_vec = pack_bits(condensed, conf_len);
	int *conf_copy = (int*)malloc(sizeof(int)*(src->length));
	memcpy(conf_copy,src->conf, sizeof(int)*(src->length));
	iris *eye = alloc_iris();
	eye->eye_vec = pack_vec->bits;
	eye->length = pack_vec->length;
	eye->pad_len = pack_vec->pad_len;
	eye->locs_len = conf_len;
	eye->num_filters = num_filters;
	eye->filter_preimage = (uint16_t*) calloc(subsel_size, sizeof(uint64_t));
	eye->sub_len = subsel_size;
	eye->conf_vec = conf_copy;
	eye->input_len = src->length;
	eye->filters = (uint64_t**)calloc(num_filters, sizeof(uint64_t*));
	eye->lockers = (uint8_t**)calloc(num_filters, sizeof(uint8_t*));
	free(condensed);
	free(pack_vec);
	return eye;
}
