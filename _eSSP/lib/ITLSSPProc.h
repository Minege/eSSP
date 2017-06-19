#define CCONV _stdcall
#define NOMANGLE

#include "../inc/SSPComs.h"
#include "../inc/itl_types.h"
#include <time.h>

typedef enum{
    LEVEL_CHECK_OFF = 254,
    LEVEL_CHECK_ON
}LEVEL_CHECK;


typedef enum{
  FLOAT_PAYOUT_TO_PAYOUT,
  FLOAT_PAYOUT_TO_CASHBOX,
}FLOAT_MODE;

typedef enum{
	LEVEL_NOT_SUFFICIENT = 1,
	NOT_EXACT_AMOUNT,
	HOPPER_BUSY,
	HOPPER_DISABLED,
	REQ_STATUS_OK = 255
}PAYOUT_REQ_STATUS;


typedef enum{
	DEAL_MODE_SPLIT = 0xFE,
	DEAL_MODE_FREE,
}DEAL_MODE;

typedef struct{
	UINT32 CoinValue;
	UINT32 CoinLevel;
}COINS;

#define MAX_COIN_CHANNEL		30

typedef struct{
	UINT8 NumberOfCoinValues;
	COINS CoinsToPay[MAX_COIN_CHANNEL];
	COINS CoinsInHopper[MAX_COIN_CHANNEL];
	UINT8 FloatMode[MAX_COIN_CHANNEL];
	UINT16 SplitQty[MAX_COIN_CHANNEL];
	UINT32 AmountPayOutRequest;
	UINT32 FloatAmountRequest;
	UINT16 MinPayout;
	UINT8 Mode;
	UINT8 DealMode;
	UINT8 LevelMode;
	UINT8 ExitMode;
	UINT16 MinPayoutRequest;
}PAY;

typedef struct{
	unsigned long NumberOfBlocks;
	unsigned long NumberOfRamBytes;
	unsigned char* fData;
	SSP_PORT port;
	unsigned long dwnlBlockSize;
	unsigned char SSPAddress;
	unsigned char EncryptionStatus;
	SSP_FULL_KEY Key;
    char  portname[255];
	unsigned long baud;
}ITL_FILE_DOWNLOAD;
void  DownloadITLTarget(void * itl_file_pointer);
int TestSplit(PAY* py,UINT32 valueToFind);

void __attribute__ ((constructor)) my_init(void);
void __attribute__ ((destructor)) my_fini(void);

//private
clock_t GetClockMs();
void SSPDataIn(unsigned char RxChar, SSP_TX_RX_PACKET* ss);
int EncryptSSPPacket(unsigned char ptNum,unsigned char* dataIn, unsigned char* dataOut, unsigned char* lengthIn,unsigned char* lengthOut, unsigned long long* key);
int DecryptSSPPacket(unsigned char* dataIn, unsigned char* dataOut, unsigned char* lengthIn,unsigned char* lengthOut, unsigned long long* key);
int InitiateSSPHostKeys(SSP_KEYS*  keyArray,const unsigned char ssp_address);
int CreateHostInterKey(SSP_KEYS* keyArray);
int CreateSSPHostEncryptionKey(SSP_KEYS* keyArray);
