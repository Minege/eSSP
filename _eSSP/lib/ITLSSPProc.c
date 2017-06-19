
#include "ITLSSPProc.h"
#include <stdlib.h>
#include "Random.h"
#include "Encryption.h"
#include "../inc/ssp_defines.h"
#include <unistd.h>
#include <stdio.h>

#include <pthread.h>
extern unsigned char download_in_progress;


#define VER_MAJ  1  // not > 255
#define VER_MIN	 1	// not > 255
#define VER_REV	 0	// not > 255


unsigned int encPktCount[MAX_SSP_PORT];
unsigned char sspSeq[MAX_SSP_PORT];
/*
extern int PortStatus,PortStatus2,PortStatusUSB,PortStatusCCT;
extern HANDLE hDevice,hDevice2,hDeviceUSB,hDeviceCCT;
*/
/*		Linear Feedback Shift Registers			*/
#define LFSR(n)    {if (n&1) n=((n^0x80000055)>>1)|0x80000000; else n>>=1;}
/*		Rotate32								*/
#define ROT(x, y)  (x=(x<<y)|(x>>(32-y)))


typedef enum{
	KEY_GENERATOR,
	KEY_MODULUS,
	KEY_HOST_INTER,
	KEY_HOST_RANDOM,
	KEY_SLAVE_INTER,
	KEY_SLAVE_RANDOM,
	KEY_HOST,
	KEY_SLAVE,
}SSP_KEY_INDEX;


int GetProcDLLVersion(unsigned char* ver)
{
	ver[0] = VER_MAJ;
	ver[1] = VER_MIN;
	ver[2] = VER_REV;

	return 1;

}


/*    DLL function call to generate host intermediate numbers to send to slave  */
int InitiateSSPHostKeys(SSP_KEYS *  keyArray, const unsigned char ssp_address)
{


	long long swap = 0;

	/* create the two random prime numbers  */
	keyArray->Generator = GeneratePrime();
	keyArray->Modulus = GeneratePrime();
	/* make sure Generator is larger than Modulus   */
	if (keyArray->Generator > keyArray->Modulus)
	{
		swap = keyArray->Generator;
		keyArray->Generator = keyArray->Modulus;
		keyArray->Generator = swap;
	}


	if(CreateHostInterKey(keyArray)== -1)
		return 0;


	/* reset the apcket counter here for a successful key neg  */
	encPktCount[ssp_address] = 0;

	return 1;
}





/* creates the host encryption key   */
int CreateSSPHostEncryptionKey(SSP_KEYS* keyArray)
{
	keyArray->KeyHost = XpowYmodN(keyArray->SlaveInterKey,keyArray->HostRandom,keyArray->Modulus);

	return 1;
}


 int EncryptSSPPacket(unsigned char ptNum,unsigned char* dataIn, unsigned char* dataOut, unsigned char* lengthIn,unsigned char* lengthOut, unsigned long long* key)
{
	#define FIXED_PACKET_LENGTH   7
	unsigned char pkLength,i,packLength = 0;
	unsigned short crc;
	unsigned char tmpData[255];


	pkLength = *lengthIn + FIXED_PACKET_LENGTH;

	/* find the length of packing data required */
	if(pkLength % C_MAX_KEY_LENGTH != 0){
		packLength = C_MAX_KEY_LENGTH - (pkLength % C_MAX_KEY_LENGTH);
	}
	pkLength += packLength;

	tmpData[0] = *lengthIn; /* the length of the data without packing */

	/* add in the encrypted packet count   */
	for(i = 0; i < 4; i++)
		tmpData[1 + i] = (unsigned char)((encPktCount[ptNum] >> (8*i) & 0xFF));


	for(i = 0; i < *lengthIn; i++)
		tmpData[i + 5] = dataIn[i];


	/* add random packing data  */
	for(i = 0; i < packLength; i++)
		tmpData[5 + *lengthIn + i] =  (unsigned char)(rand() % 255);
	/* add CRC to packet end   */

	crc = cal_crc_loop_CCITT_A(pkLength - 2,tmpData,CRC_SSP_SEED,CRC_SSP_POLY);

	tmpData[pkLength - 2] = (unsigned char)(crc & 0xFF);
	tmpData[pkLength - 1] = (unsigned char)((crc >> 8) & 0xFF);

	if (aes_encrypt( C_AES_MODE_ECB,(unsigned char*)key,C_MAX_KEY_LENGTH,NULL,0,tmpData,&dataOut[1],pkLength) != E_AES_SUCCESS)
							return 0;

	pkLength++; /* increment as the final length will have an STEX command added   */
	*lengthOut = pkLength;
	dataOut[0] = SSP_STEX;

	encPktCount[ptNum]++;  /* incremnet the counter after a successful encrypted packet   */

	return 1;
}


 int  DecryptSSPPacket(unsigned char* dataIn, unsigned char* dataOut, unsigned char* lengthIn,unsigned char* lengthOut, unsigned long long* key)
{


	if (aes_decrypt( C_AES_MODE_ECB,(unsigned char*)key,C_MAX_KEY_LENGTH,NULL,0,dataOut,dataIn,*lengthIn) != E_AES_SUCCESS)
							return 0;



	return 1;
}





/* Creates a host intermediate key */
int CreateHostInterKey(SSP_KEYS * keyArray)
{

	if (keyArray->Generator ==0 || keyArray->Modulus ==0 )
		return -1;

	keyArray->HostRandom = (long long) (GenerateRandomNumber() % MAX_RANDOM_INTEGER);
	keyArray->HostInter = XpowYmodN(keyArray->Generator,keyArray->HostRandom,keyArray->Modulus );

	return 0;
}




void __attribute__ ((constructor)) my_init(void)
{
    int i;
    for(i = 0; i < MAX_SSP_PORT; i++){
		encPktCount[i] = 0;
		sspSeq[i] = 0x80;
	}
    srand((int)GetRTSC());
    download_in_progress = 0;
}
void __attribute__ ((destructor)) my_fini(void)
{
    if (download_in_progress)
    {
        printf("Waiting for download to complete...\n");
        while (download_in_progress)
            sleep(1);
    }
}

/*
Name: NegotiateSSPEncryption
Inputs:
    SSP_PORT The port handle (returned from OpenSSPPort) of the port to use
    char ssp_address: The ssp_address to negotiate on
    SSP_FULL_KEY * key: The ssp encryption key to be used
Return:
    1 on success
    0 on failure
Notes:
    Only the EncryptKey iin SSP_FULL_KEY will be set. The FixedKey needs to be set by the user
*/
int NegotiateSSPEncryption(SSP_PORT port, const char ssp_address, SSP_FULL_KEY * key)
{
    SSP_KEYS temp_keys;
    SSP_COMMAND sspc;
    unsigned char i;
    //setup the intial host keys
    if (InitiateSSPHostKeys(&temp_keys,ssp_address) == 0)
        return 0;
    sspc.EncryptionStatus = 0;
    sspc.RetryLevel = 2;
    sspc.Timeout = 1000;
    sspc.SSPAddress = ssp_address;

    //make sure we can talk to the unit
    sspc.CommandDataLength = 1;
    sspc.CommandData[0] = SSP_CMD_SYNC;
    SSPSendCommand(port,&sspc);
    if (sspc.ResponseData[0] != SSP_RESPONSE_OK)
        return 0;

    //setup the generator
    sspc.CommandDataLength = 9;
    sspc.CommandData[0] = SSP_CMD_SET_GENERATOR;
    for (i = 0; i < 8 ; ++i)
        sspc.CommandData[1+i] = (unsigned char)(temp_keys.Generator >> (i*8));
    //send the command
    SSPSendCommand(port,&sspc);
    if (sspc.ResponseData[0] != SSP_RESPONSE_OK)
        return 0;

    //setup the modulus
    sspc.CommandDataLength = 9;
    sspc.CommandData[0] = SSP_CMD_SET_MODULUS;
    for (i = 0; i < 8 ; ++i)
        sspc.CommandData[1+i] = (unsigned char)(temp_keys.Modulus >> (i*8));
    //send the command
    SSPSendCommand(port,&sspc);
    if (sspc.ResponseData[0] != SSP_RESPONSE_OK)
        return 0;

    //swap keys
    sspc.CommandDataLength = 9;
    sspc.CommandData[0] = SSP_CMD_REQ_KEY_EXCHANGE;
    for (i = 0; i < 8 ; ++i)
        sspc.CommandData[1+i] = (unsigned char)(temp_keys.HostInter >> (i*8));
    //send the command
    SSPSendCommand(port,&sspc);
    if (sspc.ResponseData[0] != SSP_RESPONSE_OK)
        return 0;

    //read the slave key
    temp_keys.SlaveInterKey = 0;
    for (i = 0; i < 8 ; ++i)
        temp_keys.SlaveInterKey +=  ((long long)(sspc.ResponseData[1+i])) << (8*i);


    if (CreateSSPHostEncryptionKey(&temp_keys) == 0)
        return 0;
    key->EncryptKey = temp_keys.KeyHost;
    return 1;
}

