"""
stats.py
=========
For statistics of the datapath
"""

class Stats:
    """
    Stats class that updates and keeps track of the stats of the datapath
    """
    def __init__(self):
        "initialize different types of stats"
        self.branch = {
            "forward_taken": 0,
            "backward_not_taken": 0,
            "backward_taken": 0,
            "forward_not_taken": 0
        }
        self.inst_count = {
            "arithmetic": 0,
            "csr": 0,
            "branch": 0,
            "jump": 0,
            "store": 0,
            "jump_reg": 0,
            "load": 0,
            "misc": 0
        }
        self.inst_name = {
            "arithmetic": set(),
            "csr": set(),
            "branch": set(),
            "jump": set(),
            "store": set(),
            "jump_reg": set(),
            "load": set(),
            "misc": set()
        }
        self.inst_fetch_bytes = 0
        self.mcycle = 0
        self.mem_write_bytes = 0
        self.mem_read_bytes = 0
    
    def update_instr_stats(self, instr):
        "figures out the instruction type and updates respective counter"
        if instr.startswith("csr"):
            instr_type = "csr"
        elif instr.startswith("b"):
            instr_type = "branch"
        elif instr == "jal":
            instr_type = "jump"
        elif instr in ["sb", "sh", "sw", "sd"]:
            instr_type = "store"
        elif instr == "jalr":
            instr_type = "jump_reg"
        elif instr.startswith("l"):
            instr_type = "load"
        elif instr in ["ecall", "ebreak", "fence", "fence.i", "mret"]:
            instr_type = "misc"
        else:
            instr_type = "arithmetic"
        self.inst_name[instr_type].add(instr)
        self.inst_count[instr_type] += 1
    
    def update_branch_stats(self, pc, target, taken):
        if (target < pc):
            if taken:
                self.branch["backward_taken"] += 1
            else:
                self.branch["backward_not_taken"] += 1
        else:
            if taken:
                self.branch["forward_taken"] += 1
            else:
                self.branch["forward_not_taken"] += 1
    
    def display(self):
        # print branch stats
        print("-- BRANCH Statistics")
        for key in self.branch:
            print(f"{key}: {self.branch[key]}")
        # print new line char
        print()

        # print instr stats
        print("-- INSTRUCTION Statistics")
        for key in self.inst_name:
            print(f"{key} (count: {self.inst_count[key]}): {self.inst_name[key]}")
        # print another new line char
        print()

        # print overall stats
        print("-- OVERALL Statistics")
        print(f"instruction fetch: {self.inst_fetch_bytes} bytes")
        print(f"mcycle: {self.mcycle} cycles")
        print(f"memory write: {self.mem_write_bytes} bytes")
        print(f"memory read: {self.mem_read_bytes} bytes")
