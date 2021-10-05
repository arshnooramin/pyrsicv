# function to define/make muxes
def make_mux(*args):
   return lambda i: args[i]()

# testbench for mux
if __name__=="__main__":
   mux = make_mux(lambda: 1,lambda: 2,lambda: 3,lambda: 4, lambda: 5)
   for i in range(5):
      print(f"mux({i}) == {mux(i)}")