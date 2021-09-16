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

# reg symbol table
reg_symb = {
    0: 'zero', 1: 'ra', 10: 'a0', 11: 'a1', 12: 'a2', 
    13: 'a3', 14: 'a4', 15: 'a5', 16: 'a6', 17: 'a7'
}

# instr dict for opcode, funct3, and funct7 lookup
instr_dict = {
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

# instr type dict
instr_type = {
    'i': ['addi', 'ecall'],
    'r': ['add', 'sub']
}

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
    
    def get_instr_type(self, instr):
        "get the instr type based on the instr"
        for type in instr_type:
            for curr in instr_type[type]:
                if instr == curr:
                    return type

    def check_pseudo(self, instr, rs1):
        "check if the instr is a pseudo instr, if it is replace it"
        if instr == 'addi' and rs1 == 'zero':
            return 'li', None
        else:
            return instr, rs1

    def get_instr(self):
        "get the instr from the value"
        # determine what instruction it is
        obj = instr_dict[self.val & 0x7f]
        if type(obj) == str:
            return obj
        else:
            # get funct3
            funct3 = self.val >> 12 & 0x7
            obj = obj[funct3]
            if type(obj) == str:
                return obj
            else:
                # get funct7
                funct7 = self.val >> 25 & 0x7F
                return obj[funct7]

    def __str__ (self):
        """
        Translates the machine instructions into human-readable assembly instructions
        """
        # get the instruction from value
        instr = self.get_instr()
        
        # get the instruction type based on opcode
        type = self.get_instr_type(instr)

        # set rd, rs1, rs2 or imm
        rd = None; rs1 = None; rs2imm = None
        # if instruction type is R
        if type == 'i' or type == 'r': # get the rd and rs1
            rd = reg_symb[self.val >> 7 & 0x1F]
            rs1 = reg_symb[self.val >> 15 & 0x1F]
            if type == 'r': # get rs2
                rs2imm = reg_symb[self.val >> 20 & 0x1F]
            elif type == 'i': # get imm
                rs2imm = self.val >> 20 & 0xFFF
        # clear if all registers zero
        if rd == 'zero' and rs1 == 'zero' and rs2imm == 0:
            rd = None; rs1 = None; rs2imm = None

        # check and replace if pseudo instr
        instr, rs1 = self.check_pseudo(instr, rs1)
        
        # create the human-readable code string
        readable = '{}\t\t'.format(instr)
        if rd: # if rd exist add to output string
            readable += rd
        if rs1: # if rs exist add to output string
            readable += ',{}'.format(rs1)
        if rs2imm: # if rs2 exist add to output string
            readable += ',{}'.format(rs2imm)

        return readable + '\n'
