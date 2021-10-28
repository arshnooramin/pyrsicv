"""
control.py
========
Generates a table for the control signals for each of the required
instructions - outputs a csv file with the required signals and values
"""

import csv
from riscv_isa.decoder import control, enums

# the required instructions to decode
req = ["add", "mul", "sub", "sll", "mulh", "slt", "xor", "div", "srl", 
       "sra", "or", "rem", "and", "lb", "lh", "lw", "addi", "slli",
       "slti", "xori", "srli", "srai", "ori", "andi", "ecall", "sb",
       "sh", "sw", "beq", "bne", "lui", "jal"]

# a helper method to get control signal enums and their values
def controlFormatter(instr, field):
    obj = control[instr]
    sig_type = obj.renums[field][getattr(obj,field)]
    val = enums[field][sig_type]
    return sig_type, val

if __name__=="__main__":
# opens and writes to a csv file
    with open('control_table.csv', 'w', newline='') as csvfile:
        fields = control[list(control.keys())[0]].fields.copy()
        fields.insert(0, "instr")
        writer = csv.writer(csvfile)

        writer.writerow(fields)

        for instr in req:
            if instr not in control:
                vals = ["xx"]*len(fields)
                vals[0] = instr
                writer.writerow(vals)
            else:
                out = ["%s (%s)" % controlFormatter(instr, field) \
                    for field in control[instr].fields]
                out.insert(0, instr)
                writer.writerow(out)