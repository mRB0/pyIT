#!/usr/bin/env python

"""\

Python script for batch setting of song messages,
and sample and instrument lists, of IT files.

(c) 2008 mike burke / mrb

Todo:
 - nothing!

"""

#
# Set these to suit your needs.
#
# When set_*_msg = False, the designated message will be
# UNTOUCHED from the original.  If you want to CLEAR a
# message or sample/inst list, use set_*_msg = True and 
# an empty message.
#

# preserve_file_date: If True, new files will be created with the same
#                     modification time as the source files.

preserve_file_date = True

# enable_strftime: If True, strftime substitution will be performed on
#                  song message texts, using the file's modification
#                  time.   A strftime string reference can be found at:
#                  http://www.python.org/doc/2.5.2/lib/module-time.html

enable_strftime = True

# set_sample_msg    : Modify the sample list?
# append_sample_msg : Append to the end of existing sample names?
#                     If False, will start writing at 0;
#                     Otherwise, attempts to find the last sample,
#                     and starts writing there..
#
# If you are appending, it might make sense to insert an empty line before
# the beginning of your message, to avoid eg. a song message like:
#
#    Old message
#    old message
#    blah blah
#    old messageAPPENDED MESSAGE
#    appended message blah blah
#
# If you put {FILENAME} into a message, it will be replaced with the
# name of the file currently being processed.
#

set_sample_msg = True
append_sample_msg = False
sample_msg = (
# "123456789A123456789B12345" <- anything longer than 25 characters will be truncated
  "Sample Line 1",
  "Sample Line 2",
  "Sample Line 3",
  "and so on...",
)

set_instrument_msg = True
append_instrument_msg = False
instrument_msg = (
# "123456789A123456789B12345"
  "{FILENAME}",
  "",
  "  %Y-%m-%d",
  "  %I:%M:%S %p",
  "",
  "by me! :)",
)

set_song_msg = True
append_song_msg = False
song_msg = """\
This is a song message.
It's a multi-line Python string,
so you can use multiple lines.
This file was last modified on %d %B %Y.
"""

##########################################################
#                                                        #
#  You don't need to change anything beyond this point.  #
#                                                        #
##########################################################

import os, os.path, sys, exceptions, traceback, time
import pyIT

def add_messages(itf, filespec):
  mtime = time.localtime(os.stat(filespec).st_mtime)
  
  if enable_strftime:
    tmp_song_msg = time.strftime(song_msg, mtime)
    tmp_instrument_msg = [time.strftime(m, mtime) for m in instrument_msg]
    tmp_sample_msg = [time.strftime(m, mtime) for m in sample_msg]
  else:
    tmp_song_msg = song_msg
    tmp_instrument_msg = instrument_msg
    tmp_sample_msg = sample_msg
  
  # substitutions (only filename, so far)
  tmp_song_msg = tmp_song_msg.replace('{FILENAME}', os.path.basename(filespec))
  tmp_instrument_msg = [m.replace('{FILENAME}', os.path.basename(filespec)) for m in tmp_instrument_msg]
  tmp_sample_msg = [m.replace('{FILENAME}', os.path.basename(filespec)) for m in tmp_sample_msg]
  
  if set_song_msg:
    if append_song_msg:
      itf.Message = itf.Message + tmp_song_msg
    else:
      itf.Message = tmp_song_msg
  
  if set_instrument_msg:
    # set instrument msg

    i = 0
    if not append_instrument_msg:
      for instrument in itf.Instruments:
        if i >= len(tmp_instrument_msg):
          instrument.InstName = ''
        else:
          instrument.InstName = tmp_instrument_msg[i]
        i = i + 1

    while len(tmp_instrument_msg) > i:
      iti = pyIT.ITinstrument()
      iti.InstName = tmp_instrument_msg[i]
      itf.Instruments.append(iti)
      i = i + 1
  
  if set_sample_msg:
    # set sample msg
    
    i = 0
    if not append_sample_msg:
      for sample in itf.Samples:
        if i >= len(tmp_sample_msg):
          sample.SampleName = ''
        else:
          sample.SampleName = tmp_sample_msg[i]
        i = i + 1
    
    while len(tmp_sample_msg) > i:
      its = pyIT.ITsample()
      its.SampleName = tmp_sample_msg[i]
      itf.Samples.append(its)
      i = i + 1
  

def process(indir, outdir):
  infiles = [f for f in os.listdir(indir) if f.upper()[-3:] == '.IT']
  
  if not os.path.exists(outdir):
    sys.stderr.write("W: " + outdir + " doesn't exist so I'm creating it\n")
    os.mkdir(outdir)
  
  if not os.path.isdir(outdir):
    sys.stderr.write("E: " + outdir + " is not a directory\n")
    raise exceptions.OSError()
  
  for filename in infiles:
    try:
      infilespec = os.path.join(indir, filename)
      sys.stderr.write('I: ' + infilespec)
      itf = pyIT.ITfile()
      itf.open(infilespec)
      
      sys.stderr.write(" => ")
      
      add_messages(itf, infilespec)
      
      outfilespec = os.path.join(outdir, filename)
      
      sys.stderr.write(outfilespec)
      itf.write(outfilespec)
      
      if preserve_file_date:
        statresult = os.stat(infilespec)
        os.utime(outfilespec, (statresult.st_atime, statresult.st_mtime))
      
      sys.stderr.write('\n')
    except:
      sys.stderr.write("\nE: error processing " + filename + ":\n")
      traceback.print_exc()

if __name__ == '__main__':
  if not len(sys.argv) == 3:
    sys.stderr.write(sys.argv[0] + " indir outdir! morans\n")
    sys.exit(1)
  process(sys.argv[1], sys.argv[2])
