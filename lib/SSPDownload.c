
#include "ITLSSPProc.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>


#include "Random.h"
#include "Encryption.h"
#include "../inc/SSPComs.h"
#include "serialfunc.h"
#include "../inc/ssp_defines.h"
#include <pthread.h>
unsigned char download_in_progress;
unsigned long download_block;
/*
Name:   DownloadDataToTarget
Inputs:
    char * data: The array of data you wish to download
    long data_length: length of data to download
    char * port: The name of the port to use (eg /dev/ttyUSB0 for usb serial, /dev/ttyS0 for com port 1)
    unsigned char sspAddress: The ssp address to download to
Return:
    If the value is less than 0x100000 it is the number of blocks to be downloaded.
    On an error, the value will be greater than 0x100000, and one of the following
    Failure:
    OPEN_FILE_ERROR					0x100001
    READ_FILE_ERROR					0x100002
    NOT_ITL_FILE					0x100003
    PORT_OPEN_FAIL					0x100004
    SYNC_CONNECTION_FAIL			0x100005
    SECURITY_PROTECTED_FILE			0x100006
    DATA_TRANSFER_FAIL				0x100010
    PROG_COMMAND_FAIL				0x100011
    HEADER_FAIL						0x100012
    PROG_STATUS_FAIL				0x100013
    PROG_RESET_FAIL					0x100014
    DOWNLOAD_NOT_ALLOWED			0x100015
    HI_TRANSFER_SPEED_FAIL			0x100016
Notes:
    The download is done in a seperate thread - see GetDownloadStatus() for information about its progress
    Only one download operation may be in progress at once.
*/
int  DownloadDataToTarget(const unsigned char* data, const unsigned long dlength, const char * cPort, const unsigned char sspAddress, const unsigned long long key)
{

	int i;
	unsigned long numCurBytes;
	unsigned short dBlockSize;
    ITL_FILE_DOWNLOAD * itlFile;
    SSP_COMMAND sspC;
    SSP_PORT port;
    if (download_in_progress == 1)
        return PORT_OPEN_FAIL;
    itlFile = malloc(sizeof(ITL_FILE_DOWNLOAD));
    itlFile->fData = malloc(dlength);
    memcpy(itlFile->fData,data,dlength);

	/*ramStatus.currentRamBlocks = 0;
	ramStatus.ramState = rmd_RAM_DOWNLOAD_IDLE;
	ramStatus.totalRamBlocks = 0;
*/

    download_block = 0;
	// check for ITL BV/SH type file
    if (itlFile->fData[0] == 'I' && itlFile->fData[1] == 'T' && itlFile->fData[2] == 'L') {

		 numCurBytes = 0;
		 for(i = 0; i <4; i++){
			numCurBytes += (unsigned long)itlFile->fData[17 + i] << (8*(3-i));
		 }
		  //get the block size from header
		 dBlockSize = (256*(unsigned short)itlFile->fData[0x3e]) + (unsigned short)itlFile->fData[0x3f];
		// correct for NV9 type
		 if(dBlockSize == 0) dBlockSize = 4096;

		  itlFile->NumberOfBlocks = numCurBytes / dBlockSize;
		  if(numCurBytes % dBlockSize != 0) itlFile->NumberOfBlocks += 1;
	}
	else{
		free(itlFile->fData);
		free(itlFile);
		return NOT_ITL_FILE;
	}

	/* check target connection   */
	sspC.Timeout = 1000;
	sspC.BaudRate = 9600;
	sspC.RetryLevel = 2;
	sspC.SSPAddress = sspAddress;
	itlFile->SSPAddress = sspAddress;
	port = OpenSSPPort(cPort);
	strcpy(itlFile->portname,cPort);
	itlFile->port = port;
	if (port == -1)
	{
        free(itlFile->fData);
		free(itlFile);
		return PORT_OPEN_FAIL;
	}
	sspC.EncryptionStatus = 0;
	sspC.CommandDataLength = 1;
	sspC.CommandData[0]  = SSP_CMD_SYNC;

	if (SSPSendCommand(port,&sspC) == 0){
        CloseSSPPort(port);
		free(itlFile->fData);
		free(itlFile);
		return SYNC_CONNECTION_FAIL;
	}
	if(sspC.ResponseData[0] != SSP_RESPONSE_OK){
		CloseSSPPort(port);
		free(itlFile->fData);
		free(itlFile);
		return SYNC_CONNECTION_FAIL;
	}
	if (key > 0)
	{
        if (NegotiateSSPEncryption(port,sspAddress,&itlFile->Key) == 0)
        {
            CloseSSPPort(port);
            free(itlFile->fData);
            free(itlFile);
            return SYNC_CONNECTION_FAIL;
        }
        itlFile->EncryptionStatus = 1;
        itlFile->Key.FixedKey = key;
	}
    pthread_t thread;
    pthread_create(&thread,NULL,(void *)DownloadITLTarget,(void*)itlFile);
	//_beginthread(DownloadITLTarget,0,NULL);

	return itlFile->NumberOfBlocks;


}

/*
Name: DownloadFileToTarget
Inputs:
    char *file: The full path of the file to download
    char * port: The name of the port to use (eg /dev/ttyUSB0 for usb serial, /dev/ttyS0 for com port 1)
    unsigned char sspAddress: The ssp address to download to
Return:
    If the value is less than 0x100000 it is the number of blocks to be downloaded.
    On an error, the value will be greater than 0x100000, and one of the following
    Failure:
    OPEN_FILE_ERROR					0x100001
    READ_FILE_ERROR					0x100002
    NOT_ITL_FILE					0x100003
    PORT_OPEN_FAIL					0x100004
    SYNC_CONNECTION_FAIL			0x100005
    SECURITY_PROTECTED_FILE			0x100006
    DATA_TRANSFER_FAIL				0x100010
    PROG_COMMAND_FAIL				0x100011
    HEADER_FAIL						0x100012
    PROG_STATUS_FAIL				0x100013
    PROG_RESET_FAIL					0x100014
    DOWNLOAD_NOT_ALLOWED			0x100015
    HI_TRANSFER_SPEED_FAIL			0x100016
Notes:
    The download is done in a seperate thread - see GetDownloadStatus() for information about its progress.
    Only one download operation may be in progress at once.
*/
int DownloadFileToTarget(const char * file, const char * port, const unsigned char sspAddress,const unsigned long long key)
{
	FILE * f;
	unsigned long data_length = 0;
	unsigned char * data;
	unsigned long i;
	f = fopen(file,"rb");

	if (f == 0)
	    return OPEN_FILE_ERROR;

    //get length of file
	fseek(f, 0 , SEEK_END);
	data_length = ftell(f);
	rewind(f);
    data = malloc(data_length);
    i = fread(data,1,data_length,f);
    fclose(f);
    i = DownloadDataToTarget(data,data_length,port,sspAddress,key);
    free(data);
    return i;
}

unsigned short _read_single_byte_reply(ITL_FILE_DOWNLOAD * itlFile, const unsigned long timeout)
{
    unsigned char buffer;
    clock_t start = GetClockMs();

    while(BytesInBuffer(itlFile->port) == 0)
    {
        usleep(1000);
        if (GetClockMs()-start > timeout)
            return -1;
    }
    ReadData(itlFile->port,&buffer,1);
    return buffer;
}

unsigned char _send_download_command(const unsigned char * data, const unsigned long length, const unsigned char expected_response, ITL_FILE_DOWNLOAD * itlFile)
{
    unsigned char buffer;
    while(BytesInBuffer(itlFile->port) > 0)
    {
        ReadData(itlFile->port,&buffer,1);
    }
    WriteData(data,length,itlFile->port);

    buffer = _read_single_byte_reply(itlFile,500);

    if (buffer == expected_response)
        return 1;
    return 0;
}

#define RAM_DWNL_BLOCK_SIZE				128
unsigned long _download_ram_file(ITL_FILE_DOWNLOAD * itlFile, SSP_COMMAND * sspC)
{
    unsigned long i;
    unsigned long baud;
    unsigned char buffer;
    int numRamBlocks;
    //initiate communication
	sspC->CommandDataLength = 2;
	sspC->CommandData[0] = SSP_CMD_PROGRAM;
	sspC->CommandData[1] = SSP_PROGRAM_RAM;

	if (SSPSendCommand(itlFile->port,sspC) == 0)
        return PROG_COMMAND_FAIL;
    if (sspC->ResponseData[0] != SSP_RESPONSE_OK)
        return PROG_COMMAND_FAIL;

    //calculate block size
    itlFile->dwnlBlockSize = ((unsigned short)sspC->ResponseData[1]) + (((unsigned short)sspC->ResponseData[2])<<8);

    sspC->EncryptionStatus = 0;
    sspC->CommandDataLength = 128;
    for (i = 0; i < 128; ++i)
        sspC->CommandData[i] = itlFile->fData[i];

    SSPSendCommand(itlFile->port,sspC);
    if (sspC->ResponseData[ 0] == SSP_RESPONSE_HEADER_FAILURE)
        return HEADER_FAIL;
    else if (sspC->ResponseData[0] != SSP_RESPONSE_OK)
        return DATA_TRANSFER_FAIL;

    baud = 38400;
	if((itlFile->fData[5] != 0x9) && (itlFile->fData[5] != 0xA)){ //NV9/10
		baud = 0;
		for(i = 0; i < 4; i++){
			baud += (long)itlFile->fData[68 + i] << ((3- i)  * 8);
		}
		if(baud == 0) baud = 38400;
	}
	SetBaud(itlFile->port,baud);
    itlFile->baud = baud;

    usleep(500000);

    numRamBlocks = itlFile->NumberOfRamBytes/RAM_DWNL_BLOCK_SIZE;

    for (i = 0; i < numRamBlocks; i++){
		WriteData(&itlFile->fData[128+(i*RAM_DWNL_BLOCK_SIZE)],RAM_DWNL_BLOCK_SIZE,itlFile->port);
		while (TransmitComplete(itlFile->port) == 0)
                    usleep(1000);

		//ramStatus.currentRamBlocks = i;
	}

    if ((itlFile->NumberOfRamBytes % RAM_DWNL_BLOCK_SIZE) != 0)
    {
        WriteData(&itlFile->fData[128+(i*RAM_DWNL_BLOCK_SIZE)],itlFile->NumberOfRamBytes % RAM_DWNL_BLOCK_SIZE,itlFile->port);
    }
    buffer = _read_single_byte_reply(itlFile,500);
    //check checksum
    if (itlFile->fData[0x10] != buffer)
        return DATA_TRANSFER_FAIL;

	return DOWNLOAD_COMPLETE;
}
#define ram_OK_ACK  0x32
unsigned long _download_main_file(ITL_FILE_DOWNLOAD * itlFile)
{
    unsigned char chk;
    unsigned long cur_block;
    unsigned long i;
    unsigned long block_offset;
    CloseSSPPort(itlFile->port);
    sleep(2);
    OpenSSPPort(itlFile->portname);
    SetBaud(itlFile->port,itlFile->baud);
    //ensure buffer clear after restart
    if (_send_download_command(&itlFile->fData[6],1,ram_OK_ACK,itlFile) == 0)
        return DATA_TRANSFER_FAIL;

    if (_send_download_command(itlFile->fData,128,ram_OK_ACK,itlFile) == 0)
        return DATA_TRANSFER_FAIL;

    for (cur_block = 1; cur_block <= itlFile->NumberOfBlocks; ++cur_block)
    {
        block_offset = 128 + ((cur_block-1)*itlFile->dwnlBlockSize) + itlFile->NumberOfRamBytes;
        chk = 0;
        for(i = 0; i < itlFile->dwnlBlockSize; ++i)
            chk ^= itlFile->fData[block_offset + i];
        /*
        for(i = 0; i < itlFile->dwnlBlockSize/128; ++i)
        {
            WriteData(&itlFile->fData[block_offset + (i*128)],128,itlFile->port);
            while (TransmitComplete(itlFile->port) == 0)
                    //usleep(1000);
                    sleep(0);

        }*/
        WriteData(&itlFile->fData[block_offset ],itlFile->dwnlBlockSize,itlFile->port);
        while (TransmitComplete(itlFile->port) == 0)
            usleep(1000);
        if (_send_download_command(&chk,1,chk,itlFile) ==0)
            return DATA_TRANSFER_FAIL;

        download_block = cur_block;
    }
    return DOWNLOAD_COMPLETE;

}

void  DownloadITLTarget(void * itl_file_pointer)
{
    ITL_FILE_DOWNLOAD * itlFile = 0;
	unsigned int i;
	unsigned long return_value;
	SSP_COMMAND sspC;
    itlFile = (ITL_FILE_DOWNLOAD*)itl_file_pointer;

    download_in_progress = 1;

	//ramStatus.ramState = rmd_ESTABLISH_COMS;
    sspC.Timeout = 1000;
	sspC.BaudRate = 9600;
	sspC.RetryLevel = 2;
	sspC.SSPAddress = itlFile->SSPAddress;
	sspC.EncryptionStatus = 0;

    if (itlFile->EncryptionStatus)
    {
        sspC.EncryptionStatus = 1;
        sspC.Key = itlFile->Key;
    }

    //get the number of ram bytes to download
	itlFile->NumberOfRamBytes = 0;
	for(i = 0; i < 4; i++)
		itlFile->NumberOfRamBytes += (unsigned long)itlFile->fData[7 + i] << (8 * (3-i));

    return_value = _download_ram_file(itlFile,&sspC);
    if (return_value == DOWNLOAD_COMPLETE)
    {
        return_value = _download_main_file(itlFile);
    }
    CloseSSPPort(itlFile->port);
    free(itlFile->fData);
    free(itlFile);
    download_in_progress = 0;
    download_block = return_value;
    pthread_exit(NULL);
}

unsigned long GetDownloadStatus()
{
    return download_block;
}
