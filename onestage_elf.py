# filename: onestage_elf.py
import sys
import itertools
from pydigital.memory import readmemh, Memory, MemorySegment
from pydigital.register import Register
from pydigital.elfloader import load_elf
from pydigital.utils import as_twos_comp
from riscv_isa.control import controlFormatter
from riscv_isa import Instruction
from riscv_isa.csrs import CsrMemory
from regfile import RegFile
from stats import Stats
from alu import alu
from mux import make_mux

# debug/silent flag
DEBUG = True
# test flag
TEST = False
# print stats flag
STATS = False
# max cycle num
MAX_CYCLES = 0

# the PC register
PC = Register()
# the reg file
RF = RegFile()
# init csr memory
CSR = CsrMemory()
# stats counter
COUNT = Stats()

# check if a path was provided
if len(sys.argv) < 2:
    exit("ERROR: input elf file not provided!")

# check for flags
for i, arg in enumerate(sys.argv):
    # if argument is a flag
    if arg.startswith('-'):
        if arg == '-s': # silent flag
            DEBUG = False
        elif arg == '-t':
            TEST = True
        elif arg == '-x':
            MAX_CYCLES = int(sys.argv[i+1]) * 1000
        elif arg == '-p':
            STATS = True

# get the inputted elf path
elf_path = sys.argv[1]

# construct a memory segment for instruction memory
# load the contents from the 32-bit fetch_test hex file (big endian)
try:
    imem, symbols = load_elf(elf_path, quiet=not(DEBUG))
except:
    exit("ERROR: couldn't read elf file!")

# initialize memory from the elf
MEM = Memory(imem)

def handle_test():
    "handles the output for test - checks whether test passed or not"
    # if test flag is set
    if TEST:
        a0_val = RF.read(10)
        if a0_val == 0:
            print(f"{sys.argv[1]} -- Test Passed!\n")
        else:
            print(f"{sys.argv[1]} -- Test Failed! ({a0_val})\n")

def handle_syscall(mem_em, mem_wr, word_size, alu_val):
    "handles UCB syscalls"
    # check if a syscall was made
    if mem_em == 1 and mem_wr == 1 and 'tohost' in symbols:
        if (word_size == 4 and as_twos_comp(alu_val) == symbols['tohost'] + 4) or \
           (word_size == 8 and as_twos_comp(alu_val) == symbols['tohost']):
            val = MEM.mem[symbols['tohost']]
            # handle exit call
            if val & 0b1 == 0b1:
                if DEBUG: 
                    print(f"SYSCALL: exit ({val>>1})\n")
                    RF.display()
                handle_test()
                if STATS:
                    COUNT.display()
                sys.exit(val>>1)
            # handle printf if not exit
            # get all the args for putchar
            which = MEM.mem[MEM.mem[symbols['tohost']]]
            arg0 = MEM.mem[MEM.mem[symbols['tohost']] + 8]
            arg1 = MEM.mem[MEM.mem[symbols['tohost']] + 16]
            arg2 = MEM.mem[MEM.mem[symbols['tohost']] + 24]
            # putchar implementation
            if which == 64:
                # print the chars
                if DEBUG: 
                    try:
                        print(f"SYSCALL: printf -- {MEM.mem[arg1:arg1 + arg2].decode('ASCII')}\n")
                    except:
                        print("SYSCALL: printf -- PRINT ERROR: unidentified character\n")
                else: 
                    try:
                        print(f"{MEM.mem[arg1:arg1 + arg2].decode('ASCII')}\n")
                    except:
                        print("PRINT ERROR: unidentified character\n")
            MEM.mem[symbols['fromhost']] = 1

def display():
    if pc_val == None:
        return "PC: xxxxxxxx, IR: xxxxxxxx\n"
    else:
        if instr.rd != None:
            rd_str = f"rd: {RF.read(instr.rd):x} [{instr.rd}] "
        else:
            rd_str = f"rd: xxxxxxxx [xx] "

        if rs1_val != None:
            rs1_str = f"rs1: {rs1_val:x} [{instr.rs1}] "
        else:
            rs1_str = f"rs1: xxxxxxxx [xx] "

        if rs2_val != None:
            rs2_str = f"rs2: {rs2_val:x} [{instr.rs2}] "
        else:
            rs2_str = f"rs2: xxxxxxxx [xx] "

        if instr.imm != None:
            imm_str = f"imm: {instr.imm:04x} "
        else:
            imm_str = f"imm: xxxx "
        
        return f"PC: {pc_val:08x}, IR: {instr.val:08x}, {instr}" + \
            rd_str + rs1_str + rs2_str + imm_str + \
            f" op: {instr.get_opcode():x} func3: {instr.funct3} func7: {instr.funct7}" + \
            f" alu_fun: {alufun_tup[0]}\n"

def branch_taken(op1, op2, br_fun):
    "check wether jump or branch AND if branch is taken or not by comparing op1 and op2"
    if br_fun == 0: # no jump
        return 0
    elif br_fun == 1: # jr
        return 1
    elif br_fun == 2: # bgeu
        return 2 if as_twos_comp(op1) >= as_twos_comp(op2) else 0
    elif br_fun == 5: # bge
        return 2 if op1 >= op2 else 0
    elif br_fun == 3: # blt
        return 2 if op1 < op2 else 0
    elif br_fun == 7: # bltu
        return 2 if as_twos_comp(op1) < as_twos_comp(op2) else 0
    elif br_fun == 4: # bne
        return 2 if op1 != op2 else 0
    elif br_fun == 6: # jump
        return 3
    elif br_fun == 8: # beq
        return 2 if op1 == op2 else 0

startup = True
# generate system clocks until we reach a stopping condition
# this is basically the run function from the last lab
for t in itertools.count():
    # sample inputs
    pc_val = PC.out()

    # RESET the PC register
    if startup:
        PC.reset(symbols["_start"])
        startup = False
        if DEBUG: print(f"{t}:", display())
        continue

    # access instruction memory
    instr = Instruction(imem[pc_val], pc_val)
    # count the instruction fetch bytes -> +4 for ea. instr
    COUNT.inst_fetch_bytes += 4
    # update the instruction count and name set
    COUNT.update_instr_stats(instr.instr)

    # no op mret calls
    if instr.instr == 'mret':
        if DEBUG: print(f"{t}: PC: {pc_val:08x}, IR: {instr.val:08x}, {instr.instr} -- no-op\n")
        PC.clock(4 + pc_val)
        continue

    # get rd, rs1, and rs2 addresses and their values using regfile
    rs1_val = None
    if instr.rs1 != None:
        rs1_val = RF.read(instr.rs1)

    # get the rs2 value if a rs2 address exists
    rs2_val = None
    if instr.rs2 != None:
        rs2_val = RF.read(instr.rs2)

    # define the op1, op2 muxes
    op1_mux = make_mux(lambda: rs1_val, lambda: None, lambda: instr.imm)
    op2_mux = make_mux(lambda: rs2_val, lambda: instr.imm, lambda: instr.imm, lambda: pc_val)

    # get the alu fun val using decoder
    alufun_tup = controlFormatter(instr.get_instr(), "ALU_fun")
    # get the op1 and op2 sel
    op1_sel = controlFormatter(instr.get_instr(), "op1_sel")[1]
    op2_sel = controlFormatter(instr.get_instr(), "op2_sel")[1]

    # perform the alu operation
    alu_val = alu(op1_mux(op1_sel), op2_mux(op2_sel), alufun_tup[1])

    # get mask type
    mask_type = controlFormatter(instr.get_instr(), "mask_type")[1]

    # check if signed or not
    signed = not(instr.instr.endswith('u'))
    # read data memory -> get addr from alu
    rdata = lambda: MEM.out(as_twos_comp(alu_val), mask_type, signed)

    # get mem write and mem em
    mem_em = controlFormatter(instr.get_instr(), "mem_em")[1]
    mem_wr = controlFormatter(instr.get_instr(), "mem_wr")[1]
    # write data from alu to memory
    MEM.clock(as_twos_comp(alu_val), rs2_val, mem_wr, mask_type)
    if mem_wr:
        if DEBUG: print(f"dmem_write @ 0x{alu_val:08x} to value 0x{MEM.out(as_twos_comp(alu_val)):08x}")
        # count num of bytes written
        COUNT.mem_write_bytes += mask_type

    # get csr cmd
    csr_cmd = controlFormatter(instr.get_instr(), "csr_cmd")
    # init csr val
    csr_reg = None
    # handle csr instructions
    if instr.instr.startswith("csr"):
        csr_val = instr.rs1 if instr.instr.endswith("i") else rs1_val
        csr_reg = CSR.clock(instr.imm, csr_cmd[1], csr_val, t)
    
    # define the wb mux
    wb_mux = make_mux(lambda: 4 + pc_val, lambda: alu_val, rdata, lambda: csr_reg)
    # get wb_sel
    wb_sel = controlFormatter(instr.get_instr(), "wb_sel")[1]

    # count num of bytes read
    if wb_sel == 2:
        COUNT.mem_read_bytes += mask_type

    # get rf_wen
    rf_wen = controlFormatter(instr.get_instr(), "rf_wen")[1]
    # update register values
    RF.clock(instr.rd, wb_mux(wb_sel), rf_wen)

    # print one line at the end of the clock cycle
    if DEBUG: print(f"{t}:", display())

    # handle env calls
    # check a0 value env call type
    a0_val = RF.read(10)
    if instr.instr == 'ecall' and a0_val == 1:
        if DEBUG: print(f"ECALL({a0_val}): {RF.read(11)}\n")
        else: print(f"{elf_path} output -- {RF.read(11)}")
    elif instr.instr == 'ecall' and (a0_val == 0 or a0_val == 10):
        if DEBUG: 
            print(f"ECALL({a0_val}): " + 'EXIT\n' if a0_val == 10 else f"ECALL({a0_val}): " + 'HALT\n')
            RF.display()
        handle_test()
        if STATS:
            COUNT.display()
        break

    # check for UCB syscalls and handle them
    handle_syscall(mem_em, mem_wr, mask_type, alu_val)
    
    # define the pc mux
    pc_mux = make_mux(lambda: 4 + pc_val, lambda: instr.imm + as_twos_comp(rs1_val), lambda: instr.imm + pc_val, lambda: instr.imm + pc_val, lambda: None)

    # get branch type
    br_type = controlFormatter(instr.get_instr(), "br_type")[1]
    # get the pc sel based on instr type and whether branch is taken on not
    pc_sel = branch_taken(op1_mux(op1_sel), op2_mux(op2_sel), br_type)

    # clock logic blocks, PC is the only clocked module!
    PC.clock(pc_mux(pc_sel))
    # if a branch type instruction
    if instr.type == "sb":
        # update branch stats
        COUNT.update_branch_stats(pc_val, instr.imm + pc_val, pc_sel == 2)
    
    # update mcycle
    COUNT.mcycle += 1

    # check if max cycles reached
    if MAX_CYCLES and (t >= MAX_CYCLES):
        if DEBUG: 
            print("HALT: Max cycles reached.\n")
            # print register values at the end of program
            RF.display()
        handle_test()
        if STATS:
            COUNT.display()
        break

    # check stopping conditions on NEXT instruction
    if imem[PC.out()] == 0:
        if DEBUG: 
            print("Done -- end of program.\n")
            # print register values at the end of program
            RF.display()
        handle_test()
        if STATS:
            COUNT.display()
        break
