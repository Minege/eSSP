/***************************************************************************
 *                                                                         *
 * Copyright                                                               *
 *     escrypt GmbH, Bochum, Germany                                       *
 *     Lise-Meitner-Allee 4                                                *
 *     D-44801 Bochum, Germany                                             *
 *     http://www.escrypt.com                                              *
 *     info@escrypt.com                                                    *
 *                                                                         *
 * All Rights reserved                                                     *
 *                                                                         *
 ***************************************************************************/

/***************************************************************************/
/*! 
    \file        defs.h

    \brief       Common definitions

    \author      MW,
                 AW
    
    \version     2.7
    
    \date        August 31, 2005
    
    \par Reviews:
    \li          28.08.2005 Reviewed by AW
    \li          28.01.2004 Reviewd by AW
    \li          28.01.2004 Corrected by MW
    \li          25.08.2004 Splint 3.1.1 (no warnings)

*/
/***************************************************************************/

#ifndef _DEFS_H_
#define _DEFS_H_

/***************************************************************************
 * 2. DEFINES                                                              *
 ***************************************************************************/


  #define NDEBUG
  #define I_AES_ENCRYPT 0
  #define I_AES_DECRYPT 1
  #define I_AES_ECB_MODE 1 
  #define I_FIXED_S_BOX 0
  #define I_FIXED_INVERSE_S_BOX 0
  #define C_SKIP_PARAMETER_CHECK 1
  #define C_SKIP_PARAMETER_CHECK_API 0


#endif // defs.h

