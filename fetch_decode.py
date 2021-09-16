# filename: fetch_decode.py
import itertools
from pydigital.memory import readmemh
from pydigital.register import Register
from riscv_isa import Instruction
 
# the PC register
PC = Register()
 
# construct a memory segment for instruction memory
# load the contents from the 32-bit fetch_test hex file (big endian)
imem = readmemh('riscv_isa/programs/fetch_test.hex',
   word_size = 4, byteorder = 'big')
 
def display():
   if pc_val == None:
       return "PC: xxxxxxxx, IR: xxxxxxxx"
   else:
       return f"PC: {pc_val:08x}, IR: {instr.val:08x}, {instr}"
 
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
       print(f"{t:20d}:", display())
       continue
  
   # access instruction memory
   instr = Instruction(imem[pc_val], pc_val)
 
   # print one line at the end of the clock cycle
   print(f"{t:20d}:", display())
 
   # clock logic blocks, PC is the only clocked module!
   # here the next pc value is always +4
   PC.clock(4 + pc_val)
  
   # check stopping conditions on NEXT instruction
   if PC.out() > 0x1100:
       print("STOP -- PC is large! Is something wrong?")
       break
   if imem[PC.out()] == 0:
       print("Done -- end of program.")
       break