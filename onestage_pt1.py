# filename: fetch_decode.py
import sys
import itertools
from pydigital.memory import readmemh
from pydigital.register import Register
from regfile import RegFile
from riscv_isa.control import controlFormatter
from riscv_isa import Instruction
from alu import alu

# the PC register
PC = Register()
# the reg file
RF = RegFile()

# check if a path was provided
if len(sys.argv) != 2:
    exit("ERROR: input hex file not provided!")

# get the inputted hex path
hex_path = sys.argv[1]

# construct a memory segment for instruction memory
# load the contents from the 32-bit fetch_test hex file (big endian)
try:
    imem = readmemh(hex_path, word_size=4, byteorder='big')
except:
    exit("ERROR: incorrect hex file path!")

def display():
    if pc_val == None:
        return "PC: xxxxxxxx, IR: xxxxxxxx"
    else:
        rs2imm_str= ""
        if imm != None:
            rs2imm_str = f"rs2: xxxxxxxx [xx] i_imm: {imm:04x}"
        else:
            rs2imm_str = f"rs2: {rs2_val} [{rs2_addr}] i_imm: xxxx"
        return f"PC: {pc_val:08x}, IR: {instr.val:08x}, {instr}" + \
            f"rd: {RF.read(rd_addr)} [{rd_addr}] rs1: {rs1_val} [{rs1_addr}] " + rs2imm_str + \
            f" op: {instr.get_opcode():x} func3: {instr.funct3} func7: {instr.funct7}" + \
            f" alu_fun: {alufun_tup[0]}"

startup = True
# generate system clocks until we reach a stopping condition
# this is basically the run function from the last lab
for t in itertools.count():
    # sample inputs
    pc_val = PC.out()

    # RESET the PC register
    if startup:
        PC.reset(imem.begin_addr)
        startup = False
        print(f"{t}:", display())
        continue

    # access instruction memory
    instr = Instruction(imem[pc_val], pc_val)

    # get rd, rs1, and rs2 addresses and their values using regfile
    rs1_addr = instr.get_rs1()
    rs1_val = RF.read(rs1_addr)
    
    # get rs2 or imm depending on instr type
    rs2_tup = instr.get_rs2imm()
    imm = None; rs2_addr = None; rs2_val = None
    if rs2_tup[0]: # if imm
        imm = rs2_tup[1]
    else: # if rs2
        rs2_addr = rs2_tup[1]
        rs2_val = RF.read(rs2_addr)
    
    rd_addr = instr.get_rd()
    rd_val = RF.read(rd_addr)

    # get the alu fun val using decoder
    alufun_tup = controlFormatter(instr.get_instr(), "ALU_fun")

    print(alufun_tup[1])

    # perform alu functions on the operands
    if imm != None:
        alu_val = alu(rs1_val, imm, alufun_tup[1])
    else:
        alu_val = alu(rs1_val, rs2_val, alufun_tup[1])
    
    # update register values
    RF.clock(rd_addr, alu_val, True)

    # print one line at the end of the clock cycle
    print(f"{t}:", display())

    # clock logic blocks, PC is the only clocked module!
    # here the next pc value is always +4
    PC.clock(4 + pc_val)

    # check stopping conditions on NEXT instruction
    if PC.out() > 0x1100:
        print("STOP -- PC is large! Is something wrong?")
        break
    if imem[PC.out()] == 0:
        print("Done -- end of program.\n")
        # print register values at the end of program
        RF.display()
        break
