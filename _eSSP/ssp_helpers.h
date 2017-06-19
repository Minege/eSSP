
#ifndef BASIC_DEMO6_SSP_HELPERS_H
#define BASIC_DEMO6_SSP_HELPERS_H

#ifdef WIN32
#include "port_win32_ssp.h"
#else
#include "port_linux.h"
#endif

#include <stdio.h>

#define SSP_CMD_RUN_CALIBRATION 0x48
#define SSP_CMD_SET_COINMECH_INHIBITS 0x40
#define SSP_CMD_PAYOUT_NOTE 0x42
#define SSP_CMD_STACK_NOTE 0x43
#define SSP_CMD_PAYOUT_VALUE 0x33



#define SSP_POLL_CALIBRATION_FAIL 0x83
#define SSP_POLL_SMART_EMPTYING 0xB3
#define SSP_POLL_SMART_EMPTIED 0xB4
#define SSP_POLL_STORED 0xDB
#define SSP_POLL_DISPENSING 0xDA
#define SSP_POLL_DISPENSED 0xD2
#define SSP_POLL_JAMMED 0xD5
#define SSP_POLL_HALTED 0xD6
#define SSP_POLL_FLOATING 0xD7
#define SSP_POLL_FLOATED 0xD8
#define SSP_POLL_TIMEOUT 0xD9
#define SSP_POLL_CASHBOX_PAID 0xDE
#define SSP_POLL_COIN_CREDIT 0xDF


#define SSP6_OPTION_BYTE_TEST 	0x19
#define SSP6_OPTION_BYTE_DO		0x58



#define PRINT_CMD(_sspC) do { 						\
	int _i; 										\
	printf("cmd: ");								\
	for (_i=0; _i<_sspC->CommandDataLength; _i++) 	\
		printf ("0x%02x ", _sspC->CommandData[_i]); \
	printf("\n"); 									\
} while (0)
#define PRINT_RSP(_sspC) do { 						\
	int _i;											\
	printf("rsp: ");								\
	for (_i=0; _i<_sspC->ResponseDataLength; _i++) 	\
		printf ("0x%02x ", _sspC->ResponseData[_i]);\
	printf("\n"); 									\
} while (0)


typedef struct {
    unsigned char event;
    unsigned long data1;
    unsigned long data2;
    char cc[4];
} SSP_POLL_EVENT6;

typedef struct {
    SSP_POLL_EVENT6 events[20];
    unsigned char event_count;
} SSP_POLL_DATA6;

typedef struct {
    unsigned char security;
    unsigned int value;
    char cc[4];
} SSP6_CHANNEL_DATA;

typedef struct {
    unsigned char UnitType;
    char FirmwareVersion[5];
 //   char CountryCode[4];
 //   unsigned long ValueMultiplier;
    unsigned int NumberOfChannels;
    SSP6_CHANNEL_DATA ChannelData[20];
    unsigned long RealValueMultiplier;
    unsigned char ProtocolVersion;
}SSP6_SETUP_REQUEST_DATA;

enum calibration_failures {
    NO_FAILUE=0x00,
    SENSOR_FLAP=0x01,
    SENSOR_EXIT=0x02,
    SENSOR_COIL1=0x03,
    SENSOR_COIL2=0x04,
    NOT_INITIALISED=0x05,
    CHECKSUM_ERROR=0x06,
    COMMAND_RECAL=0x07
};

enum channel_state {
    DISABLED=0x00,
    ENABLED=0x01
};


SSP_RESPONSE_ENUM ssp6_payout(SSP_COMMAND *sspC, const int value, const char *cc, const char option);
SSP_RESPONSE_ENUM ssp6_set_route(SSP_COMMAND *sspC, const int value, const char *cc, const char route);
SSP_RESPONSE_ENUM ssp6_sync(SSP_COMMAND *sspC);
SSP_RESPONSE_ENUM ssp6_setup_encryption(SSP_COMMAND *sspC,const unsigned long long fixedkey);
SSP_RESPONSE_ENUM ssp6_host_protocol(SSP_COMMAND *sspC,const unsigned char host_protocol);
SSP_RESPONSE_ENUM ssp6_setup_request(SSP_COMMAND *sspC, SSP6_SETUP_REQUEST_DATA *setup_request_data);
SSP_RESPONSE_ENUM ssp6_enable(SSP_COMMAND *sspC);
SSP_RESPONSE_ENUM ssp6_enable_payout(SSP_COMMAND *sspC, const char type);
SSP_RESPONSE_ENUM ssp6_set_inhibits(SSP_COMMAND *sspC,const unsigned char lowchannels, const unsigned char highchannels);
SSP_RESPONSE_ENUM ssp6_poll(SSP_COMMAND *sspC, SSP_POLL_DATA6 * poll_response);
SSP_RESPONSE_ENUM ssp6_reset(SSP_COMMAND *sspC);
SSP_RESPONSE_ENUM ssp6_disable_payout(SSP_COMMAND *sspC);
SSP_RESPONSE_ENUM ssp6_disable(SSP_COMMAND *sspC);
SSP_RESPONSE_ENUM ssp6_stack_note(SSP_COMMAND *sspC);
SSP_RESPONSE_ENUM ssp6_payout_note(SSP_COMMAND *sspC);
SSP_RESPONSE_ENUM ssp6_run_calibration(SSP_COMMAND *sspC);
SSP_RESPONSE_ENUM ssp6_set_coinmech_inhibits(SSP_COMMAND *sspC, unsigned int value, const char *cc, enum channel_state state);

#endif
