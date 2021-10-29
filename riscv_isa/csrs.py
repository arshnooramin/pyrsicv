"""
Riscv basic CSR implementation 
Alan Marchiori
2021
"""

from collections import defaultdict

from riscv_isa import isa
from riscv_isa.decoder import enums
from riscv_isa.csr_list import csrs

class CsrMemory():
    """
    A RISC CSR memory, allows read/write to any address.
    """
    def __init__(self):        
        self.regs = defaultdict(int)

    def clock(self, csr, cmd, value, cycle):
        ret = None
        self.regs[0xb00] = cycle # update mcycle csr
        if cmd == enums['csr_cmd']['CSR.W']:
            # write
            self.regs[csr] = value
        elif cmd == enums['csr_cmd']['CSR.C']:
            # read and clear
            ret = self.regs[csr]
            self.regs[csr] &= ~value
        elif cmd == enums['csr_cmd']['CSR.S']:
            # read and set (bits in value)
            ret = self.regs[csr]
            self.regs[csr] |= value
            
        elif cmd == enums['csr_cmd']['CSR.I']:
            # ret, break, call and others use this, guessing it means ignore
            pass
        # CSR.N means NO CSR access ?

        return ret
