from os import stat
from .csr_list import csrs
class BadInstruction(Exception):
    pass

# build csr lookup
csrd = {k:v for k,v in csrs}

def regNumToName(num):
    if type(num) != int or num < 0 or num > 31:
        raise BadInstruction()
    return ['zero','ra','sp','gp',  # 0..3
            'tp', 't0', 't1', 't2', # 4..7
            's0', 's1', 'a0', 'a1', # 8..11
            'a2', 'a3', 'a4', 'a5', # 12..15
            'a6', 'a7', 's2', 's3', # 16..19
            's4', 's5', 's6', 's7', # 20..23
            's8', 's9', 's10', 's11', # 24..27]
            't3', 't4', 't5', 't6'][num] # 28..31

class Instruction():
    "represents/decodes RISCV instructions"    
    def __init__ (self, val, pc, symbols = {}):
        """
        Decodes a risc-v instruction word
        val is the machine code word
        pc is the pc value used to format pc-relative assembly instructions
        symbols is an optional symbol table to decode addresses in assembly output 
        """
        self.val = val        
        self.pc = pc # pc relative instrs need pc to compute targets for display
        self.symbols = symbols
        # opcode for different types of instructions
        self.op_dict = {
            'r': [0b0110011, 0b0111011],
            'i': [0b0000011, 0b0001111, 0b0010011, 0b0011011, 0b1100111, 0b1110011]
        }
        # rd symbol table
        self.reg_symb = {
            0: 'zero', 1: 'ra', 10: 'a0', 11: 'a1', 12: 'a2', 13: 'a3', 
            14: 'a4', 15: 'a5', 16: 'a6', 17: 'a7'
        }
        # instruction dictionary (opcode/funct3/funct7)
        self.instr_dict = {
            19: {
                0: 'addi'
            },
            51: {
                0: {
                    0: 'add',
                    32: 'sub'
                }
            },
            115: {
                0: {
                    0: 'ecall',
                    1: 'ebreak'
                }
            }
        }
    
    def get_inst_type(self, opcode):
        for inst_type in self.op_dict:
            for op in self.op_dict[inst_type]:
                if opcode == op:
                    return inst_type
    
    def __str__ (self):
        """
        Translates the machine instructions into human-readable assembly instructions
        """
        # analyze the first six bits
        opcode = self.val & 0x7f

        # get the instruction type based on opcode
        inst_type = self.get_inst_type(opcode)

        # determine what instruction it is
        instr_obj = self.instr_dict[opcode]
        if type(instr_obj) == str:
            instr = instr_obj
        else:
            # get funct3
            funct3 = self.val >> 12 & 0x7
            instr_obj = instr_obj[funct3]
            if type(instr_obj) == str:
                instr = instr_obj
            else:
                # get funct7
                if inst_type == 'r':
                    funct7 = self.val >> 25 & 0x7F
                elif inst_type == 'i':
                    funct7 = self.val >> 20 & 0xFFF
                else:
                    return None
                instr = instr_obj[funct7]

        rd = None; rs1 = None; rs2imm = None
        # if instruction type is R
        if inst_type == 'i' or inst_type == 'r':
            # get the rd
            rd = self.reg_symb[self.val >> 7 & 0x1F]
            rs1 = self.reg_symb[self.val >> 15 & 0x1F]
        if inst_type == 'r':
            # get rs2
            rs2imm = self.reg_symb[self.val >> 20 & 0x1F]
        elif inst_type == 'i':
            # get imm
            rs2imm = self.val >> 20 & 0xFFF

        # check for pseudo operations
        if instr == 'addi' and rs1 == 'zero':
            instr = 'li'; rs1 = None
        
        # clear if all registers zero
        if rd == 'zero' and rs1 == 'zero' and rs2imm == 0:
            rd = None; rs1 = None; rs2imm = None

        readable = '{}\t\t'.format(instr)
        if rd:
            readable += rd
        if rs1:
            readable += ',{}'.format(rs1)
        if rs2imm:
            readable += ',{}'.format(rs2imm)

        return readable + '\n'
