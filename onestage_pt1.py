# filename: fetch_decode.py
import sys
import itertools
from pydigital.memory import readmemh
from pydigital.register import Register
from regfile import RegFile
from riscv_isa.control import controlFormatter
from riscv_isa import Instruction
from alu import alu
from mux import make_mux

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
        return "PC: xxxxxxxx, IR: xxxxxxxx\n"
    else:
        if instr.i_imm != None:
            rs2imm_str = f"rs2: xxxxxxxx [xx] i_imm: {instr.i_imm:04x}"
        elif instr.u_imm != None:
            rs2imm_str = f"rs2: xxxxxxxx [xx] i_imm: {instr.u_imm:04x}"
        else:
            rs2imm_str = f"rs2: {rs2_val} [{instr.rs2}] i_imm: xxxx"
        
        if rs1_val != None:
            rs1_str = f"rs1: {rs1_val} [{instr.rs1}] "
        else:
            rs1_str = f"rs1: xxxxxxxx [xx] "
        
        return f"PC: {pc_val:08x}, IR: {instr.val:08x}, {instr}" + \
            f"rd: {RF.read(instr.rd)} [{instr.rd}] " + rs1_str + rs2imm_str + \
            f" op: {instr.get_opcode():x} func3: {instr.funct3} func7: {instr.funct7}" + \
            f" alu_fun: {alufun_tup[0]}\n"

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
    rs1_val = RF.read(instr.rs1)

    # get the rs2 value if a rs2 address exists
    rs2_val = None
    if instr.rs2 != None:
        rs2_val = RF.read(instr.rs2)

    # define the op1 and op2 muxes
    op1_mux = make_mux(lambda: rs1_val, lambda: None, lambda: instr.u_imm)
    op2_mux = make_mux(lambda: rs2_val, lambda: instr.i_imm, lambda: None, lambda: pc_val)

    # get the alu fun val using decoder
    alufun_tup = controlFormatter(instr.get_instr(), "ALU_fun")
    # get the op1 and op2 sel
    op1_sel = controlFormatter(instr.get_instr(), "op1_sel")[1]
    op2_sel = controlFormatter(instr.get_instr(), "op2_sel")[1]

    alu_val = alu(op1_mux(op1_sel), op2_mux(op2_sel), alufun_tup[1])
 
    # get rf_wen
    rf_wen = controlFormatter(instr.get_instr(), "rf_wen")[1]
    # update register values
    RF.clock(instr.rd, alu_val, rf_wen)

    # print one line at the end of the clock cycle
    print(f"{t}:", display())

    # handle env calls
    # check a0 value env call type
    a0_val = RF.read(10)
    if instr.instr == 'ecall' and a0_val == 1:
        print(f"ECALL({a0_val}): {RF.read(11)}\n")
    elif instr.instr == 'ecall' and (a0_val == 0 or a0_val == 10):
        print(f"ECALL({a0_val}): " + 'EXIT\n' if a0_val == 10 else 'HALT\n')
        RF.display()
        break

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
