# 
# EMU1802 V1.R1.M0
#
# This file is part of the EMU1802 distribution (https://github.com/SYSPROG-JLS/emu1802).
# Copyright (c) 2025 James Salvino.
# 
# This program is free software: you can redistribute it and/or modify  
# it under the terms of the GNU General Public License as published by  
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
import time

class Reg():
    def __init__(self):
        self.zero()
    def zero(self):
        self.msb = '00'
        self.lsb = '00'
        self.value = 0
    def fmt_bytes(self, v):
        x = hex(v)[2:].zfill(4).upper()
        self.msb = x[0:2]
        self.lsb = x[2:]
    def incr(self):
        self.value += 1
        if self.value > 65535:
            self.zero()
        else:
            self.fmt_bytes(self.value)
    def decr(self):
        self.value -= 1
        if self.value < 0:
            self.zero()
        else:    
           self.fmt_bytes(self.value)
    def glo(self):
        return self.lsb
    def ghi(self):
        return self.msb
    def plo(self, d):
        self.lsb = d
        self.value = int(self.msb + self.lsb, 16)
    def phi(self, d):
        self.msb = d
        self.value = int(self.msb + self.lsb, 16)

# Define the registers
R = [Reg() for _ in range(0, 16)]

I = 0
N = 0
P = 0
X = 0

T = '00'

D = '00'

DF = 0
IE = 0
Q = 0

EF1 = 0
EF2 = 0
EF3 = 0
EF4 = 0

Short_Branch = ["1 == 1",            # BR  
                "Q == 1",            # BQ
                "D == '00'",         # BZ
                "DF == 1",           # BDF (aka BPZ, BGE)
                "EF1 == 1",          # B1
                "EF2 == 1",          # B2
                "EF3 == 1",          # B3
                "EF4 == 1",          # B4
                "0 == 1",            # SKP (aka NBR)
                "Q == 0",            # BNQ
                "D != '00'",         # BNZ
                "DF == 0",           # BNF (aka BM, BL)
                "EF1 == 0",          # BN1
                "EF2 == 0",          # BN2
                "EF3 == 0",          # BN3
                "EF4 == 0",          # BN4
]

Long_Br_Skp = ["1 == 1",            # LBR  
               "Q == 1",            # LBQ
               "D == '00'",         # LBZ
               "DF == 1",           # LBDF
               "1 == 1",            # NOP
               "Q == 0",            # LSNO
               "D != '00'",         # LSNZ
               "DF == 0",           # LSNF 
               "1 == 1",            # LSKP (aka NLBR)
               "Q == 0",            # LBNQ
               "D != '00'",         # LBNZ
               "DF == 0",           # LBNF
               "IE == 1",           # LSIE 
               "Q == 1",            # LSQ
               "D == '00'",         # LSZ
               "DF == 1",           # LSDF
]

or_and_xor_add = [' ', '|', '&', '^', '+']

debug = True  # Set to True for register & memory dump between instructions

delay = 500   # Sleep time between instructions in milliseconds

# Define 256 Bytes of RAM
#RAM = ['7A', 'F8', '10', 'B1', '21', '91', '3A', '04', 
#       '31', '00', '7B', '30', '01' ]
#RAM = ['7B', 'F8', '03', 'A1', '21', '81', '3A', '04', '7A', '00']
#RAM = ['E2', 'F8', '00', 'B2', 'F8', '20', 'A2', 'F8', '00', '52',
#       '64', '22', 'F0', 'FC', '01', '52', 'FD', '10', '3A', '0A', '00',
#       '30', '07', '00', '00', '00', '00', '00', '00', '00', '00', '00', '00']
RAM = ['E2', 'F8', '00', 'B2', 'F8', '20', 'A2', 
       '6C', 'A3', '6C', '83', 'F5', '52',
       '64', '22', '00', '00', '00', '00', '00', '00', '00', '00', '00', '00',
       '00', '00', '00', '00', '00', '00', '00', '00']


def subtract(x, y):
    # Subtraction is 2's complement: each bit of the subtrahend is complemented and the 
    # resultant byte added to the minuend plus 1. 
    # The final carry of this operation is stored in DF:
    # DF=O indicates a borrow DF=1 indicates no borrow

    # Example1: 42-0E=42+F1+1=134
    # D register contains 34, DF contains 1. (No borrow)

    # Example2: 42-42=42+BD+1=100
    # D register contains 00, DF contains 1. (No borrow)

    # Example3: 42-77=42+88+1=CB
    # D register contains CB, DF contains O. (Borrow)

    minuend = int(x, 16)

    z = bin(int(y, 16))[2:].zfill(8)
    subtrahend = ''.join(['1' if d == '0' else '0' for d in z])
    
    r = hex(minuend + int(subtrahend, 2) + 1)[2:].zfill(2).upper()

    if len(r) == 3:
        return (r[1:], int(r[0]))
    else:
        return (r, 0)


def subtract_with_borrow(x, y, df):
    # MINUEND - SUBTRAHEND - (NOT DF) --> DF, 0

    # CONDITION I: DF = 0, i.e. Borrow = 1
    # Borrow is present from a preceding carry
    # 
    # Case 1 M(R(X)) > D
    # Example:
    # M(R(X) = 40
    #      D = 20
    # 40 - 20 - 1 = 40 +DF + 0 = llF 
    # After addition:
    #    D register contains 1F
    #    DF contains I (Borrow = 0)
    # 
    # Case 2 M(R(X)) < D 
    #  Example:
    # M(R(X)) = 4A 
    #       D = Cl
    # 4A - C1 - 1 = 4A + 3E + 0 = 88 
    # After addition:
    #    D register contains 88
    #    DF contains 0 (Borrow = 1)
    # 
    # 
    # CONDITION II: DF = 1, i.e. Borrow = 0
    # No borrow is present from a preceding carry
    # 
    # Case 3 M(R(X)) > D 
    #  Example:
    # M(R(X)) = 64 
    #       D = 32
    # 64 - 32 - 0 = 64 + CD + 1 = 132 
    # After addition:
    #    D register contains 32
    #    DF contains 1 (Borrow = 0)
    # 
    # Case 4 M(R(X)) < D 
    # Example:
    # M(R(X)) = 71 
    #       D = F2
    # 71 - F2 - 0 = 71 + OD + 1 = 7F 
    # After addition:
    #    D register contains 7F
    #    DF contains 0 (Borrow = 1)

    minuend = int(x, 16)

    z = bin(int(y, 16))[2:].zfill(8)
    subtrahend = ''.join(['1' if d == '0' else '0' for d in z])
    
    r = hex(minuend + int(subtrahend, 2) + df)[2:].zfill(2).upper()

    if len(r) == 3:
        return (r[1:], int(r[0]))
    else:
        return (r, 0)


while True:
    if debug:
        print("addr: ", hex(R[P].value), "inst: " + RAM[R[P].value])

    I = eval('0x' + RAM[R[P].value][0])
    N = eval('0x' + RAM[R[P].value][1])
    if I == 0x0:   # IDL / LDN
        if N == 0:   # IDL
            print('Idle Instruction Encountered')
            print('Exiting')
            break
        else:
            D = RAM[R[N].value]   # LDN
            R[P].incr()


    if I == 0x1:   # INC
        R[N].incr()
        R[P].incr()


    if I == 0x2:   # DEC
        R[N].decr()
        R[P].incr()


    if I == 0x3:   # BRANCH Instructions
        c = eval(Short_Branch[N])
        if c:
            R[P].incr()
            R[P].plo(RAM[R[P].value])
        else:
            R[P].incr()
            R[P].incr()            
          

    if I == 0x4:   # LDA
        D = RAM[R[N].value]
        R[N].incr()
        R[P].incr()


    if I == 0x5:   # STR
        RAM[R[N].value] = D
        R[P].incr()


    if I == 0x6:   # IRX / OUT / INP
        if N == 0x0:   # IRX
            R[X].incr()
            R[P].incr()
        elif N in [0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7]:   # OUT
            if N == 0x4:
                print("OUT 64 > ", RAM[R[X].value])
            else:
                print("OUT N = ", N, " not currently supported")
            R[X].incr()
            R[P].incr()
        elif N in [0x9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF]:   # INP
            if N == 0xC:
                D = input("Enter data byte for INP 6C > ")
                RAM[R[X].value] = D
            else:
                print("INP N = ", N, " not currently supported")
            R[P].incr()


    if I == 0x7:
        if N == 0x0 or N == 0x1:   # RET, DIS
            m = RAM[R[X].value]
            X = int(m[0], 16)
            P = int(m[1], 16)
            R[X].incr()
            IE = 0 if N == 0x1 else 1   # DIS
        if N == 0x2:       # LDXA
            D = RAM[R[X].value]
            R[X].incr()
            R[P].incr()
        if N == 0x3:       # STXD
            RAM[R[X].value] = D
            R[X].decr()
            R[P].incr()
        if N == 0x4 or N == 0xC:         # ADC / ADCI
            if N == 0x4:                 # ADC
                z = int(RAM[R[X].value], 16) + int(D, 16) + DF
            else:
                R[P].incr()                # ADCI
                z = int(RAM[R[P].value], 16) + int(D, 16) + DF
            if z > 255:
                DF = 1
                D = hex(z)[3:].zfill(2).upper()
            else:
                DF = 0
                D = hex(z)[2:].zfill(2).upper()
            R[P].incr()
        if N in [0x5, 0x7, 0xD, 0xF]:         # SDB / SMB / SDBI / SMBI
            if N == 0x5 or N == 0x7:
                m = RAM[R[X].value] 
            else:
                R[P].incr()
                m = RAM[R[P].value]
            if N == 0x5 or N == 0xD:    # SDB / SDBI
                D, DF = subtract_with_borrow(m, D, DF)
            else:                       # SMB / SMBI
                D, DF = subtract_with_borrow(D, m, DF)
            R[P].incr()
        if N == 0x6:         # SHRC 
            t = bin(int(D, 16))[2:].zfill(8)   
            D = hex(int(str(DF) + t[0:7], 2))[2:].upper()
            DF = int(t[-1])
            R[P].incr()
        if N == 0x8:         # SAVE
            RAM[R[X].value] = T
            R[P].incr()
        if N == 0x9:         # MARK
            T = hex(X)[2:].upper() + hex(P)[2:].upper()
            RAM[R[2].value] = T
            X = P
            R[2].decr()
            R[P].incr()
        if N == 0xA:        # REQ
            Q = 0
            R[P].incr()
        if N == 0xB:        # SEQ
            Q = 1
            R[P].incr()
        if N == 0xE:        # SHLC (aka RSHL)
            t = bin(int(D, 16))[2:].zfill(8)   
            D = hex(int(t[1:8] + str(DF), 2))[2:].upper()
            DF = int(t[0])
            R[P].incr()


    if I == 0x8:    # GLO
        D = R[N].glo()
        R[P].incr()


    if I == 0x9:    # GHI
        D = R[N].ghi()
        R[P].incr()


    if I == 0xA:    # PLO
        R[N].plo(D)
        R[P].incr()


    if I == 0xB:    # PHI
        R[N].phi(D)
        R[P].incr()


    if I == 0xC:
        c = eval(Long_Br_Skp[N])
        if N == 0x4:                         # NOP
            R[P].incr()
        elif N in [0x0, 0x1, 0x2, 0x3, 0x9, 0xA, 0xB]: # LBR, LBQ, LBZ, LBDF, LBNQ, LBNZ, LBNF
            if c:
                R[P].incr()
                R[P].phi(RAM[R[P].value])
                R[P].incr()
                R[P].plo(RAM[R[P].value])     
            else:
                R[P].incr()
                R[P].incr()
                R[P].incr()    
        elif N in [0x5, 0x6, 0x7, 0x8, 0xC, 0xD, 0xE, 0xF]: # LSNQ, LSNZ, LSNF, LSKP, LSIE,
            if c:                               # LSQ, LSZ, LSDF
                R[P].incr()
                R[P].incr()
                R[P].incr()
            else:
                R[P].incr()


    if I == 0xD:    # SEP
        P = N


    if I == 0xE:    # SEX
        X = N
        R[P].incr()


    if I == 0xF:
        if N == 0x0:   # LDX
            D = RAM[R[X].value]
            R[P].incr()
        if N in [0x1, 0x2, 0x3, 0x4, 0x9, 0xA, 0xB, 0xC]:   # OR   AND   XOR   ADD   ORI   ANI   XRI   ADI
            if N < 0x9:
                t = eval('int(RAM[R[X].value], 16) ' + or_and_xor_add[N] + ' int(D, 16)')
            else:
                R[P].incr()
                t = eval('int(RAM[R[P].value], 16) ' + or_and_xor_add[N-8] + ' int(D, 16)')
            D = hex(t)[2:].zfill(2).upper()
            if N == 0x4 or N == 0x0C:
                if t > 255:
                    DF = 1
                    D = hex(t)[3:].zfill(2).upper()
                else:
                    DF = 0
                    D = hex(t)[2:].zfill(2).upper()
            R[P].incr() 
        if N in [0x5, 0x7, 0xD, 0xF]:         # SD / SM / SDI / SMI
            if N == 0x5 or N == 0x7:
                m = RAM[R[X].value] 
            else:
                R[P].incr()
                m = RAM[R[P].value]
            if N == 0x5 or N == 0xD:    # SD / SDI
                D, DF = subtract(m, D)
            else:                       # SM / SMI
                D, DF = subtract(D, m)
            R[P].incr()
        if N == 0x6:         # SHR
            t = bin(int(D, 16))[2:].zfill(8)   
            D = hex(int('0' + t[0:7], 2))[2:].upper()
            R[P].incr()
        if N == 0x8:   # LDI
            R[P].incr()
            D = RAM[R[P].value]
            R[P].incr()
        if N == 0xE:         # SHL
            t = bin(int(D, 16))[2:].zfill(8)   
            D = hex(int(t[1:8 + '0'], 2))[2:].upper()
            R[P].incr()

    if debug:
        print("I:", hex(I), " N:", hex(N), " D:", D, " DF:", hex(DF),  " P:", hex(P), " X:", hex(X), " T:", T, " IE:", hex(IE), " Q:", Q)   
        print("R0:", R[0].value, " R1:", R[1].value, " R2:", R[2].value, " R3:", R[3].value, " R4:", R[4].value, " R5:", R[5].value, " R6:", R[6].value, " R7:", R[7].value)
        print("R8:", R[8].value, " R9:", R[9].value, " RA:", R[10].value, " RB:", R[11].value, " RC:", R[12].value, " RD:", R[13].value, " RE:", R[14].value, " RF:", R[15].value)
        try:
            print("M(R(X)):", RAM[R[X].value])
        except:
            pass
        finally:
            print("\n")

    time.sleep(delay/1000)
