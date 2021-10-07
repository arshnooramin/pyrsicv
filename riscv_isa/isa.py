from os import stat
from .csr_list import csrs
from pydigital.utils import sextend
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
    0: 'zero', 1: 'ra', 2: 'sp', 3: 'gp', 4: 'tp',
    5: 't0', 6: 't1', 7: 't2', 8: 's0', 9: 's1',
    10: 'a0', 11: 'a1', 12: 'a2', 13: 'a3', 14: 'a4', 
    15: 'a5', 16: 'a6', 17: 'a7', 18: 's2', 19: 's3',
    20: 's4', 21: 's5', 22: 's6', 23: 's7', 24: 's8',
    25: 's9', 26: 's10', 27: 's11', 28: 't3', 29: 't4',
    30: 't5', 31: 't6'
}

# instr dict for opcode, funct3, and funct7 lookup
instr_dict = {
    19: {
        0: 'addi',
        1: 'slli',
        2: 'slti',
        3: 'sltiu',
        4: 'xori',
        5: {
            0: 'srli',
            32: 'srai'
        },
        6: 'ori',
        7: 'andi'
    },
    51: {
        0: {
            0: 'add',
            32: 'sub'
        },
        1: 'sll',
        2: 'slt',
        3: 'sltu',
        4: 'xor',
        5: {
            0: 'srl',
            32: 'sra'
        },
        6: 'or',
        7: 'and'
    },
    55: 'lui',
    115: {
        0: {
            0: 'ecall',
            1: 'ebreak'
        }
    }
}

# instr type dict
instr_type = {
    'i': ['addi', 'slli', 'slti', 'sltiu', 'xori', 'srli',
          'srai', 'ori', 'andi', 'ecall'],
    'r': ['add', 'sub', 'sll', 'slt', 'sltu', 'xor', 'srl', 
          'sra', 'or', 'and'],
    'u': ['lui']
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
        # init funct7 and funct3
        self.funct3 = 0; self.funct7 = 0
        # init rd, rs1, rs2
        self.rd = None; self.rs1 = None; self.rs2 = None
        # init immediates
        self.i_imm = None; self.u_imm = None
        # decode the instruction
        self.decode_inst()
    
    def decode_inst(self):
        # get the instruction from value
        self.instr = self.get_instr()
        # get the instruction type based on opcode
        self.type = self.get_instr_type()
        # if instruction type is R
        # if self.type == 'i' or self.type == 'r': # get the rd and rs1
        self.rd = self.get_rd()
        self.rs1 = self.get_rs1()
        if self.type == 'i': # if i imm
            self.i_imm = self.get_iimm()
        elif self.type == 'r': # if rs2
            self.rs2 = self.get_rs2()
        elif self.type == 'u': # if u imm
            self.u_imm = self.get_uimm()

    # returns the rd val
    def get_rd(self):
        return self.val >> 7 & 0x1F
    
    # returns the rs1 val
    def get_rs1(self):
        return self.val >> 15 & 0x1F
    
    def get_rs2(self):
        return self.val >> 20 & 0x1F
    
    def get_iimm(self):
        return sextend(self.val >> 20 & 0xFFF, 12)

    def get_uimm(self):
        return sextend(self.val >> 12 & 0xFFFFF, 20)
    
    # returns the funct3 val
    def get_funct3(self):
        return self.val >> 12 & 0x7

    # returns the funct7 val
    def get_funct7(self):
        return self.val >> 25 & 0x7F

    def get_opcode(self):
        return self.val & 0x7f
    
    def get_instr_type(self):
        "get the instr type based on the instr"
        for type in instr_type:
            for curr in instr_type[type]:
                if self.instr == curr:
                    return type

    def check_pseudo(self, rs1_str):
        "check if the instr is a pseudo instr, if it is replace it"
        if self.instr == 'addi' and rs1_str == 'zero':
            return 'li', None
        if self.type == 'u':
            return self.instr, None
        else:
            return self.instr, rs1_str

    def get_instr(self):
        "get the instr from the value"
        # determine what instruction it is
        obj = instr_dict[self.get_opcode()]
        if type(obj) == str:
            return obj
        else:
            # get funct3
            self.funct3 = self.get_funct3()
            obj = obj[self.funct3]
            if type(obj) == str:
                return obj
            else:
                # get funct7
                self.funct7 = self.get_funct7()
                return obj[self.funct7]
    
    def __str__ (self):
        """
        Translates the machine instructions into human-readable assembly instructions
        """
        rd_str = reg_symb[self.rd]
        rs1_str = reg_symb[self.rs1]
        if self.rs2 != None:
            rs2imm_str = reg_symb[self.rs2]
        elif self.i_imm != None:
            rs2imm_str = self.i_imm
        elif self.u_imm != None:
            rs2imm_str = self.u_imm

        # clear if all registers zero
        if rd_str == 'zero' and rs1_str == 'zero' and rs2imm_str == 0:
            rd_str = None; rs1_str = None; rs2imm_str = None

        # check and replace if pseudo instr
        self.instr, rs1_str = self.check_pseudo(rs1_str)
        
        # create the human-readable code string
        readable = '{} '.format(self.instr)
        if rd_str: # if rd exist add to output string
            readable += rd_str
        if rs1_str: # if rs exist add to output string
            readable += ',{}'.format(rs1_str)
        if rs2imm_str: # if rs2 exist add to output string
            readable += ',{}'.format(rs2imm_str)

        return readable + '\n'
