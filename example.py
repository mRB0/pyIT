#!/usr/bin/env python

import sys
import os

import pyIT

def add_pattern(itmodule):

    # Create a new pattern
    new_pattern = pyIT.ITpattern()

    # Put a note into the first channel of every fourth row
    channel = 0
    for row in range(0, len(new_pattern.Rows), 4):
        new_note = pyIT.ITnote()

        new_note.Note = 60 + (row / 4) # C-5, then C#5, D-5, etc.
        new_note.Volume = max(64 - row, 0) # Vol 64, then 60, etc. down to 0
        new_note.Instrument = 1 # First instrument
        
        new_pattern.Rows[row][channel] = new_note

        
    # Add the pattern to the module, and add a reference to it in the order list
    new_pattern_idx = len(itmodule.Patterns)
    
    itmodule.Patterns.append(new_pattern)
    itmodule.Orders.append(new_pattern_idx)

def alter(input_file, output_file):
    workfile = pyIT.ITfile()
    
    if input_file is not None and os.path.exists(input_file):
        # Open existing file
        workfile.open(input_file)
        
    # Add a pattern
    add_pattern(workfile)
        
    # Save new output file
    workfile.write(output_file)

    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: %s outfile.it [infile.it]" % (sys.argv[0],))
        print("")
        print("Load infile.it, add a pattern to it, and re-save as outfile.it")
        print("")
        print("If infile.it is omitted, create a new empty IT file instead, and add a")
        print("pattern to that.")
    else:
        alter(sys.argv[2] if len(sys.argv) >= 3 else None,
              sys.argv[1])
