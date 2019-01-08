#include "FuzzyExtractor.h"
#include <dirent.h>
#include <string.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <sodium.h>
#include "FuzzyPack.h"
#include "FEGen.h"
#include "FERep.h"
#include <time.h>
#include <errno.h>
#include <stdbool.h>
#include <stdarg.h>
#include <unistd.h>
#define NUM_THREADS 1
bool VERBOSE = true;


int  gen_and_serialize(iris * iris_data,iris_array_input * data,FILE *fw,uint8_t ** key );
int rep_and_serialize(iris*, FILE*,iris_array_input * ,uint8_t **recovered_key,int choice_num);
int choice2(FILE *pub, iris* iris_data,iris_array_input * data,uint8_t ** recovered_key,int choice_num);
int choice1(const char * pub, iris* iris_data,iris_array_input  * data, uint8_t ** gen_key);


void setVerbose(bool setting) {
	VERBOSE = setting;
}

int verbose(const char * restrict format, ...) {
	if( !VERBOSE )
		return 0;
	va_list args;
	va_start(args, format);
	int ret = vprintf(format, args);
	va_end(args);
	return ret;
}

int within_range(float val, Confidence conf){
	return ((val < conf.highpos && val > conf.lowpos) || (val < conf.highneg && val > conf.lowneg));

}
int conf_levels(float val){
	Confidence lev1= {1206,828,-879,-1522};
	Confidence lev2= {1522,676,-654,-1726};
	Confidence lev3= {1726,540,-513,-2132};
	Confidence lev4= {2132,437,-399,-2132};
	Confidence lev5= {2132, 343, -307, -2132};
	if(within_range(val,lev5)){ return 5; }
	if(within_range(val,lev4)){ return 4; }
	if(within_range(val,lev3)){ return 3; }
	if(within_range(val,lev2)){ return 2; }
	if(within_range(val,lev1)){ return 1;}

	return 0;
}

int bit_value(float val){
	if(val <= 0)
		return 0;
	else
		return 1;
}


void checkAlloc(int *v){
	if(v==NULL){
		verbose("Failed to allocate memory");
		exit(1);
	}
}

// check the json file format
int checkFormat(FILE * fp, int i){ 

	int c;
	//checking the first 2 brackets
	if ((c=fgetc(fp))!='[' || (c=fgetc(fp))!='['){
		verbose("File %d does not have the right format!\n",i);
		fclose(fp);
		//free(fp);
		return -1;
	}
	//checking the floats
	float fptemp;
	int d=fscanf(fp, "%f, ", &fptemp);
	while(d!=0 && d!=EOF){
		d=fscanf(fp, "%f, ", &fptemp);
	}
	//checking the ending bracket
	if((c=fgetc(fp))!=']'|| (c=fgetc(fp)) != ']'){
		verbose("File %d does not have the right format!\n",i);
		fclose(fp);
		//	free(fp);
		return -1;
	}
    return 0;
}



iris_array_input * readArray(FILE* fp, Confidence conf){

	size_t length = 32768;
	float intermediateVector[length*sizeof(float)];
	FILE * fp_mask;
	char * line=NULL;
	size_t len=0;
	int size =0;
	iris_array_input * data = malloc(sizeof(struct iris_array_struct));
	printf("The size of the allocation is %u\n",sizeof(struct iris_array_struct));
	if(data==NULL){verbose("Failed to allocate memory\n"); exit(1);}
	size_t charsRead = 0;
	char x,y ;


	//	const char * mask_file="/Iris/IrisCorpus/ND_merge/output/mask_vec";
	/* Initialize and read mask vector
	 *
	 */
	const char * mask_file="./mask_vec";
	if((fp_mask=fopen(mask_file,"r"))==NULL){
		verbose("Failed to open mask vector.\n");
		exit(1);
	}
	char mask_buff[length];
	//char mask_buff[data.length];
	for (int i=0;i<length;i++){
		fscanf(fp_mask,"%c ", &mask_buff[i]);
	}
	fclose(fp_mask);

	x = fgetc(fp);
	y = fgetc(fp);
	if(x!=91 || x!=91){
		verbose("Error in parsing input file\n");
		exit(1);
	}

	while(0!= fscanf(fp, "%f, ", &intermediateVector[charsRead])){ charsRead++; }
	if(charsRead!=length){
		verbose("Error in parsing input file\n");
		exit(1);
	}
	data->length = 32768;
	for(int j = 0; j<data->length; j++){
		data->conf_level[j] = conf_levels(intermediateVector[j]);
		data->vector[j]= bit_value(intermediateVector[j]);
		data->conf[j]= (within_range(intermediateVector[j], conf)) & (mask_buff[j]=='1');
	}
	fclose(fp);

	verbose("Done reading the array.\n");
	printf("The data length is %u\n",data->length);
	return data;
}

// open file and check format
FILE * Check_File(const char * file,int i){
	FILE * fp;
	//check if file i was opened without errors
	if ( (fp = fopen(file, "r")) == NULL ){
		verbose("I could not open file named %s!\n",file);
		perror("Error");
		return NULL;
	}
	//check if the file has the right format
	if(-1== checkFormat(fp,i)){ return NULL;}

	//reset the pointer to the beginning of the file
	fseek(fp, 0, SEEK_SET);
	//return the json file pointer
	return fp;
}



//User choice 1
int choice1(const char * pub, iris* iris_data,iris_array_input * data, uint8_t ** gen_key){
	//uint8_t *gen_key;

	verbose("Made the iris\n");
	//open the txt file to write
	FILE *fw=fopen(pub, "w");
	//check if the file was opened successfully
	if(fw==NULL){
		verbose("Failed to open the file to write\n");
		return -1;
	}
	//check if gen_and_serialize didn't fail
	if((gen_and_serialize(iris_data,data,fw,gen_key))!=0){
		verbose("Failed to generate.\n");
		return -1;
	}
	printf("The generated key pointer is %x\n",*gen_key);
	//avoid the fread/fwrite conflict
	fflush(fw);
	//close the file
	fclose(fw);
	return 0;
}



//User choice 2
int choice2(FILE *pub, iris* iris_data,iris_array_input * data,uint8_t **recovered_key, int choice_num){
	verbose("Remade the iris\n");
	uint8_t*  rec;
	//open the txt file to read
	FILE *fr=fopen(pub,"r");
	//check if the file was opened successfully
	if(fr==NULL){
		verbose("Failed to open the file to read\n");
		return -1;}
	if((rep_and_serialize(iris_data,fr,data,recovered_key, choice_num))!=0){
		verbose("Rep and serialize failed\n");
		return NULL;
	}
	//close the file
	fclose(fr);
	return 0;
}	

//get the confidence vector
void get_confvec(FILE *pub,iris_array_input data){
	FILE *fr=fopen(pub,"r");
	//check if the file was opened successfully
	if(fr==NULL){
		verbose("Failed to open the file to read\n");
		return;
	}
	read_confvec(fr,data);
	fflush(fr);
	fclose(fr);
}




int main(int argc, const char* argv[]){
	//checking command line
	if (argc <4){
		fprintf(stderr,"Usage: %s [1 for Gen |2 for Rep |3 for both] [public_file] [json_files]\n", argv[0]);
		exit(1);
	}

	// debugging mode when adding "-v" at the end of command line
	if (argc>2 && !strcmp(argv[argc-1], "-v")){
		setVerbose(true);
	}
	FILE * fp;
	iris_array_input * dataG;
	iris_array_input * data;
	iris * iris_data;
	iris * iris_dataG; // iris data of gen
	uint8_t* recovered_key=NULL; // key returned from Rep
	uint8_t * gen_key=NULL; // key generated in gen
	uint64_t ** temp_filters;
	int  user_choice=atoi(argv[1]);
	uint64_t num_filters=100000;
	uint64_t sub_size=16;
	Confidence conf = {2132, 343, -307, -2132};

	switch(user_choice){
	case(1):
	/* Gen
				check the number of arguments given*/
	  if(argc<4){
	  	fprintf(stderr,"Usage: %s [1] [public_file] [json_file]\n",argv[0]);
	  	exit(1);
	  }
	  //open the public file and call gen_serialize to write to it
	  verbose("User choice: Generate\n");
	  fp=Check_File(argv[3],1);
	  data = readArray(fp, conf);
	  iris_data = make_iris(data, num_filters,sub_size);
	  printf("The pointer here is 0x%x\n",iris_data);
	  choice1(argv[2],iris_data,data,&gen_key);
	  break;
	case(2):
	  /*Rep
      check the number of arguments given*/
	  if(argc<4){
	    fprintf(stderr,"Usage: %s [2] [public_file] [json_file]\n",argv[0]);
	    exit(1);
	  }
	  //open the public the file and call rep and serialize to read from it
	  verbose("\nUser choice: Reproduce\n");
	  fp=Check_File(argv[3],1);
	  data = readArray(fp, conf);
	  get_confvec(argv[2],*data);
	  iris_data = make_iris(data,num_filters, sub_size);
	  if((choice2(argv[2],iris_data,data,&recovered_key,2))!=0){
		  verbose("Reproduce Failed\n");
	  }
	  break;
	case(3):
	  /*gen then rep*/
	  //check the number of arguments given
	  if( argc <5){
	    fprintf(stderr,"Usage: %s [3] [public_file] [json_file] [json_file]\n",argv[0]);
	    exit(1);
	  }
	//generate with the first json file
	  verbose("\nUser choice: Generate and Reproduce\n");
	  fp=Check_File(argv[3],1);
	  dataG = readArray(fp, conf);
	  iris_dataG = make_iris(dataG, num_filters,sub_size);
	  choice1(argv[2],iris_dataG,dataG,&gen_key);

   	//reproduce with the second json file
	  verbose("\n************************************\n");
	  fp=Check_File(argv[4],2);
	  data = readArray(fp, conf);
	//getting the confidence vector from the public value before making the iris
	  get_confvec(argv[2],*data);
	//remaking the iris made in Gen
	  remake_iris(data,dataG,iris_dataG,num_filters,sub_size);
	  choice2(argv[2],iris_dataG,data,&recovered_key,3);
	  free(data);
	  data=NULL;
	  free(dataG);
	  dataG=NULL;
	  free_iris(iris_dataG,0);
	  break;
//
//	case(4): // pass a directory
//	  if( argc <4){
//		  fprintf(stderr,"Usage: %s [4] [public_file] [json files_directory]\n",argv[0]);
//		  exit(1);
//	  }
//	  verbose("\nUser choice: Generate first file and Reproduce the rest\n");
//	  int i=0;
//	  struct dirent *pDirent_files, *pDirent_ID, *pDirent_EYE;
//	  DIR *pDir_Mas, *pDir_ID, *pDir_EYE;
//	  pDir_Mas=opendir(argv[3]);  // open the master directory passed as argument
//	  if (pDir_Mas==NULL){        // check the success of opening the master directory
//		verbose("Failed to open Master Directory!\n");
//		return -1;
//	  }
//	//  check the existence of the data file and remove it
//	  if((access("/home/mariem/IrisFe/data/dist_rep_time.txt",F_OK)==0)&&(remove("/home/mariem/IrisFe/data/dist_rep_time.txt"))!=0){
//		verbose("Deleting data file failed.\n");
//	  }
//	// go through the persons' directory
//	  while((pDirent_ID =readdir(pDir_Mas)) != NULL){
//	    char path_ID[1024];
//		strcpy(path_ID,argv[3]);
//		if (path_ID[strlen(path_ID) - 1] != '/') {strcat(path_ID, "/");}
//		strcat(path_ID, pDirent_ID->d_name);
//		if(pDirent_ID->d_name[0]=='.') { continue;}
//		pDir_ID=opendir(path_ID);  // open person's directory
//		// check the success of opening the person's directory
//		if (pDir_ID==NULL){
//			verbose("Failed to open Person's Directory %s !\n",path_ID);
//			return -1;
//		}
//		//go through the person's eye directory
//		while((pDirent_EYE=readdir(pDir_ID))!=NULL){
//		  char path_EYE[1024];
//		  strcpy(path_EYE,path_ID);
//		  if (path_EYE[strlen(path_EYE) - 1] != '/') {strcat(path_EYE, "/");}
//		  strcat(path_EYE, pDirent_EYE->d_name);
//		  if(pDirent_EYE->d_name[0]=='.') { continue;}
//		  pDir_EYE=opendir(path_EYE);
//		  if(pDir_EYE==NULL){
//			verbose("Failed to open Person's EYE directory!");
//			return -1;
//		  }
//		// initialize run_gen to 0 when opening new directory of files
//		  int run_gen=0;
//		  iris * iris1_data;
//		  iris_array_input dataG;
//		  while((pDirent_files=readdir(pDir_EYE))!=NULL){
//			iris_array_input data;
//			char json_file[250];
//			strcpy(json_file, path_EYE);
//			if (json_file[strlen(json_file) - 1] != '/'){
//				strcat(json_file, "/");
//			}
//			strcat(json_file, pDirent_files->d_name);
//			if (pDirent_files->d_name[0]=='.'){ continue; }
//			if((fp=Check_File(json_file,(i+1)))==NULL) {continue;}
//			if(run_gen==0){  //run gen for the first file in the directory
//				dataG = readArray(fp, conf);
//				iris1_data = make_iris(&dataG, num_filters,sub_size);
//				choice1(argv[2],iris1_data,dataG,&gen_key);
//				// update run_gen
//				run_gen=1;
//			}
//			else if (run_gen==1){ // run rep for the rest of the files
//				data = readArray(fp, conf);
//				get_confvec(argv[2],data);
//				remake_iris(&data,&dataG,iris1_data,num_filters,sub_size);
//				choice2(argv[2],iris1_data,data,&recovered_key,4);
//				if(data.vector) {free(data.vector);	}
//				if(data.conf)   {free(data.conf);}
//				if(data.conf_level) {free(data.conf_level);}
//			}
//			i++;
//		  }
//		  if(iris1_data){free_iris(iris1_data,1);}
//		  if(dataG.conf){free(dataG.conf);}
//		  if(dataG.vector){ free(dataG.vector);}
//		  if(dataG.conf_level) {free(dataG.conf_level);}
//
//		  closedir(pDir_EYE);
//		}
//		closedir(pDir_ID);
//	}
//	closedir(pDir_Mas);
//	verbose("Number of json files tested is %d\n", i);
//	break;

	default:
		printf("Unknown Option!\nEnter '1' for Generate, '2' for Reproduce,'3' for Generate then Reproduce, and '4' to pass a directory.\n");
		exit(1);
	}


	if((gen_key!=NULL)&&(recovered_key!=NULL)){
		unsigned int j,match=0;
		for(j=0;j<32;j++){
			if(gen_key[j]==recovered_key[j]){
				match++;
			}
		}
		if (match==32){
			printf("Keys match!\n");
		}else{
			printf("Keys don't match!\n");
		}

	}
	if(gen_key){
		free(gen_key);
	}
	if(recovered_key){free(recovered_key);}


	if(user_choice ==1 || user_choice ==2){
		free_iris(iris_data,0);
		if(data!=NULL){ free(data); data = NULL;}
	}
	return 0;
}
