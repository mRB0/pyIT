#!/usr/bin/env python

"""\

Python module for handling Impulse Tracker files.

(c) 2008 mike burke / mrb / mrburke@gmail.com

doesn't and won't handle old format IT instruments (cmwt < 0x200),
but I don't think these even exist in the wild.

creates an IT with the basic structure:
  IT header
  message
  patterns
  sample headers
  instruments
  sample data

todo:
 - add some compatibility-making code: fix envelopes that have no points, etc.
 - create some exceptions to replace assertion errors
"""

import sys
import struct

class ITenvelope_node:
  def __init__(self):
    self.y_val = 0
    self.tick = 0
  
  def __len__(self):
    return 3
  
class ITenvelope:
  def __init__(self):
    
    self.IsOn = False
    self.LoopOn = False
    self.SusloopOn = False
    
    self.LpB = 0
    self.LpE = 0
    self.SLB = 0
    self.SLE = 0
    
    # xxx convert this to not have 25 nodes always, and remove numNodePoints;
    # the self.Nodes list should contain the number of node points
    self.numNodePoints = 0
    self.Nodes = [ITenvelope_node() for i in xrange(25)] # create 25 nodes
  
  def extraFlags(self):
    return 0
    
  def write(self, outf):
    flags = 0
    flags = flags | ((self.IsOn) << 0)
    flags = flags | ((self.LoopOn) << 1)
    flags = flags | ((self.SusloopOn) << 2)
    flags = flags | self.extraFlags()
    
    outf.write(struct.pack('<BBBB', flags, self.numNodePoints, self.LpB, self.LpE))
    outf.write(struct.pack('<BB', self.SLB, self.SLE))
    
    for node in self.Nodes:
      outf.write(struct.pack('<bH', node.y_val, node.tick))
    
    outf.write('\0')
    
  def load(self, inf):
    (flags, self.numNodePoints, self.LpB, self.LpE, self.SLB,
     self.SLE) = struct.unpack('<BBBBBB', inf.read(6))
    
    self.setFlags(flags)
    
    self.Nodes = []
    
    for i in xrange(25):
      node = ITenvelope_node()
      self.Nodes.append(node)
      (node.y_val, node.tick) = struct.unpack('<bH', inf.read(3))
    inf.read(1)
    
  def setFlags(self, flags):
    self.IsOn = bool(flags & 0x01)
    self.LoopOn = bool(flags & 0x02)
    self.SusloopOn = bool(flags & 0x04)
    
  def __len__(self):
    return 82
  
  
class ITvol_envelope(ITenvelope):
  def __init__(self):
    ITenvelope.__init__(self)

class ITpan_envelope(ITenvelope):
  def __init__(self):
    ITenvelope.__init__(self)

class ITpitch_envelope(ITenvelope):
  def __init__(self):
    ITenvelope.__init__(self)
    self.IsFilter = False
  
  def extraFlags(self):
    if self.IsFilter:
      return 0x80
    else:
      return 0
  
  def setFlags(self, flags):
    ITenvelope.setFlags(self, flags)
    self.IsFilter = bool(flags & 0x80)

class ITinstrument:
  def __init__(self):
    self.Filename = ''
    self.NNA = 0
    self.DCT = 0
    self.DCA = 0
    self.FadeOut = 0
    self.PPS = 0
    self.PPC = 0x3c
    self.GbV = 128
    self.DfP = 128
    self.RV = 0
    self.RP = 0
    # TrkVers and NoS are ignored (used in instrument files only)
    self.InstName = ''
    self.IFC = 0
    self.IFR = 0
    self.MCh = 0
    self.MPr = 0
    self.MIDIBank = 0
    
    self.SampleTable = [[i, 0] for i in range(120)]
    
    self.volEnv = ITvol_envelope()
    self.panEnv = ITpan_envelope()
    self.pitchEnv = ITpitch_envelope()
  
  def write(self, outf):
    outf.write(struct.pack('<4s12s', 'IMPI', self.Filename))
    outf.write(struct.pack('<BBBB', 0, self.NNA, self.DCT, self.DCA))
    outf.write(struct.pack('<HBB', self.FadeOut, self.PPS, self.PPC))
    outf.write(struct.pack('<BBBB', self.GbV, self.DfP, self.RV, self.RP))
    outf.write(struct.pack('<HBB', 0xadde, 0xbe, 0xef)) # unused data
    outf.write(struct.pack('<26s', self.InstName[:25]+'\0'))
    outf.write(struct.pack('<BBBBH', self.IFC, self.IFR, self.MCh, self.MPr, self.MIDIBank))
    for smp in self.SampleTable:
      outf.write(struct.pack('<BB', smp[0], smp[1]))
    
    self.volEnv.write(outf)
    self.panEnv.write(outf)
    self.pitchEnv.write(outf)
    
    outf.write('FOOB')
  
  def load(self, inf):
    """inf must be seeked to position of instrument to be read"""
    (IMPI, self.Filename) = struct.unpack('<4s12s', inf.read(16))
    assert(IMPI == 'IMPI')
    
    (zero, self.NNA, self.DCT, self.DCA, self.FadeOut, self.PPS, self.PPC, 
     self.GbV, self.DfP, self.RV, self.RP, discard, discard,
     discard) = struct.unpack('<BBBBHBBBBBBHBB', inf.read(16))
    
    # seems some mods (saved by a bad schismtracker, maybe?)
    # don't have zero = 0x0
    #assert(zero == 0x0)
    
    self.InstName = inf.read(26).replace('\0', ' ')[:25]
    
    (self.IFC, self.IFR, self.MCh, self.MPr,
     self.MIDIBank) = struct.unpack('<BBBBH', inf.read(6))
    
    self.SampleTable = []
    for i in xrange(120):
      self.SampleTable.append(list(struct.unpack('<BB', inf.read(2))))
    
    self.volEnv = ITvol_envelope()
    self.panEnv = ITpan_envelope()
    self.pitchEnv = ITpitch_envelope()
    
    self.volEnv.load(inf)
    self.panEnv.load(inf)
    self.pitchEnv.load(inf)
    
    inf.read(4) # dummy read
    
    
  def __len__(self):
    return 554

class ITsample:
  def __init__(self):
    self.Filename = ''
    self.GvL = 64
    
    self.IsSample = False
    self.Is16bit = False
    self.IsStereo = False
    self.IsCompressed = False
    self.IsLooped = False
    self.IsSusLooped = False
    self.IsPingPongLoop = False
    self.IsPingPongSusLoop = False
    
    self.Vol = 64
    self.SampleName = ''
    self.Cvt = 0x01
    self.DfP = 0x00
    
    # length is determined by sample data
    # note, lengths and loop indices are in SAMPLES, not BYTES
    
    self.LoopBegin = 0
    self.LoopEnd = 0
    self.C5Speed = 8363
    self.SusLoopBegin = 0
    self.SusLoopEnd = 0
    self.ViS = 0
    self.ViD = 0
    self.ViT = 0
    self.ViR = 0
    
    self.SampleData = ''
  
  def sampleDataLen(self):
    divider = 1
    if self.Is16bit:
      divider = divider * 2
    if self.IsStereo:
      divider = divider * 2
      
    return len(self.SampleData) / divider
  
  def write(self, outf, sample_offset):
    if not self.IsSample:
      self.SampleData = ''
    
    flags = 0
    flags = flags | ((self.IsSample) << 0)
    flags = flags | ((self.Is16bit) << 1)
    flags = flags | ((self.IsStereo) << 2)
    flags = flags | ((self.IsCompressed) << 3)
    flags = flags | ((self.IsLooped) << 4)
    flags = flags | ((self.IsSusLooped) << 5)
    flags = flags | ((self.IsPingPongLoop) << 6)
    flags = flags | ((self.IsPingPongSusLoop) << 7)
    
    outf.write(struct.pack('<4s12s', 'IMPS', self.Filename))
    outf.write(struct.pack('<BBBB', 0, self.GvL, flags, self.Vol))
    outf.write(struct.pack('<26s', self.SampleName[:25]+'\0'))
    outf.write(struct.pack('<BB', self.Cvt, self.DfP))
    outf.write(struct.pack('<I', self.sampleDataLen()))
    outf.write(struct.pack('<III', self.LoopBegin, self.LoopEnd, self.C5Speed))
    outf.write(struct.pack('<II', self.SusLoopBegin, self.SusLoopEnd))
    outf.write(struct.pack('<I', sample_offset))
    outf.write(struct.pack('<BBBB', self.ViS, self.ViD, self.ViT, self.ViR))

  def load(self, inf):
    (IMPS, self.Filename) = struct.unpack('<4s12s', inf.read(16))
    assert(IMPS == 'IMPS')
    
    (zero, self.GvL, flags, self.Vol) = struct.unpack('<BBBB', inf.read(4))
    # seems some mods (saved by a bad schismtracker, maybe?)
    # don't have zero = 0x0
    #assert(zero == 0x0)
    
    self.IsSample = bool(flags & 0x01)
    self.Is16bit = bool(flags & 0x02)
    self.IsStereo = bool(flags & 0x04)
    self.IsCompressed = bool(flags & 0x08)
    self.IsLooped = bool(flags & 0x10)
    self.IsSusLooped = bool(flags & 0x20)
    self.IsPingPongLoop = bool(flags & 0x40)
    self.IsPingPongSusLoop = bool(flags & 0x80)
    
    self.SampleName = inf.read(26).replace('\0', ' ')[:25]
    
    (self.Cvt, self.DfP) = struct.unpack('<BB', inf.read(2))
    
    (length, self.LoopBegin, self.LoopEnd, self.C5Speed) = struct.unpack('<IIII', inf.read(16))
    (self.SusLoopBegin, self.SusLoopEnd, offs_sampledata, self.ViS,
     self.ViD, self.ViT, self.ViR) = struct.unpack('<IIIBBBB', inf.read(16))
    
    # load sample, if there is one
    if self.IsSample and length > 0:
      # first, find length in bytes (not samples!)
      mult = 1
      if self.Is16bit:
        mult = mult * 2
      if self.IsStereo:
        mult = mult * 2
      
      length = length * mult
      inf.seek(offs_sampledata)
      self.SampleData = inf.read(length)
      
  def __len__(self):
    return 80
  

class ITpattern:
  def __init__(self):
    self.rows = 64
    self.ptnData = ''
  
  def __len__(self):
    return len(self.ptnData) + 8
  
  def __eq__(self, other):
    return self.rows == other.rows and self.ptnData == other.ptnData
    
  def write(self, outf):
    outf.write(struct.pack('<HH4s', len(self.ptnData), self.rows, '\0'*4))
    outf.write(self.ptnData)
  
  def load(self, inf):
    """Load IT pattern data from inf.  inf should already be seeked to 
       the offset of the pattern to be loaded."""
    (ptnlen, self.rows, discard) = struct.unpack('<HH4s', inf.read(8))
    self.ptnData = inf.read(ptnlen)
    
class ITfile:
  Orderlist_offs = 192 # length of IT header before any dynamic data (order list)
  
  def __init__(self):
    self.SongName = 'gohoho'
    self.PHilight_minor = 4
    self.PHilight_major = 16
    
    # OrdNum, InsNum, SmpNum, PatNum are used only when loading files; 
    # the actual numbers will be stored as len(lists)
    
    self.Cwt_v = 0x0214
    self.Cmwt = 0x0214
    self.Flags = 0x000d
    self.Special = 0x0006
    self.GV = 128  # global vol
    self.MV = 48   # mixing vol
    self.IS = 6    # initial speed
    self.IT = 125  # initial tempo
    self.Sep = 128 # stereo separation
    self.PWD = 0x00
    
    # msglen is also collected by actual message length
    self.Message = ''
    
    self.ChannelPans = 64*[64]
    self.ChannelVols = 64*[64]
    
    self.Orders = []
    
    self.Instruments = []
    self.Samples = []
    self.Ptns = []

  def open(self, infilename):
    inf = file(infilename, "rb")
    
    buf = inf.read(30)
    (IMPM, self.SongName) = struct.unpack('<4s26s', buf)
    
    assert(IMPM == 'IMPM')
    
    self.SongName = self.SongName.split('\0')[0]
    
    buf = inf.read(34)
    (self.PHilight_minor, self.PHilight_major, n_ords, n_insts, n_samps,
     n_ptns, Cwt_v, Cmwt, self.Flags, self.Special, self.GV, self.MV,
     self.IS, self.IT, self.Sep, self.PWD, msglen, offs_msg, reserved) = struct.unpack(
     '<BBHHHHHHHHBBBBBBHII', buf)
    
    offs_ords = ITfile.Orderlist_offs
    offs_instoffs = offs_ords + n_ords
    offs_sampoffs = offs_instoffs + n_insts*4
    offs_ptnoffs = offs_sampoffs + n_samps*4
    
    
    assert(inf.tell() == 0x40)
    
    self.ChannelPans = []
    for i in xrange(64):
      self.ChannelPans.append(struct.unpack('<B', inf.read(1))[0])
    
    self.ChannelVols = []
    for i in xrange(64):
      self.ChannelVols.append(struct.unpack('<B', inf.read(1))[0])
    
    assert(inf.tell() == offs_ords)
    
    self.Orders = []
    for i in xrange(n_ords):
      self.Orders.append(struct.unpack('<B', inf.read(1))[0])
    
    assert(inf.tell() == offs_instoffs)
    
    offs_insts = []
    for i in xrange(n_insts):
      offs_insts.append(struct.unpack('<I', inf.read(4))[0])
    
    assert(inf.tell() == offs_sampoffs)
    
    offs_samps = []
    for i in xrange(n_samps):
      offs_samps.append(struct.unpack('<I', inf.read(4))[0])
    
    assert(inf.tell() == offs_ptnoffs)
    
    offs_ptns = []
    for i in xrange(n_ptns):
      offs_ptns.append(struct.unpack('<I', inf.read(4))[0])
    
    # load song message
    
    if (self.Special & 0x0001) and (msglen > 0):
      inf.seek(offs_msg)
      self.Message = inf.read(msglen).replace('\0', ' ').replace('\r', '\n')[:-1]
    else:
      self.Message = ''
    
    # load patterns
    
    self.Ptns = []
    
    for offs_ptn in offs_ptns:
      inf.seek(offs_ptn)
      
      ptn = ITpattern()
      ptn.load(inf)
      self.Ptns.append(ptn)
    
    # load instruments
    
    self.Instruments = []
    
    for offs_inst in offs_insts:
      inf.seek(offs_inst)
      
      inst = ITinstrument()
      try:
        inst.load(inf)
      except:
        # the instrument failed to load, but we'll pretend it didn't
        pass
      self.Instruments.append(inst)
    
    self.Samples = []
    
    for offs_samp in offs_samps:
      inf.seek(offs_samp)
      
      samp = ITsample()
      try:
        samp.load(inf)
      except:
        # the sample failed to load, but we'll pretend it didn't
        # we might need to do some cleanup...
        
        pass
      self.Samples.append(samp)
    
    inf.close()
    
  def write(self, outfilename):
    outf = file(outfilename, "wb")
    
    if (len(self.Message) > 0):
      self.Special = self.Special | 0x0001
      message = self.Message.replace('\n', '\r') + '\0'
    else:
      self.Special = self.Special & (~0x0001)
      message = ''
    
    
    instoffs_offs = ITfile.Orderlist_offs + len(self.Orders)
    sampoffs_offs = instoffs_offs + len(self.Instruments)*4
    ptnoffs_offs = sampoffs_offs + len(self.Samples)*4
    msg_offs = ptnoffs_offs + len(self.Ptns)*4
    ptn_offs = msg_offs + len(message)
    
    # pack patterns so we can predict total pattern data length, and
    # next offset
    (pattern_list, unique_ITpatterns) = self.pack_ptns()
    ptn_offsets = {} 
    offs = ptn_offs
    for x in pattern_list:
      if x not in ptn_offsets:
        # unknown pattern
        
        # store new pattern offset
        ptn_offsets[x] = offs
        
        offs = offs + len(unique_ITpatterns[x])
    
    
    #samp_offs = ptn_offs + sum([len(x) for x in self.Ptns])
    samp_offs = offs
    inst_offs = samp_offs + sum([len(x) for x in self.Samples])
    sampledata_offs = inst_offs + sum([len(x) for x in self.Instruments])
    
    # write header
    songname = self.SongName[:25].ljust(26, '\x00')
    
    outf.write(struct.pack('<4s26sBB', 'IMPM', songname, self.PHilight_minor, self.PHilight_major))
    outf.write(struct.pack('<HHHHHHHH', len(self.Orders), len(self.Instruments),
                           len(self.Samples), len(self.Ptns),
                           self.Cwt_v, self.Cmwt, self.Flags, self.Special))
    outf.write(struct.pack('<BBBBBBHII', self.GV, self.MV, self.IS, self.IT,
                           self.Sep, self.PWD, len(message), msg_offs, 0))
    for x in self.ChannelPans:
      if (x > 64):
        x = 64
      elif x < 0:
        x = 0
      outf.write(struct.pack('<B', x))
    
    for x in self.ChannelVols:
      if (x > 64):
        x = 64
      elif x < 0:
        x = 0
      outf.write(struct.pack('<B', x))
    
    assert(outf.tell() == ITfile.Orderlist_offs)
    
    for x in self.Orders:
      if (x > 199):
        if (x < 254):
          x = 199
        elif (x > 255):
          x = 255
      elif x < 0:
        x = 0
      outf.write(struct.pack('<B', x))
    
    assert(outf.tell() == instoffs_offs)
    
    offs = inst_offs
    for x in self.Instruments:
      outf.write(struct.pack('<I', offs))
      offs = offs + len(x)
      
    assert(outf.tell() == sampoffs_offs)
    
    offs = samp_offs
    for x in self.Samples:
      outf.write(struct.pack('<I', offs))
      offs = offs + len(x)
    
    assert(outf.tell() == ptnoffs_offs)
    
    # save patterns (packed)
    for x in pattern_list:
      print x
      outf.write(struct.pack('<I', ptn_offsets[x]))
    
    assert(outf.tell() == msg_offs)
    if message:
      outf.write(message)
    assert(outf.tell() == ptn_offs)
    
    for ptn in unique_ITpatterns:
      ptn.write(outf)
    assert(outf.tell() == samp_offs)
    
    # next_smpoffs is the actual offset of the sample data for each sample.
    # It's stored in the header, so writing the header needs to know it.
    
    next_smpoffs = sampledata_offs
    for samp in self.Samples:
      samp.write(outf, next_smpoffs)
      next_smpoffs = next_smpoffs + len(samp.SampleData)
    eof = next_smpoffs
    
    assert(outf.tell() == inst_offs)
    
    for inst in self.Instruments:
      inst.write(outf)
    assert(outf.tell() == sampledata_offs)
    
    for samp in self.Samples:
      outf.write(samp.SampleData)
    
    assert(outf.tell() == eof)
        
    outf.close()
    
  def pack_ptns(self):
    """Returns a tuple(pattern_list, unique_ITpatterns)""" 
    ptnlist = []
    ptns = []
    
    for ptn in self.Ptns:
      if ptn in ptns:
        # already in pattern set, create a reference only
        ptnlist.append(ptns.index(ptn))
      else:
        # doesn't exist in pattern set, add it and create a reference to it
        ptns.append(ptn)
        ptnlist.append(ptns.index(ptn))
    
    return (ptnlist, ptns) 

def process():
  itf = ITfile()
  
  assert(len(sys.argv) == 2)
  
  itf.open(sys.argv[1])
  
  #for samp in itf.Samples:
  #  print samp.SampleName.decode('cp437')
  
  itf.write('new.it')
  
  # Create a mostly-empty .IT file
  #itf = ITfile()
  #itf.Orders.append(0)
  #itf.Instruments.append(ITinstrument())
  #itf.Instruments[0].Filename = 'fallow'
  #itf.Instruments[0].InstName = 'aaaaaa!!'
  #
  #itf.Samples.append(ITsample())
  #itf.Samples[0].Filename = 'HUUU'
  #itf.Samples[0].SampleName = 'Bubuuu!!!'
  #
  #itf.Message = 'ahahaha!'
  #itf.write('bloo.it')

if __name__ == '__main__':
  process()
