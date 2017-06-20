#include "inc/SSPComs.h"
#include "port_linux.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

SSP_COMMAND *ssp_init(char *port_c, char *addr_c, bool debug)
{
    SSP_COMMAND* sspC = malloc(sizeof(SSP_COMMAND));
    
    sspC->SSPAddress = (int)(strtod(addr_c, NULL));
    // Linux does not need to do any initialisation for the SSP library
    sspC->Timeout = 1000;
    sspC->EncryptionStatus = NO_ENCRYPTION; // But there is an encryption
    sspC->RetryLevel = 3;
    sspC->BaudRate = 9600;
    sspC->Key.EncryptKey = 1;   // Just to make sure 
    //Open the COM port
    if ( debug == true ){ 
	    printf("PORT: %s\n", port_c); // Printing the connection informations

	    printf ("##%s##\n", port_c);
    }

    if (open_ssp_port(port_c) == 0)
    {
	printf("Port Error\n");
	return NULL;
    }
     

    //run_validator(&sspC);
    // close the com port
    //close_ssp_port();
    
    return sspC;
}

unsigned char* ssp_get_response_data(SSP_COMMAND* sspc)
{
    return sspc->ResponseData;
}
