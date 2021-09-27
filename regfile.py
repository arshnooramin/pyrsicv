from riscv_isa.isa import regNumToName

class RegFile:
    def __init__(self):
        """
        Represents a register file
        regs is the register array
        """
        self.regs = [None]*32
        self.regs[0] = 0 # set the zero reg to value 0

    # a function to read the register value at addr
    def read(self, addr):
        return self.regs[addr]
    
    # a clocked writer function that updates the register on the neg clock edge
    def clock(self, addr, val, en):
        # return if value is null or address is invalid or if enable bit is not set
        if val == None or not en or addr <= 0 or addr >= 32:
            return
        # else update the value
        self.regs[addr] = val
        
    # a display function to print the registers and the respective values
    def display(self):
        fmt_reg = lambda i: f"{self.regs[i]:09x}" \
                  if self.regs[i] != None else " xxxxxxxx"
        for y in range(0, 32, 4):
            print(" ".join([f"{regNumToName(i).rjust(4)}: {fmt_reg(i)}" \
                  for i in range(y, y+4)]))

# testbench for regfile
if __name__=="__main__":
    # instantiate the reg file class
    regfile = RegFile()
    # how many cycles to run the clock for
    ticks = 32
    # address var
    addr = 0
    # loop for the clock signal
    for _ in range(ticks):
        regfile.clock(addr, 0x42 + addr, True)
        addr += 1
    # display the register
    regfile.display()