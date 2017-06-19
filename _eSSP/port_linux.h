#ifndef BASIC_DEMO6_LINUX_H
#define BASIC_DEMO6_LINUX_H

#ifdef INCLUDED_PORT
#error "Multiple ports included"
#endif
#define INCLUDED_PORT

#include "inc/SSPComs.h"

// Linux does not need to do any initialisation for the SSP library
#define init_lib()

void changemode(int dir);
int kbhit (void);

int open_ssp_port (const char *port);
void close_ssp_port ();
int send_ssp_command(SSP_COMMAND *sspC);
int negotiate_ssp_encryption(SSP_COMMAND *sspC, SSP_FULL_KEY * hostKey);

#endif
