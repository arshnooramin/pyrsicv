class regfile():
   """
   Implements the register file of a CPU
   """
   def __init__(self):
       "create a counter with the given bit width"

   def read(self, rs):
       return

   def clock(self, wa, wd, en):
       # if reset signal is true or high reset the value
       if reset:
           self._value = 0
       "clock the counter"       
       if self._value == None or reset: # no counts in reset
           return
       self._value = (self._value + 1) & self._mask
 
# lambda function to define the reset signal
reset_val = lambda: reset

# ==== main simulation ====
# create a counter component
c1 = counter(reset_val)
t = 0 # simulation time
 
# helper function to "run" a clock cycle
# for a given "system" of modules with a clock method
def run(system, monitor: lambda: "", ticks = 1):
   global t  # simulation time is a global
   last_str = None
   for _ in range(ticks):
       # sample inputs before clocking
       args = [[y() for y in x._args] for x in system]
       # now clock with sampled inputs
       [module.clock(*arg) for module,arg in zip(system, args)]
       # emulate a monitor function, only print on change
       test = monitor()
       if last_str == None or test != last_str:
           print(f"{t:20d}:", test)
           last_str = test
       # increment simulation time
       t += 1
 
# a monitor function
def monitor():
   if c1.count() == None:
       return "value = xx (xx)"
   else:
       return f"value = {c1.count():2x} ({c1.count():d})"

# run the testbench
reset = False
run([c1], monitor, 3)
reset = True 
run([c1], monitor, 3)
reset = False
run([c1], monitor, 3)
reset = True
run([c1], monitor, 3)
reset = False
run([c1], monitor, 3)