"""
test.py
========
Test script to run multiple unit tests on the onestage simulator.
"""

import os, sys

# check if a path was provided
if len(sys.argv) < 2:
    exit("ERROR: test directory path not provided!")

# get the inputted test directory path
test_dir = sys.argv[1]

# fix formatting
if not test_dir.endswith("\\"): test_dir += "\\"

# check if path is a directory
if not os.path.isdir(test_dir):
    exit("ERROR: provided path is not a directory")

# loop through files in the test directory
for elf_file in os.listdir(test_dir):
    # execute the test for each elf file
    os.system(f"python onestage_elf.py {test_dir}{elf_file} -t -s")

