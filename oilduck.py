#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import os.path
import logging
import random

import pyIT

class composer(object):
    
    # weighted chord changes
    # influences how likely each chord is to be chosen from a given chord
    wt_chord_change = [
        [ -25, -50,   0,  25,  40,   0, -99], # I   -> I, II, III, ...
        [  25, -45, -10,  60,  60,   0, -99], # II  -> I, II, III, ...
        [  25, -50, -60,  45,  60, -70, -99], # III -> I, II, III, ...
        [  65, -10,  15,   0,  45,  25, -99], # IV  -> I, II, III, ...
        [  65,   0,   0,  45,   0,  20, -99], # V   -> I, II, III, ...
        [  40, -50,  30,   0, -10, -30, -99], # VI  -> I, II, III, ...
        [  65,   0,   0,  25,  40,   0, -50], # VII -> I, II, III, ...
    ]
    
    # note locations in each mode
    modes = {
        "major":
            [ 0, 2, 4, 5, 7, 9, 11 ],
        "minor":
            [ 0, 2, 3, 5, 7, 8, 10 ],
        "mixolydian":
            [ 0, 2, 4, 5, 7, 9, 10 ],
        "lydian":
            [ 0, 2, 4, 6, 7, 9, 11 ],
        "phrygian":
            [ 0, 1, 3, 5, 7, 8, 10 ],
        "dorian":
            [ 0, 2, 3, 5, 7, 9, 10 ],
        "locrian":
            [ 0, 1, 3, 5, 6, 8, 10 ],
    }
    
    def __init__(self, key, mode_name):
        self.key = key
        self.mode_name = mode_name
    
    def insert_dummy_stuff(self):
        self.workfile.Patterns.append(pyIT.ITpattern())
        self.workfile.Orders.append(0)
    
    def devise_pattern(self):
        new_ptn = pyIT.ITpattern()
        self.workfile.Patterns.append(new_ptn)
        self.workfile.Orders.append(len(self.workfile.Patterns)-1)
        
        tonic = self.key # C-5
        mode = self.modes[self.mode_name]
        
        chord = 0
        
        ptndelay = 4 # rows between chord changes
        
        for i in xrange(16):
            row = new_ptn.Rows[i*ptndelay]
            
            # write notes of chord
            for j in xrange(3):
                octave = 0
                note_idx = j*2 + chord
                
                octave = note_idx / len(mode)
                note_idx = note_idx % len(mode)
                    
                row[j].Note = tonic + (12*octave) + mode[note_idx]
                row[j].Instrument = 1
            
            # choose next chord
            ewt = [w+random.randint(-100, 100) for w in self.wt_chord_change[chord]]
            chord = ewt.index(max(ewt))
        
    def compose(self, input_file, output_file):
        self.workfile = pyIT.ITfile()
        
        if input_file is not None and os.path.exists(input_file):
            self.workfile.open(input_file)
        
        # erase patterns
        self.workfile.Patterns = []
        self.workfile.Orders = []
        
        # DEVISE PATTERN
        self.devise_pattern()
        
        # save file
        self.workfile.write(output_file)
    
    
if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("USAGE: %s inputfile.it outputfile.it mode key" % (sys.argv[0],))
        print("  key should be a number, 60 is C-5")
        print("  mode should be one of %s" % (', '.join(sorted(composer.modes)),))
        print("       if inputfile.it is not found, outputfile.it will be created from empty")
    else:
        composer(int(sys.argv[4]), sys.argv[3]).compose(sys.argv[1], sys.argv[2])
