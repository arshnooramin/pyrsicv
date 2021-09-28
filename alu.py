aluNumToOp = ['x','xor','cp','sltu',   # 0..3
              'and', 'add', 'slt', 'sra', # 4..7
              'sub', 'srl', 'sll', 'or']  # 8..11

# define a function to implement ALU
def alu(op1, op2, alu_fun):
    # figure out the op and perform the respective op
    if alu_fun == 1: # xor
        return op1 ^ op2
    if alu_fun == 2: # cp
        return op1
    if alu_fun == 3: # sltu
        return op1 * (2**op2)
    if alu_fun == 4: # and
        return op1 & op2
    if alu_fun == 5: # add
        return op1 + op2
    if alu_fun == 6: # slt
        return 1 if op1 < op2 else 0
    if alu_fun == 7: # sra
        return op1 >> op2
    if alu_fun == 8: # sub
        return op1 - op2
    if alu_fun == 9: # srl
        return (op1 & 0xffffffff) >> op2
    if alu_fun == 10: # sll
        return (op1 & 0xffffffff) << op2
    if alu_fun == 11: # or
        return op1 | op2
    # else the output is 0
    return 0

# testbench for alu
if __name__=="__main__":
    op1 = 0x100; op2 = 0x2
    for i in range(len(aluNumToOp)):
        out = alu(op1, op2, i)
        print(f"{op1:x}\t{aluNumToOp[i]}\t{op2:x}\t=\t{out:x}")
