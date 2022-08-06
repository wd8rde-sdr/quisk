#!/usr/bin/env python

# Si570Utils class gives python access to the Si570 Digital
# Sythesizer via a USB connection.
# Copyright (C) 2014 Martin Ewing
# Massive modifications by Bob Bouterse WD8RDE, I only need it to calculate register values.
# Robert Bouterse - Jan 30,2022 modified division operators for python 3.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact the author by e-mail: aa6e@arrl.net

# This is "middleware" that defines an API for general user programming
# of radio systems using the Si570 Programmable VCXO as an inexpensive
# digital VFO.  These routines connect via USB to an ATtiny45 USB-to-I2C
# device, which is running the usbavrsi570 code from PE0FKO.

# Tested on SoftRock RxTx Ensemble that uses the ATtiny85 MPU chip and a
# SiLabs 570 ("CAC000141G / D1HOS144") chip
# [3.3v CMOS, 61 ppm stab., 10-160 MHz]

# partially based on a subset of operations.c from Andrew Nilsson VK6JBL
# Also, see http://www.silabs.com/Support%20Documents/TechnicalDocs/si570.pdf
# and https://code.google.com/p/usbavrsi570/

# require libusb-1.0 wrapper from https://pypi.python.org/pypi/libusb1/1.2.0

import math, sys
from .sidefs import *

# Note changes from operation.c:
#       1. method names have changed to make them more regular.
#       2. get/set freq always work with floating MHz of signal frequency =
#           osc frequency / multiplier.

class Si570Utils(object):
    def __init__(self, verbose=0, fXtal=SI570_NOMINAL_XTALL_FREQ, xtal_offset=0, multiplier=4):
        self.verbose = verbose
        self.fXtal = fXtal
        self.xtal_offset = float(xtal_offset)
        self.multiplier = multiplier
       
    def __calcDividers(self, f): # Returns solution = [HS_DIV, N1, f0, RFREQ]
        # Instead of solution structure, use simple list for each variable.
        cHS_DIV = list()
        cN1 = list()
        cf0 = list()
        cRFREQ = list()
        for i in range(7,-1,-1):    # Count down through the dividers
            if HS_DIV_MAP[i] > 0:
                cHS_DIV.append(i)
                y = (SI570_DCO_HIGH + SI570_DCO_LOW) // (2 * f)
                y = y // HS_DIV_MAP[i]
                if y < 1.5:
                    y = 1.0
                else:
                    y = 2 * round(y/2.0)
                if y > 128:
                    y = 128
                cN1.append( math.trunc(y) - 1 )
                cf0.append( f * y * HS_DIV_MAP[i] )
            else:
                cHS_DIV.append(None)    # dummy result
                cN1.append(None)        # another dummy
                cf0.append( 1.0E16 )
        imin = -1
        fmin = 1.0E16
        for i in range(8):
            if (cf0[i] >= SI570_DCO_LOW) & (cf0[i] <= SI570_DCO_HIGH) :
                if cf0[i] < fmin:
                    fmin = cf0[i]
                    imin = i
        if imin >= 0:
            solution = [ cHS_DIV[imin], cN1[imin], cf0[imin], cf0[imin]/(self.fXtal + self.xtal_offset) ]
            if (self.verbose >= 2):
                print("Solution:")
                print("  HS_DIV = %d" % solution[0])
                print("  N1 = %d" % solution[1])
                print("  f0 = %f" % solution[2])
                print("  RFREQ = %f" % solution[3])
        else:
            solution = None     # This is the error return
        return solution

    def __setLongWord(self, v ):           # v = int value; return bytearray(4)
        iv = int(v)                 # be sure of int type
        b = bytearray(4)
        b[0] = iv & 0xff
        b[1] = ((iv & 0xff00) >> 8) & 0xff
        b[2] = ((iv & 0xff0000) >> 16) & 0xff
        b[3] = ((iv & 0xff000000) >> 24) & 0xff
        return b                    # NB bytearray, not long word!

    def setFreq(self, frequency):
        f = self.multiplier * frequency
        if self.verbose:
            print("Setting Si570 Frequency by registers to: %f" % f)
        sHS_DIV, sN1, sf0, sRFREQ = self.__calcDividers(f)
        RFREQ_int = int(math.trunc(sRFREQ))
        RFREQ_frac= int( round((sRFREQ - RFREQ_int) * 268435456) ) # check int ok
        intbuf  = self.__setLongWord( RFREQ_int )
        fracbuf = self.__setLongWord( RFREQ_frac)
        outbuf = bytearray(6)
        outbuf[5] = fracbuf[0]
        outbuf[4] = fracbuf[1]
        outbuf[3] = fracbuf[2]
        outbuf[2] = fracbuf[3]      | ((intbuf[0] & 0xf) << 4)
        outbuf[1] = RFREQ_int // 16  + ((sN1 & 0x3) << 6)
        outbuf[0] = sN1//4           + (sHS_DIV << 5)

        if self.verbose:
            print("Set Freq Buffer",)
            print("%x %x %x %x %x %x" % (outbuf[0], outbuf[1], outbuf[2], outbuf[3], outbuf[4], outbuf[5]))

        return outbuf
# End of Si570 class

if __name__ == "__main__":
    # debug code goes here
    si = Si570Utils(verbose=4)
    print("SET FREQ BY VALUE")
    si.setFreq(7.5)
    print("Done.")

