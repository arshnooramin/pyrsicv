"""
predictors.py
=========
All the types of predictors
"""
import math

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
    
    def predict_update(self, pc, taken):
        "make a prediction based on PC, update the BHT and outcome table"
        # get the index for the BHT
        idx = (pc >> self.byte_offset) & ((1 << self.index_bits) - 1)
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

    def display(self):
        for line in self.outcome:
            print("\t|\t".join(line))
        print()
        print(self.bht)
        print(f"Accurancy: {self.corr_pred/(self.corr_pred+self.incorr_pred)}")
