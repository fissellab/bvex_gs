#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <arpa/inet.h>
#include <netinet/in.h>

#include "file_io_Oph.h"
#include "server.h"
#include "lens_adapter.h"
#include "astrometry.h"
#include "motor_control.h"
#include "ec_motor.h"

struct sockaddr_in cliaddr;
int tel_server_running = 0;
int stop_tel = 0;
FILE* server_log;

extern struct astrometry all_astro_params;
extern struct camera_params all_camera_params;

void sendString(int sockfd, char* string_sample){

	sendto(sockfd, (const char*) string_sample, strlen(string_sample), MSG_CONFIRM,(const struct sockaddr *) &cliaddr, sizeof(cliaddr));
	return;
}

void sendInt(int sockfd, int sample){
	char string_sample[6];

	snprintf(string_sample,6,"%d",sample);
        sendto(sockfd, (const char*) string_sample, strlen(string_sample), MSG_CONFIRM,(const struct sockaddr *) &cliaddr, sizeof(cliaddr));
        return;
}

void sendFloat(int sockfd, float sample){
        char string_sample[10];

        snprintf(string_sample,10,"%f",sample);
        sendto(sockfd, (const char*) string_sample, strlen(string_sample), MSG_CONFIRM,(const struct sockaddr *) &cliaddr, sizeof(cliaddr));
        return;
}

void sendDouble(int sockfd,double sample){
	char string_sample[10];

	snprintf(string_sample,10,"%lf",sample);
	sendto(sockfd, (const char*) string_sample, strlen(string_sample), MSG_CONFIRM,(const struct sockaddr *) &cliaddr, sizeof(cliaddr));
	return;
}

//Initialize the socket
int init_socket(){
	int sockfd = socket(AF_INET,SOCK_DGRAM,0);
	struct timeval tv;

	tv.tv_sec = 0;
	tv.tv_usec = config.server.timeout;

	if(sockfd < 0){
		write_to_log(server_log,"server.c","init_socket","Socket creation failed");
	}else{
		tel_server_running = 1;

		memset(&cliaddr,0, sizeof(cliaddr));
		cliaddr.sin_family = AF_INET;
		cliaddr.sin_port = htons(config.server.port);
		cliaddr.sin_addr.s_addr = inet_addr(config.server.ip);
		setsockopt(sockfd,SOL_SOCKET,SO_RCVTIMEO,&tv,sizeof(tv));

		write_to_log(server_log,"server.c","init_socket","Telemetry started scucessfull");
	}

	return sockfd;
}

//listen for requests
void sock_listen(int sockfd, char* buffer){

	int n , len;
	n = recvfrom(sockfd, buffer,MAXLEN, MSG_WAITALL, (struct sockaddr *) &cliaddr, &len);

	buffer[n] = '\0';

	return;
}

//check if metric exists if so send the corresponding value
void send_metric(int sockfd, char* id){
	// add channels using the format below here;
	//Star Camera channels

	if(strcmp(id,"sc_ra")==0){
		sendDouble(sockfd,all_astro_params.ra);
	}else if(strcmp(id,"sc_dec")==0){
		sendDouble(sockfd,all_astro_params.dec);
	}else if(strcmp(id,"sc_fr")==0){
                sendDouble(sockfd,all_astro_params.fr);
        }else if(strcmp(id,"sc_ir")==0){
                sendDouble(sockfd,all_astro_params.ir);
        }else if(strcmp(id,"sc_alt")==0){
                sendDouble(sockfd,all_astro_params.alt);
        }else if(strcmp(id,"sc_az")==0){
                sendDouble(sockfd,all_astro_params.az);
        }else if(strcmp(id,"sc_texp")==0){
                sendDouble(sockfd,all_camera_params.exposure_time);
        }else if(strcmp(id,"sc_start_focus")==0){
                sendInt(sockfd,all_camera_params.start_focus_pos);
        }else if(strcmp(id,"sc_end_focus")==0){
                sendInt(sockfd,all_camera_params.end_focus_pos);
        }else if(strcmp(id,"sc_curr_focus")==0){
                sendInt(sockfd,all_camera_params.focus_position);
        }else if(strcmp(id,"sc_focus_step")==0){
                sendInt(sockfd,all_camera_params.focus_step);
        }else if(strcmp(id,"sc_focus_mode")==0){
                sendInt(sockfd,all_camera_params.focus_mode);
        }else if(strcmp(id,"sc_solve")==0){
                sendInt(sockfd,all_camera_params.solve_img);
        }else{
		fprintf(server_log,"[%ld][server.c][send_metric] Received unkown request: %s",time(NULL),id);
	}

}

void *do_server(){

	int sockfd = init_socket();
	char buffer[MAXLEN];

	if(tel_server_running){
		while(!stop_tel){
			sock_listen(sockfd, buffer);
			send_metric(sockfd, buffer);
		}
		write_to_log(server_log,"server.c","do_server","Shutting down server");
		tel_server_running = 0;
		stop_tel = 0;
		fclose(server_log);
		close(sockfd);
	}else{
		write_to_log(server_log,"server.c","do_server","Could not start server");
		fclose(server_log);
	}
}
