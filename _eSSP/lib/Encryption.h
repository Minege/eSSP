#ifndef _AES_H_
#define _AES_H_

#include <assert.h>
#include "../inc/itl_types.h"

//


/***************************************************************************
 * 2. DEFINES                                                              *
 ***************************************************************************/

#define CRC_SSP_SEED		0xFFFF
#define CRC_SSP_POLY		0x8005


// ECB Mode
#define C_AES_MODE_ECB 1

// CBC Mode
#define C_AES_MODE_CBC 2

// maximum key length (in bytes)
#define C_MAX_KEY_LENGTH 16

// number of rounds
#define C_NUMBER_ROUNDS 10

// error types
#define E_AES_SUCCESS       0x0
#define E_AES_WRONG_MODE	0x1


#define SSP_STEX			0x7E


/***************************************************************************
 * 3. DECLARATIONS                                                         *
 ***************************************************************************/

typedef struct
{
    UINT32 enc_round_keys[(C_NUMBER_ROUNDS + 1) * C_MAX_KEY_LENGTH/4];   /* encryption round keys         */
    UINT8  IV[16];                                                       /* 128-bit initialization vector */
} aes_context;

/***************************************************************************
 * 4. CONSTANTS                                                            *
 ***************************************************************************/

/***************************************************************************
 * 5. FUNCTION PROTOTYPES                                                  *
 ***************************************************************************/

/* F-AES/100: aes_encrypt */
extern UINT8 aes_encrypt( const UINT8   aes_mode,              // the AES mode (ECB or CBC)
                          const UINT8  *aes_key,               // pointer to key
                          const UINT32  aes_key_length,        // key length in bytes (library only supports keys of length 16 bytes)
                          const UINT8  *IV,                    // pointer to IV
                          const UINT32  IV_length,             // IV length in bytes (library only supports IV of length 16 bytes)
                                UINT8  *plain_data,            // pointer to data to encrypt
                                UINT8  *cipher_data,           // pointer to encrypted data (might be same as plain_data)
                          const UINT32  data_length );         // length of data to encrypt in bytes (must be a multiple of 16)

/* F-AES/120: aes_decrypt */
extern UINT8 aes_decrypt( const UINT8   aes_mode,              // the AES mode (ECB or CBC)
                          const UINT8  *aes_key,               // pointer to key
                          const UINT32  aes_key_length,        // key length in bytes (library only supports keys of length 16 bytes)
                          const UINT8  *IV,                    // pointer to IV
                          const UINT32  IV_length,             // IV length in bytes (library only supports IV of length 16 bytes)
                                UINT8  *plain_data,            // pointer to decrypted data
                                UINT8  *cipher_data,           // pointer to encrypted data to decrypt (might be same as plain_data)
                          const UINT32  data_length );         // length of data to decrypt in bytes (must be a multiple of 16)


unsigned short cal_crc_loop_CCITT_A( short l, unsigned char* p, unsigned short seed,unsigned short cd );
/***************************************************************************
 * 6. MACRO FUNCTIONS                                                      *
 ***************************************************************************/

/***************************************************************************
 * 7. END                                                                  *
 ***************************************************************************/





#endif // aes.h

