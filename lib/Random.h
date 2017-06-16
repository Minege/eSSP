
#ifndef _RANDOM_H
#define _RANDOM_H


#define MAX_RANDOM_INTEGER		2147483648LL //Should make these numbers massive to be more secure
#define MAX_PRIME_NUMBER		2147483648LL //Bigger the number the slower the algorithm

/*		Linear Feedback Shift Registers			*/
#define LFSR(n)    {if (n&1) n=((n^0x80000055)>>1)|0x80000000; else n>>=1;}
/*		Rotate32								*/
#define ROT(x, y)  (x=(x<<y)|(x>>(32-y)))


unsigned long long GeneratePrime(void);
unsigned char MillerRabin (long long n, long long trials);
unsigned char IsItPrime (long long n, long long a);
long long XpowYmodN(long long x, long long y, long long N);
unsigned long long GenerateRandomNumber(void);
long long GetRTSC( void );



#endif

