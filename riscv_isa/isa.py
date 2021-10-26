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

# instr dict for opcode, funct3, and funct7 lookup
instr_dict = {
    3: {
        0: 'lb',
        1: 'lh',
        2: 'lw',
        3: 'ld',
        4: 'lbu',
        5: 'lhu',
        6: 'lwu'
    },
    15: {
        0: 'fence',
        1: 'fence.i'
    },
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
    23: 'auipc',
    27: {
        0: 'addiw',
        1: 'slliw',
        5: {
            0: 'srliw',
            32: 'sraiw'
        }
    },
    35: {
        0: 'sb',
        1: 'sh',
        2: 'sw',
        3: 'sd'
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
    59: {
        0: {
            0: 'addw',
            32: 'subw'
        },
        1: 'sllw',
        5: {
            0: 'srlw',
            32: 'sraw'
        }
    },
    99: {
        0: 'beq',
        1: 'bne',
        4: 'blt',
        5: 'bge',
        6: 'bltu',
        7: 'bgeu'
    },
    103: 'jalr',
    111: 'jal',
    115: {
        0: {
            0: 'ecall',
            1: 'ebreak'
        },
        1: 'csrrw',
        2: 'csrrs',
        3: 'csrrc',
        5: 'csrrwi',
        6: 'csrrsi',
        7: 'csrrci'
    }
}

# instr type dict
instr_type = {
    'i': ['lb', 'lh', 'lw', 'ld', 'lbu', 'lhu', 'lwu',
          'fence', 'fence.i',
          'addi', 'slli', 'slti', 'sltiu', 'xori', 'srli', 'srai', 'ori', 'andi',
          'addiw', 'slliw', 'srliw', 'sraiw',
          'jalr',
          'ecall', 'ebreak', 'csrrw', 'csrrs', 'csrrc', 'csrrwi', 'csrrsi', 'csrrci'],
    'r': ['add', 'sub', 'sll', 'slt', 'sltu', 'xor', 'srl', 'sra', 'or', 'and',
          'addw', 'subw', 'sllw', 'srlw', 'sraw'],
    'u': ['auipc', 'lui'],
    'sb': ['beq', 'bne', 'blt', 'bge', 'bltu', 'bgeu'],
    'uj': ['jal'],
    's': ['sb', 'sh', 'sw', 'sd']
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
        self.imm = None
        # decode the instruction
        self.decode_inst()
    
    def decode_inst(self):
        "decodes the value into human readable instruction"
        # get the instruction from value
        self.instr = self.get_instr()
        # get the instruction type based on opcode
        self.type = self.get_instr_type()
        # figure out the rd, rs1, rs2 / immediate values
        if self.type != 's' and self.type != 'sb': # get rd is not s or sb type
            self.rd = self.get_rd()
        if self.type != 'u' and self.type != 'uj': # get rs1 value if not u or uj type
            self.rs1 = self.get_rs1()
        if self.type == 'i': # get i immediate if i type
            self.imm = self.get_iimm()
        if self.type == 'r' or self.type == 's'\
        or self.type == 'sb': # get rs2 reg if r, s, or sb type
            self.rs2 = self.get_rs2()
        if self.type == 'u': # get u immediate if u type
            self.imm = self.get_uimm()
        if self.type == 'uj': # get j immediate if uj type
            self.imm = self.get_jimm()
        if self.type == 's': # get s immediate if i type
            self.imm = self.get_simm()
        if self.type == 'sb':
            self.imm = self.get_bimm()
            
    def get_rd(self):
        "computes and returns the rd"
        return self.val >> 7 & 0x1F
    
    def get_rs1(self):
        "computes and returns the rs1"
        return self.val >> 15 & 0x1F
    
    def get_rs2(self):
        "computes and returns the rs2"
        return self.val >> 20 & 0x1F
    
    def get_iimm(self):
        "computes and returns the i immediate"
        return sextend(self.val >> 20 & 0xFFF, 12)

    def get_simm(self):
        "computes and returns the s immediate"
        s_imm = ((self.val & 0xFE000000) >> 20) | \
                ((self.val & 0x00000F00) >> 7)  | \
                ((self.val & 0x00000080) >> 7)
        return sextend(s_imm, 12)

    def get_uimm(self):
        "computes and returns the u immediate"
        return sextend(self.val & 0xFFFFF000, 32)

    def get_jimm(self):
        "computes and returns the uj immediate"
        # get imm[31:12]
        temp = self.val >> 12 & 0xFFFFF
        # rearrange to get imm[20|10:1|11|19:12]
        j_imm = (temp & 0x80000) | ((temp & 0xFF) << 11) | \
                ((temp & 0x001) << 10) | ((temp & 0x7FE00) >> 9)
        return sextend(j_imm, 20) << 1
    
    def get_bimm(self):
        "computes and returns the sb immediate"
        b_imm = ((self.val & 0x80000000) >> 20) | \
                ((self.val & 0x00000080) << 3)  | \
                ((self.val & 0x7E000000) >> 21) | \
                ((self.val & 0x00000F00) >> 8)
        return sextend(b_imm, 12) << 1

    def get_funct3(self):
        "computes and returns funct 3"
        return self.val >> 12 & 0x7

    def get_funct7(self):
        "computes and returns funct 7"
        return self.val >> 25 & 0x7F

    def get_opcode(self):
        "computes and returns opcode"
        return self.val & 0x7f
    
    def get_instr_type(self):
        "get the instr type based on the instr"
        for type in instr_type:
            for curr in instr_type[type]:
                if self.instr == curr:
                    return type

    def check_pseudo(self, rd_str, rs1_str, rs2imm_str):
        "check if the instr is a pseudo instr, if it is replace it"
        if self.instr == 'addi' and rs1_str == 'zero': # handle pseudo instr li
            return 'li', rd_str, None, rs2imm_str
        elif self.instr == 'jal': # reformat jal instr
            if rd_str == 'zero': # handle pseudo instr j
                return 'j', None, None, hex(self.pc + self.imm)[2:]
            return self.instr, rd_str, None, hex(self.pc + self.imm)[2:]
        elif self.instr == 'jalr' and rd_str == 'zero' and self.imm == 0: # handle pseudo instr jr
            return 'jr', None, rs1_str, None
        elif self.type == 'sb' and rs2imm_str == 'zero': # handle pseudo branch instrs
            return self.instr + 'z', None, rs1_str, hex(self.pc + self.imm)[2:]
        elif self.type == 'u': # reformat u type instrs
            return self.instr, rd_str, None, rs2imm_str
        elif self.type == 's': # reformat s type instrs
            return self.instr, regNumToName(self.rs2), f"{self.imm}({rs1_str})", None
        else:
            return self.instr, rd_str, rs1_str, rs2imm_str

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
        rd_str = self.rd if self.rd == None else regNumToName(self.rd)
        rs1_str = self.rs1 if self.rs1 == None else regNumToName(self.rs1)
        rs2imm_str = None
        if self.rs2 != None:
            rs2imm_str = regNumToName(self.rs2)
        elif self.imm != None:
            rs2imm_str = str(self.imm)

        # clear if all registers zero
        if rd_str == 'zero' and rs1_str == 'zero' and rs2imm_str == "0":
            rd_str = None; rs1_str = None; rs2imm_str = None

        # check and replace if pseudo or special instr
        self.instr, rd_str, rs1_str, rs2imm_str = \
        self.check_pseudo(rd_str, rs1_str, rs2imm_str)
        
        # create the human-readable code string
        readable = []
        if rd_str: # if rd exist add to output string
            readable.append(rd_str)
        if rs1_str: # if rs exist add to output string
            readable.append(rs1_str)
        if rs2imm_str: # if rs2 exist add to output string
            readable.append(rs2imm_str)

        return "{} {}\n".format(self.instr, ",".join(readable))
