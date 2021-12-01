"""
predictors.py
=========
All the types of predictors
"""
import math
from tabulate import tabulate

class BranchHistory:
    "represents the BHT for a local predictor"
    def __init__(self, size, bits, word_size):
        "initialize a BHT of size and of resolution bits (only supports 1 and 2 bit BHT)"
        self.size = size
        self.bits = bits
        self.index_bits = int(math.log(size, 2))
        self.byte_offset = int(math.log(word_size, 2))
        self.bht = {}
        self.init_bht()
        self.corr_pred = 0; self.incorr_pred = 0
        self.outcome = [["Byte Address", "BHT Index", "Outcome", "Prediction", "Correct?"]]
    
    def init_bht(self):
        "initialize the BHT cache dictionary"
        for key in range(self.size):
            self.bht[key] = (1 << self.bits) - 1
    
    def get_idx(self, pc):
        return (pc >> self.byte_offset) & ((1 << self.index_bits) - 1)
    
    def predict_update(self, pc, taken):
        "make a prediction based on PC, update the BHT and outcome table returns tuple - (taken?, correct?)"
        # get the index for the BHT
        idx = self.get_idx(pc)
        curr_out = [hex(pc), str(idx), "Taken" if taken else "Not Taken"]
        if self.bits == 1:
            if self.bht[idx] == 1:
                curr_out.append("Taken")
                if taken: 
                    curr_out.append("Yes")
                    self.corr_pred += 1
                else:
                    curr_out.append("No")
                    self.incorr_pred += 1
                    self.bht[idx] -= 1
            else:
                curr_out.append("Not Taken")
                if not(taken): 
                    curr_out.append("Yes")
                    self.corr_pred += 1
                else:
                    curr_out.append("No")
                    self.incorr_pred += 1
                    self.bht[idx] += 1
        elif self.bits == 2:
            if self.bht[idx] == 3 or self.bht[idx] == 2:
                curr_out.append("Taken")
                if taken: 
                    curr_out.append("Yes")
                    self.corr_pred += 1
                    if self.bht[idx] == 2: self.bht[idx] += 1
                else:
                    curr_out.append("No")
                    self.incorr_pred += 1
                    self.bht[idx] -= 1
            else:
                curr_out.append("Not Taken")
                if not(taken): 
                    curr_out.append("Yes")
                    self.corr_pred += 1
                    # decrement the saturating counter only if possible
                    if self.bht[idx] == 1: self.bht[idx] -= 1
                else:
                    curr_out.append("No")
                    self.incorr_pred += 1
                    # increment the saturating counter
                    self.bht[idx] += 1
        self.outcome.append(curr_out)
        return curr_out[-2:]

    def display(self):
        print(f"-- LOCAL Predictor {self.size}-Entry, {self.bits}-Bit BHT")
        print("Outcome Table:")
        print(tabulate(self.outcome[1:], headers=self.outcome[0], tablefmt="github") + '\n')
        print("Branch History Table:")
        accuracy = self.corr_pred/(self.corr_pred+self.incorr_pred)
        print(tabulate([(bht[0], f"{bht[1]:02b}") for bht in list(self.bht.items())], \
            headers=["Index", "Branch History"], tablefmt="github") + '\n')
        print(f"Prediction Accurancy:\n {accuracy:.2f}\n")

class PatternHistory:
    "represents the PHT for a global predictor"
    def __init__(self, bits):
        self.bits = bits
        self.size = 2**bits
        self.history = (1 << self.bits) - 1
        self.pht = {}
        self.init_pht()
        self.corr_pred = 0; self.incorr_pred = 0
        self.outcome = [["Byte Address", "Global History", "Outcome", "Prediction", "Correct?"]]

    def init_pht(self):
        "initialize the PHT cache dictionary"
        for key in range(self.size):
            self.pht[key] = 1

    def predict_update(self, pc, taken):
        curr_out = [hex(pc), f"{self.history:b}", "Taken" if taken else "Not Taken"]
        if self.pht[self.history] == 1:
            curr_out.append("Taken")
            if taken: 
                curr_out.append("Yes")
                self.corr_pred += 1
            else:
                curr_out.append("No")
                self.incorr_pred += 1
                self.pht[self.history] -= 1
        else:
            curr_out.append("Not Taken")
            if not(taken): 
                curr_out.append("Yes")
                self.corr_pred += 1
            else:
                curr_out.append("No")
                self.incorr_pred += 1
                self.pht[self.history] += 1
        # update global history
        self.history = (self.history >> 1) | (int(taken) << (self.bits - 1))
        self.outcome.append(curr_out)

    def display(self):
        print(f"-- GLOBAL Predictor {self.size}-Entry, {self.bits}-Bit PHT")
        print("Outcome Table:")
        print(tabulate(self.outcome[1:], headers=self.outcome[0], tablefmt="github") + '\n')
        print("Pattern History Table:")
        accuracy = self.corr_pred/(self.corr_pred+self.incorr_pred)
        print(tabulate([(f"{pht[0]:b}", pht[1]) for pht in list(self.pht.items())], \
            headers=["Index", "Pattern History"], tablefmt="github") + '\n')
        print(f"Prediction Accurancy:\n {accuracy:.2f}\n")

class GShare:
    "represents the global selects lobal GShare predictor"
    def __init__(self, g_bits, b_size, b_bits, word_size):
        "initialize the GShare predictor with the specified bht and size"
        self.g_bits = g_bits
        self.b_size = b_size
        self.mux = [BranchHistory(b_size, b_bits, word_size) for _ in range(2**self.g_bits)]
        self.history = (1 << g_bits) - 1
        self.corr_pred = 0; self.incorr_pred = 0
        self.outcome = [["Byte Address", "Global History", "BHT Index", "Outcome", "Prediction", "Correct?"]]
    
    def predict_update(self, pc, taken):
        curr_out = [hex(pc), f"{self.history:b}", self.mux[self.history].get_idx(pc),"Taken" if taken else "Not Taken"]
        pred_arr = self.mux[self.history].predict_update(pc, taken)
        if pred_arr[1] == "Yes": 
            self.corr_pred += 1
        else: 
            self.incorr_pred += 1
        curr_out += pred_arr
        # update global history
        self.history = (self.history >> 1) | (int(taken) << (self.g_bits - 1))
        self.outcome.append(curr_out)

    def display(self):
        print(f"-- GSHARE Predictor {self.g_bits}-bit global history {2**self.g_bits}-BHTs")
        print("Outcome Table:")
        print(tabulate(self.outcome[1:], headers=self.outcome[0], tablefmt="github") + '\n')
        print("Branch History Tables:")
        out = [[f"BHT ({i})" for i in range((2**self.g_bits)+1)] for _ in range(self.b_size+1)]
        out[0][0] = "Index"
        for i, bht_obj in enumerate(self.mux):
            for j, bht in enumerate(list(bht_obj.bht.items())):
                if i == 0:
                    out[j+1][i] = bht[0]
                out[j+1][i+1] = f"{bht[1]:02b}"
        print(tabulate(out[1:], headers=out[0], tablefmt="github") + '\n')
        accuracy = self.corr_pred/(self.corr_pred+self.incorr_pred)
        print(f"Prediction Accurancy:\n {accuracy:.2f}\n")


