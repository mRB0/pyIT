#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""\

wxPython app for IT file (en-masse) metadata editing

(c) 2008 mike burke / mrb / mrburke@gmail.com

todo:
 - add checked commit progress indicator
 
"""

#
# i wish the checklistbox would let me display tri-state checkboxes :(
# instead, you can't tell if a directory is fully selected or not
#

from __future__ import division

import os, os.path
import random
 
import wx
import wx.grid

import traceback

import pyIT

mod_encoding = 'cp437'

old_wx_message = """\
It seems that you are using a version of wxWidgets
that does not have wx.TextCtrl.ChangeValue.

This means any file with a song message (and maybe
even without) will be recorded as modified upon
open, even if you don't change it.  Of course,
nothing will be saved unless you actually "Commit".

To fix this issue, upgrade to wx2.8 or something mmkay\
"""

# begin wxGlade: extracode
# end wxGlade
 
class CommentGrid(wx.grid.Grid):
    def __init__(self, *args, **kwds):
        wx.grid.Grid.__init__(self, *args, **kwds)
        
        self.__set_properties()
        self.__do_layout()
        
        #self.Bind(wx.grid.EVT_GRID_ROW_SIZE, self.onGridRowResize, self)
        
    def __set_properties(self):
        self.CreateGrid(99, 1)
        #self.EnableDragColSize(0)
        #self.EnableDragRowSize(0)
        
        # find out width of font so we know how to set proper row label width
 
        dc = wx.ScreenDC()
        fontwidth = 0
        dc.SetFont(self.GetLabelFont())
 
        for i in xrange(99):
            fw = dc.GetTextExtent("99m")[0] # adds a half-m space to either side
            if fw > fontwidth:
                fontwidth = fw
            self.SetRowLabelValue(i, unicode(i+1))
 
        self.SetRowLabelSize(fontwidth)
        self.SetColLabelSize(0)
 
        self.SetDefaultCellFont(wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT))
        
        dc.SetFont(wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT))
        fontwidth = dc.GetTextExtent(26*"m")[0]
        del dc
 
        
        self.SetColMinimalWidth(0, fontwidth)
        self.SetColSize(0, fontwidth)
        self.EnableDragRowSize(False)
        
        self.ForceRefresh()
        
    def __do_layout(self):
        pass
    
    #def onGridRowResize(self, evt):
    #    print "resize"
    #    evt.Skip()
        

class ListEditorPane(wx.Panel):
    def __init__(self, *args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)
        
        self.splitter = wx.SplitterWindow(self, -1, style=wx.SP_3D|wx.SP_BORDER)
 
        self.bottomPane = wx.Panel(self.splitter, -1)
        self.topPane = wx.Panel(self.splitter, -1)
 
        self.lblFilename = wx.StaticText(self.topPane, -1, "File:")
        self.txtFilename = wx.TextCtrl(self.topPane, -1, "", style=wx.TE_READONLY|wx.NO_BORDER)
        self.gridFile = CommentGrid(self.topPane, -1, size=(1, 1))
        
        
        self.btnCommitFile = wx.Button(self.topPane, -1, "Commit")
        self.btnRevertFile = wx.Button(self.topPane, -1, "Revert")
        self.btnCopyFile = wx.Button(self.topPane, -1, "Copy")
        self.btnPasteFile = wx.Button(self.topPane, -1, "Paste")
        
        self.lblChecked = wx.StaticText(self.bottomPane, -1, "Checkmarked files")
        self.gridChecked = CommentGrid(self.bottomPane, -1, size=(1, 1))
        self.btnCommitChecked = wx.Button(self.bottomPane, -1, "Commit")
        self.btnRevertChecked = wx.Button(self.bottomPane, -1, "Revert")
        self.btnCopyChecked = wx.Button(self.bottomPane, -1, "Copy")
        self.btnPasteChecked = wx.Button(self.bottomPane, -1, "Paste")

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.onCopyFile, self.btnCopyFile)
        self.Bind(wx.EVT_BUTTON, self.onPasteFile, self.btnPasteFile)
        self.Bind(wx.EVT_BUTTON, self.onCopyChecked, self.btnCopyChecked)
        self.Bind(wx.EVT_BUTTON, self.onPasteChecked, self.btnPasteChecked)
        
    
    def __set_properties(self):
        self.txtFilename.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))
        self.txtFilename.SetValue("(none)")
    
    def __do_layout(self):
        outerSizer = wx.BoxSizer(wx.VERTICAL)
        
        # top half (edit file)
        
        szrFilenameGrid = wx.BoxSizer(wx.VERTICAL)
        szrTopGrid = wx.FlexGridSizer(2, 2, 4, 4)
        szrCopyPaste = wx.BoxSizer(wx.HORIZONTAL)
        szrCommitRevert = wx.BoxSizer(wx.VERTICAL)
        szrFilenameLabel = wx.BoxSizer(wx.HORIZONTAL)
        szrFilenameLabel.Add(self.lblFilename, 0, wx.ALL, 4)
        szrFilenameLabel.Add(self.txtFilename, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 4)
        szrFilenameGrid.Add(szrFilenameLabel, 0, wx.EXPAND, 0)
        szrTopGrid.Add(self.gridFile, 1, wx.EXPAND, 0)
        szrCommitRevert.Add(self.btnCommitFile, 0, wx.ALL, 2)
        szrCommitRevert.Add(self.btnRevertFile, 0, wx.ALL, 2)
        szrTopGrid.Add(szrCommitRevert, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        szrCopyPaste.Add(self.btnCopyFile, 0, wx.ALL, 2)
        szrCopyPaste.Add(self.btnPasteFile, 0, wx.ALL, 2)
        szrTopGrid.Add(szrCopyPaste, 1, wx.ALIGN_CENTER_HORIZONTAL, 0)
        szrTopGrid.Add((0, 0), 0, 0, 0)
        szrFilenameGrid.Add(szrTopGrid, 1, wx.EXPAND, 0)
        self.topPane.SetSizer(szrFilenameGrid)
        
        szrTopGrid.AddGrowableCol(0)
        szrTopGrid.AddGrowableRow(0)

        # bottom half (edit checked)
        
        szrBottomGrid = wx.FlexGridSizer(3, 2, 4, 4)
        szrBottomGrid.Add(self.lblChecked, 0, wx.ALL, 4)
        szrBottomGrid.Add((0, 0), 0, 0, 0)
        
        szrBottomGrid.Add(self.gridChecked, 1, wx.EXPAND, 0)
        
        szrCopyPaste = wx.BoxSizer(wx.HORIZONTAL)
        szrCommitRevert = wx.BoxSizer(wx.VERTICAL)
        
        szrCommitRevert.Add(self.btnCommitChecked, 0, wx.ALL, 2)
        szrCommitRevert.Add(self.btnRevertChecked, 0, wx.ALL, 2)
        
        szrBottomGrid.Add(szrCommitRevert, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        
        szrCopyPaste.Add(self.btnCopyChecked, 0, wx.ALL, 2)
        szrCopyPaste.Add(self.btnPasteChecked, 0, wx.ALL, 2)
        
        szrBottomGrid.Add(szrCopyPaste, 1, wx.ALIGN_CENTER_HORIZONTAL, 0)
        
        szrBottomGrid.Add((0, 0), 0, 0, 0)
        
        #szrFilenameGrid.Add(szrBottomGrid, 1, wx.EXPAND, 0)
        self.bottomPane.SetSizer(szrBottomGrid)
        
        szrBottomGrid.AddGrowableCol(0)
        szrBottomGrid.AddGrowableRow(1)
        
        # ok
        
        self.splitter.SplitHorizontally(self.topPane, self.bottomPane)
        outerSizer.Add(self.splitter, 1, wx.EXPAND, 0)
 
        #outerSizer.Add(self.topPane, 0, wx.EXPAND, 0)
        #outerSizer.Add(self.bottomPane, 0, wx.EXPAND, 0)
        self.SetSizer(outerSizer)
 
        #self.sampleTopPane.SetMinSize((0, 50))
        #self.sampleTopPane.SetSize((100, 100))
        #self.sampleBottomPane.SetSize((100, 100))
        #self.sampleBottomPane.SetMinSize((0, 30))
        #self.Layout()
        #print self.GetSize()
        self.splitter.SetSashPosition(200)#self.GetSize()[0] / 2)
    
    def onCopyFile(self, event):
        self.do_copy(self.gridFile)
    
    def onCopyChecked(self, event):
        self.do_copy(self.gridChecked)
    
    def do_copy(self, grid):
        rows = []
        
        sel_top_lefts = grid.GetSelectionBlockTopLeft()
        sel_btm_rights = grid.GetSelectionBlockBottomRight()
         
        for i in range(len(sel_top_lefts)):
            for idx in range(sel_top_lefts[i][0],
                             sel_btm_rights[i][0]+1):
                rows.append(grid.GetCellValue(idx, 0))
        
        clip = wx.TheClipboard
        if not clip.Open():
            return
        do = wx.TextDataObject()
        do.SetText(u'\r\n'.join(rows))
        clip.SetData(do)
        clip.Close()

    def onPasteFile(self, event):
        self.do_paste(self.gridFile)

    def onPasteChecked(self, event):
        self.do_paste(self.gridChecked)
        
    def do_paste(self, grid):
        clip = wx.TheClipboard
        if not clip.Open():
            return
        do = wx.TextDataObject()
        rc = clip.GetData(do)
        clip.Close()
        #print do.GetText()
        
        idx = grid.GetGridCursorRow()
        
        cliptext = do.GetText()
        
        cliptext = cliptext.replace(u"\r\n", u"\n")
        cliptext = cliptext.replace(u"\r", u"\n")
        
        for line in cliptext.rstrip(u'\n').split(u'\n'):
            if idx >= 99:
                break
            grid.SetCellValue(idx, 0, line.rstrip())
            # post cell-change event
            evt = wx.grid.GridEvent(grid.GetId(), wx.grid.wxEVT_GRID_CELL_CHANGE, grid, idx, grid.GetGridCursorCol())
            grid.GetEventHandler().ProcessEvent(evt)
            
            idx = idx + 1
            
 
class MessageEditorPane(wx.Panel):
    def __init__(self, *args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)
        
        self.splitter = wx.SplitterWindow(self, -1, style=wx.SP_3D|wx.SP_BORDER)
 
        self.bottomPane = wx.Panel(self.splitter, -1)
        self.topPane = wx.Panel(self.splitter, -1)
 
        self.lblFilename = wx.StaticText(self.topPane, -1, u"File:")
        self.txtFilename = wx.TextCtrl(self.topPane, -1, u"", style=wx.TE_READONLY|wx.NO_BORDER)
        self.editorFile = wx.TextCtrl(self.topPane, -1, u'', style=wx.TE_MULTILINE)
        
        
        self.btnCommitFile = wx.Button(self.topPane, -1, "Commit")
        self.btnRevertFile = wx.Button(self.topPane, -1, "Revert")
        #self.btnCopyFile = wx.Button(self.topPane, -1, "Copy")
        #self.btnPasteFile = wx.Button(self.topPane, -1, "Paste")
        
        self.lblChecked = wx.StaticText(self.bottomPane, -1, "Checkmarked files")
        self.editorChecked = wx.TextCtrl(self.bottomPane, -1, u'', style=wx.TE_MULTILINE)
        self.btnCommitChecked = wx.Button(self.bottomPane, -1, "Commit")
        self.btnRevertChecked = wx.Button(self.bottomPane, -1, "Revert")
        #self.btnCopyChecked = wx.Button(self.bottomPane, -1, "Copy")
        #self.btnPasteChecked = wx.Button(self.bottomPane, -1, "Paste")
        
        self.__set_properties()
        self.__do_layout()
        
        
    
    def __set_properties(self):
        self.txtFilename.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))
        self.txtFilename.SetValue("(none)")
    
    def __do_layout(self):
        outerSizer = wx.BoxSizer(wx.VERTICAL)
        
        # top half (edit file)
        
        szrFilenameGrid = wx.BoxSizer(wx.VERTICAL)
        szrTopGrid = wx.FlexGridSizer(1, 2, 4, 4)
        #szrCopyPaste = wx.BoxSizer(wx.HORIZONTAL)
        szrCommitRevert = wx.BoxSizer(wx.VERTICAL)
        szrFilenameLabel = wx.BoxSizer(wx.HORIZONTAL)
        szrFilenameLabel.Add(self.lblFilename, 0, wx.ALL, 4)
        szrFilenameLabel.Add(self.txtFilename, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 4)
        szrFilenameGrid.Add(szrFilenameLabel, 0, wx.EXPAND, 0)
        szrTopGrid.Add(self.editorFile, 1, wx.EXPAND, 0)
        szrCommitRevert.Add(self.btnCommitFile, 0, wx.ALL, 2)
        szrCommitRevert.Add(self.btnRevertFile, 0, wx.ALL, 2)
        szrTopGrid.Add(szrCommitRevert, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        #szrCopyPaste.Add(self.btnCopyFile, 0, wx.ALL, 2)
        #szrCopyPaste.Add(self.btnPasteFile, 0, wx.ALL, 2)
        #szrTopGrid.Add(szrCopyPaste, 1, wx.ALIGN_CENTER_HORIZONTAL, 0)
        #szrTopGrid.Add((0, 0), 0, 0, 0)
        szrFilenameGrid.Add(szrTopGrid, 1, wx.EXPAND, 0)
        self.topPane.SetSizer(szrFilenameGrid)
        
        szrTopGrid.AddGrowableCol(0)
        szrTopGrid.AddGrowableRow(0)

        # bottom half (edit checked)
        
        szrBottomGrid = wx.FlexGridSizer(2, 2, 4, 4)
        szrBottomGrid.Add(self.lblChecked, 0, wx.ALL, 4)
        szrBottomGrid.Add((0, 0), 0, 0, 0)
        
        szrBottomGrid.Add(self.editorChecked, 1, wx.EXPAND, 0)
        
        #szrCopyPaste = wx.BoxSizer(wx.HORIZONTAL)
        szrCommitRevert = wx.BoxSizer(wx.VERTICAL)
        
        szrCommitRevert.Add(self.btnCommitChecked, 0, wx.ALL, 2)
        szrCommitRevert.Add(self.btnRevertChecked, 0, wx.ALL, 2)
        
        szrBottomGrid.Add(szrCommitRevert, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        
        #szrCopyPaste.Add(self.btnCopyChecked, 0, wx.ALL, 2)
        #szrCopyPaste.Add(self.btnPasteChecked, 0, wx.ALL, 2)
        
        #szrBottomGrid.Add(szrCopyPaste, 1, wx.ALIGN_CENTER_HORIZONTAL, 0)
        
        #szrBottomGrid.Add((0, 0), 0, 0, 0)
        
        #szrFilenameGrid.Add(szrBottomGrid, 1, wx.EXPAND, 0)
        self.bottomPane.SetSizer(szrBottomGrid)
        
        szrBottomGrid.AddGrowableCol(0)
        szrBottomGrid.AddGrowableRow(1)
        
        # ok
        
        self.splitter.SplitHorizontally(self.topPane, self.bottomPane)
        outerSizer.Add(self.splitter, 1, wx.EXPAND, 0)
 
        #outerSizer.Add(self.topPane, 0, wx.EXPAND, 0)
        #outerSizer.Add(self.bottomPane, 0, wx.EXPAND, 0)
        self.SetSizer(outerSizer)
 
        #self.sampleTopPane.SetMinSize((0, 50))
        #self.sampleTopPane.SetSize((100, 100))
        #self.sampleBottomPane.SetSize((100, 100))
        #self.sampleBottomPane.SetMinSize((0, 30))
        #self.Layout()
        #print self.GetSize()
        self.splitter.SetSashPosition(200)#self.GetSize()[0] / 2)
 
 
class Notebook(wx.Notebook):
    def __init__(self, *args, **kwds):
        kwds["style"] = 0
        wx.Notebook.__init__(self, *args, **kwds)
 
        self.samplePane = ListEditorPane(self, -1)

        self.instrumentPane = ListEditorPane(self, -1)
        #self.footext = wx.StaticText(self.instrumentPane, -1, "Foo")

        self.messagePane = MessageEditorPane(self, -1)
 
        self.__set_properties()
        self.__do_layout()
 
        self.Bind(wx.EVT_SIZE, self.onResize, self)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.onSashPosChange, self.samplePane.splitter) 
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.onSashPosChange, self.instrumentPane.splitter) 
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.onSashPosChange, self.messagePane.splitter) 
        
    def __set_properties(self):
        self.AddPage(self.samplePane, "Samples")
        self.AddPage(self.instrumentPane, "Instruments")
        self.AddPage(self.messagePane, "Message")
 
 
    def __do_layout(self):
        pass
        # fill other panes
        #bs = wx.BoxSizer(wx.VERTICAL)
        #bs.Add(self.footext)
        #self.instrumentPane.SetSizer(bs)
 
    def onSashPosChange(self, event):
        #print "sash pos changed on",
        new_pos = event.GetEventObject().GetSashPosition()
        self.samplePane.splitter.SetSashPosition(new_pos) 
        self.instrumentPane.splitter.SetSashPosition(new_pos) 
        self.messagePane.splitter.SetSashPosition(new_pos) 
        
    def onResize(self, event):
        #print "resize event"
        #print "sash =", self.samplePane.splitter.GetSashPosition()
        #print "size =", self.GetSize()
        #print "event size =", event.GetSize()
        
        try:
          self.oldSize
        except:
          self.oldSize = event.GetSize()
          #print "no old size"
          return
        
        #print self.oldSize
        ratio = self.samplePane.splitter.GetSashPosition() / self.oldSize[1]
        
        #print "ratio =", ratio
        new_sash_pos = ratio * event.GetSize()[1]
        self.samplePane.splitter.SetSashPosition(new_sash_pos)
        self.instrumentPane.splitter.SetSashPosition(new_sash_pos)
        self.messagePane.splitter.SetSashPosition(new_sash_pos)
        
        self.oldSize = event.GetSize()
        
        event.Skip()
        
# end of class Notebook
 
 
class EditFrame(wx.Frame):
    dir_choose_messages = (
        u"Please choose a directory.",
        u"WHERE.",
        u"WHERE. TELL ME NOW.",
        u"Pick one, already.",
        u"The directory should have mods in it.  Just sayin'.",
        u"Gimme a dingle",
        u"brb"
    )
    
    def __init__(self, *args, **kwds):
        # begin wxGlade: EditFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.splitItUp = wx.SplitterWindow(self, -1, style=wx.SP_3D|wx.SP_BORDER)
        self.editPane = wx.Panel(self.splitItUp, -1)
        self.filePane = wx.Panel(self.splitItUp, -1)
        self.chDirChooser = wx.Choice(self.filePane, -1, choices=[])
        self.lbFileList = wx.CheckListBox(self.filePane, -1, choices=[])
        self.cbSelectAll = wx.CheckBox(self.filePane, -1, "Select all")
        self.nbEdits = Notebook(self.editPane, -1)
        
        self.__set_properties()
        self.__do_layout()
        # end wxGlade
        
        #self.directories = [u'C:\\Users\\Mike\\Documents\\mods']
        self.directories = []
        self.checked_files = []
        self.modified_files = {}
        
        self.opened = None
        
        # 0 is always the current dir !!!! because it
        # gets moved to the top!!!
        # self.directory_idx = 0   
        
        self.Bind(wx.EVT_CHECKLISTBOX, self.onListCheck, self.lbFileList)
        self.Bind(wx.EVT_LISTBOX, self.onListSelect, self.lbFileList)
        self.Bind(wx.EVT_CHOICE, self.onDirChoose, self.chDirChooser)
        self.Bind(wx.EVT_CHECKBOX, self.onSelectAll, self.cbSelectAll)
        
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.onSampleChange, self.nbEdits.samplePane.gridFile)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.onInstChange, self.nbEdits.instrumentPane.gridFile)
        self.Bind(wx.EVT_TEXT, self.onMessageChange, self.nbEdits.messagePane.editorFile)
        
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.onSampleCheckedChange, self.nbEdits.samplePane.gridChecked)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.onInstCheckedChange, self.nbEdits.instrumentPane.gridChecked)
        self.Bind(wx.EVT_TEXT, self.onMessageCheckedChange, self.nbEdits.messagePane.editorChecked)
        
        self.Bind(wx.EVT_BUTTON, self.onCommitFile, self.nbEdits.samplePane.btnCommitFile)
        self.Bind(wx.EVT_BUTTON, self.onRevertFile, self.nbEdits.samplePane.btnRevertFile)
        self.Bind(wx.EVT_BUTTON, self.onCommitFile, self.nbEdits.instrumentPane.btnCommitFile)
        self.Bind(wx.EVT_BUTTON, self.onRevertFile, self.nbEdits.instrumentPane.btnRevertFile)
        self.Bind(wx.EVT_BUTTON, self.onCommitFile, self.nbEdits.messagePane.btnCommitFile)
        self.Bind(wx.EVT_BUTTON, self.onRevertFile, self.nbEdits.messagePane.btnRevertFile)
        
        self.Bind(wx.EVT_BUTTON, self.onCommitChecked, self.nbEdits.samplePane.btnCommitChecked)
        self.Bind(wx.EVT_BUTTON, self.onRevertChecked, self.nbEdits.samplePane.btnRevertChecked)
        self.Bind(wx.EVT_BUTTON, self.onCommitChecked, self.nbEdits.instrumentPane.btnCommitChecked)
        self.Bind(wx.EVT_BUTTON, self.onRevertChecked, self.nbEdits.instrumentPane.btnRevertChecked)
        self.Bind(wx.EVT_BUTTON, self.onCommitChecked, self.nbEdits.messagePane.btnCommitChecked)
        self.Bind(wx.EVT_BUTTON, self.onRevertChecked, self.nbEdits.messagePane.btnRevertChecked)
        
        self.change_dir(os.getcwd())
        self.updateDirChooser()
        
        try:
            wx.TextCtrl.ChangeValue
        except AttributeError:
            wx.MessageDialog(self, old_wx_message, "wx < 2.7.1", style=wx.ICON_INFORMATION|wx.OK).ShowModal()

    def __set_properties(self):
        # begin wxGlade: EditFrame.__set_properties
        self.SetTitle("bitesy bitles")
        # end wxGlade
 
    def __do_layout(self):
        # begin wxGlade: EditFrame.__do_layout
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        editSizer = wx.BoxSizer(wx.VERTICAL)
        leftPanelSizer = wx.BoxSizer(wx.VERTICAL)
        leftPanelSizer.Add(self.chDirChooser, 0, wx.EXPAND, 0)
        leftPanelSizer.Add(self.lbFileList, 1, wx.EXPAND, 0)
        leftPanelSizer.Add(self.cbSelectAll, 0, 0, 0)
        self.filePane.SetSizer(leftPanelSizer)
        editSizer.Add(self.nbEdits, 1, wx.EXPAND, 0)
        self.editPane.SetSizer(editSizer)
        self.splitItUp.SplitVertically(self.filePane, self.editPane)
        mainSizer.Add(self.splitItUp, 1, wx.EXPAND, 0)
 
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        self.Layout()
        # end wxGlade
        self.SetSize((600, 500))
        self.splitItUp.SetSashPosition(200)
        
        #print self.nbEdits.GetSize()
        #print "*** setting sash position and size"
        self.nbEdits.samplePane.splitter.SetSashPosition(self.nbEdits.GetSize()[1]/2)
        self.nbEdits.instrumentPane.splitter.SetSashPosition(self.nbEdits.GetSize()[1]/2)
        self.nbEdits.messagePane.splitter.SetSashPosition(self.nbEdits.GetSize()[1]/2)
        self.nbEdits.oldSize = self.nbEdits.GetSize()
        #print self.nbEdits.sampleSplitter.GetSashPosition()
    
    def change_dir(self, new_dir):
        new_dir = os.path.join(new_dir, u'')
        os.chdir(new_dir)
        if new_dir in self.directories:
            old_idx = self.directories.index(new_dir)
            del self.directories[old_idx]
        self.directories.insert(0, new_dir)
        if len(self.directories) > 6: # XXX maximum number of entries?
            self.directories.pop()
        
        self.updateDirChooser()
    
    def onDirChoose(self, event):
        new_idx = self.chDirChooser.GetSelection()
        #print "Selected", new_idx
        
        if new_idx == len(self.directories): # chose "Browse"
            dd = wx.DirDialog(self, self.dir_choose_messages[random.randrange(0, len(self.dir_choose_messages))], os.getcwd())
            if (dd.ShowModal() == wx.ID_OK):
                # user selected a new dir
                self.change_dir(dd.GetPath())
            else: # cancelled choice
                self.chDirChooser.SetSelection(0)
        else: # chose existing entry, bring it to top
            new_dir = self.directories[new_idx]
            del self.directories[new_idx]
            self.directories.insert(0, new_dir)
            self.updateDirChooser()
        
            
        
    def updateDirChooser(self):
        # I don't like to display trailing backslashes (trailing slashes
        # are ok but i need a general-case solution)
        
        self.chDirChooser.Clear()
        for item in [os.path.dirname(where) for where in self.directories]:
            self.chDirChooser.Append(item)
        self.chDirChooser.SetSelection(0)
        
        self.chDirChooser.Append("Browse...")
        
        self.loadDir()
    
    def get_filelist(self, where):
        filelist = os.listdir(where)
        dirs = [os.path.join(d, u'') for d in filelist if os.path.isdir(os.path.join(where, d))]
        dirs.sort()
        
        r_filelist = [f for f in filelist if f.upper().endswith(u'.IT')]
        r_filelist.sort()
        r_filelist = dirs + r_filelist
        return r_filelist
    
    def loadDir(self):
        self.lbFileList.Clear()
        
        all_checked = True
        
        if self.directories:
            os.chdir(self.directories[0])
            self.filelist = self.get_filelist(self.directories[0])
            
            i = 0
            for filename in self.filelist:
                self.lbFileList.Append(filename)
                pathspec = os.path.join(os.getcwd(), filename)
                
                # add check to subdir
                if os.path.isdir(pathspec):
                    if [x for x in self.checked_files if x.startswith(pathspec)]:
                        self.lbFileList.Check(i)
                    else:
                        all_checked = False
                else: # add check to file
                    if pathspec in self.checked_files:
                        self.lbFileList.Check(i)
                    else:
                        all_checked = False

                i = i + 1
            
            if all_checked and self.filelist:
                self.cbSelectAll.SetValue(True)
            else:
                self.cbSelectAll.SetValue(False)
    
    def onListCheck(self, event):
        target = event.GetSelection()
        checked = self.lbFileList.IsChecked(target)
        filespec = os.path.join(os.getcwd(), self.lbFileList.GetString(target))
        self.setChecked(filespec, checked)
        
        ## debug!
        #print u"setChecked result:"
        #for f in self.checked_files:
        #    print f

    def onSelectAll(self, event):
        self.setChecked(os.path.join(os.getcwd(), ''), self.cbSelectAll.IsChecked())
        self.loadDir()
    
    def setChecked(self, filespec, checked):
        # check/uncheck subdirectories
        if os.path.isdir(filespec):
            filelist = self.get_filelist(filespec)
            for sub in filelist:
                self.setChecked(os.path.join(filespec, sub), checked)
        
        else: # check/uncheck files
            if checked and filespec not in self.checked_files:
                self.checked_files.append(filespec)
            elif not checked and filespec in self.checked_files:
                self.checked_files.remove(filespec)
        
    def onListSelect(self, event):
        
        filename = self.filelist[self.lbFileList.GetSelection()]
        filespec = os.path.join(self.directories[0], filename)
        
        self.open_it(filespec)
        
    def open_it(self, filespec):
        if os.path.isdir(filespec): # don't load directories
            self.change_dir(filespec)
        else:
            #print "loading", filespec
            if filespec in self.modified_files:
                #print "using opened file"
                self.opened = {'filespec': filespec, 'data': self.modified_files[filespec]}
                itf = self.opened['data']
                self.nbEdits.samplePane.txtFilename.SetValue(filespec + u' *')
                self.nbEdits.instrumentPane.txtFilename.SetValue(filespec + u' *')
                self.nbEdits.messagePane.txtFilename.SetValue(filespec + u' *')
            else:
                itf = pyIT.ITfile()
                self.opened = {"filespec": filespec, "data": itf}
                itf.open(filespec)
                self.nbEdits.samplePane.txtFilename.SetValue(filespec)
                self.nbEdits.instrumentPane.txtFilename.SetValue(filespec)
                self.nbEdits.messagePane.txtFilename.SetValue(filespec)
            
            # load samples
            grid = self.nbEdits.samplePane.gridFile
            grid.ClearGrid()
            
            i = 0
            for sample in itf.Samples:
                if i == 99:
                    wx.MessageDialog(self, 
                        u"""\
OK, so, the IT format allows >99 samples,
but this program only supports 99.
This particular file has more than that.
I'll only load 99.  You won't lose the
rest, but I won't let you edit them either.\
""",
                        u"Can't we just get along", style=wx.ICON_ERROR|wx.OK).ShowModal()
                grid.SetCellValue(i, 0, sample.SampleName.decode(mod_encoding, "replace").rstrip(u' '))
                i = i + 1
    
            # load instruments
            grid = self.nbEdits.instrumentPane.gridFile
            grid.ClearGrid()
            i = 0
            for instrument in itf.Instruments:
                if i == 99:
                    wx.MessageDialog(self, 
                        u"""\
OK, so, the IT format allows >99 instruments,
but this program only supports 99.
This particular file has more than that.
I'll only load 99.  You won't lose the
rest, but you can't edit them either.\
""",
                        u"You're asking too much", style=wx.ICON_ERROR|wx.OK).ShowModal()
                    break
                grid.SetCellValue(i, 0, instrument.InstName.decode(mod_encoding, "replace").rstrip(u' '))
                i = i + 1
            
            # load message
            try:
                self.nbEdits.messagePane.editorFile.ChangeValue(itf.Message.decode(mod_encoding, "replace"))
            except AttributeError:
                # workaround for wx pre-2.7.1 (deprecated method)
                self.nbEdits.messagePane.editorFile.SetValue(itf.Message.decode(mod_encoding, "replace"))
    
    def set_modified(self, filespec, data):
        if not filespec in self.modified_files:
            self.nbEdits.samplePane.txtFilename.SetValue(filespec + u' *')
            self.nbEdits.instrumentPane.txtFilename.SetValue(filespec + u' *')
            self.nbEdits.messagePane.txtFilename.SetValue(filespec + u' *')
            self.modified_files[filespec] = data
        
        # xxx dir list doesn't show modification info yet
        #self.updateDirChooser()
    
    def onSampleCheckedChange(self, event):
        grid = self.nbEdits.samplePane.gridChecked
        idx = event.GetRow()
        
        # perform transcoding to ensure that files will save properly 
        name = grid.GetCellValue(idx, 0)[:25].encode(mod_encoding, "replace")
        grid.SetCellValue(idx, 0, name.decode(mod_encoding, "replace"))
        
    def onInstCheckedChange(self, event):
        grid = self.nbEdits.instrumentPane.gridChecked
        idx = event.GetRow()
        
        # perform transcoding to ensure that files will save properly 
        name = grid.GetCellValue(idx, 0)[:25].encode(mod_encoding, "replace")
        grid.SetCellValue(idx, 0, name.decode(mod_encoding, "replace"))
        
    def onMessageCheckedChange(self, event):
        if not self.nbEdits.messagePane.editorChecked.IsModified():
            # workaround for wx pre-2.7.1 (deprecated SetValue method)
            # xxx workaround doesn't work :(
            event.Skip()
        
        #print "checked message change"
        event.Skip()
        
    def onMessageChange(self, event):
        if not self.nbEdits.messagePane.editorFile.IsModified():
            # workaround for wx pre-2.7.1 (deprecated SetValue method)
            # xxx workaround doesn't work :(
            event.Skip()
        
        itf = self.opened['data']
        self.set_modified(self.opened['filespec'], itf)
        
        itf.Message = self.nbEdits.messagePane.editorFile.GetValue()[:7999].encode(mod_encoding, "replace")
        event.Skip()
        
    def onSampleChange(self, event):
        #print "sample", event.GetRow(), "changed"
        self.set_modified(self.opened['filespec'], self.opened['data'])
        
        grid = self.nbEdits.samplePane.gridFile
        
        samp_idx = event.GetRow()
        
        itf = self.opened['data']
        
        if not (samp_idx < len(itf.Samples)): # need to add empty samples
            n_new_samples = 1 + samp_idx - len(itf.Samples)
            for i in xrange(n_new_samples):
                itf.Samples.append(pyIT.ITsample())
        
        itf.Samples[samp_idx].SampleName = grid.GetCellValue(samp_idx, 0)[:25].encode(mod_encoding, "replace")
        grid.SetCellValue(samp_idx, 0, itf.Samples[samp_idx].SampleName.decode(mod_encoding, "replace"))
        
        
        #for samp in self.opened['data'].Samples:
        #    print samp.SampleName
         
        event.Skip()

    def onInstChange(self, event):
        #print "sample", event.GetRow(), "changed"
        self.set_modified(self.opened['filespec'], self.opened['data'])
        
        grid = self.nbEdits.instrumentPane.gridFile
        
        inst_idx = event.GetRow()
        
        itf = self.opened['data']
        
        if not (inst_idx < len(itf.Instruments)): # need to add empty samples
            n_new_insts = 1 + inst_idx - len(itf.Instruments)
            for i in xrange(n_new_insts):
                itf.Instruments.append(pyIT.ITinstrument())
        
        itf.Instruments[inst_idx].InstName = grid.GetCellValue(inst_idx, 0)[:25].encode(mod_encoding, "replace")
        grid.SetCellValue(inst_idx, 0, itf.Instruments[inst_idx].InstName.decode(mod_encoding, "replace"))
        
        event.Skip()
    
    def onCommitChecked(self, event):
        # load each checked file and... 
        
        errors = u''
        
        commitlist = list(self.checked_files)
        for filespec in commitlist:
            try:
                if filespec in self.modified_files:
                    print "can't commit", filespec, "as it has current modifications"
                    continue
                
                #print "committing", filespec
                itf = pyIT.ITfile()
                itf.open(filespec)
                
                # song message
                itf.Message = self.nbEdits.messagePane.editorChecked.GetValue()[:7999].encode(mod_encoding, "replace")
    
                # load samples/instruments from grid and put into itf
                fields = [
                    {'grid': self.nbEdits.samplePane.gridChecked,
                     'metadata': itf.Samples,
                     'namefield': 'SampleName',
                     'blank': pyIT.ITsample}, 
                    {'grid': self.nbEdits.instrumentPane.gridChecked,
                     'metadata': itf.Instruments,
                     'namefield': 'InstName',
                     'blank': pyIT.ITinstrument}
                     ]
                
                for field in fields: 
                    grid = field['grid'] 
                    metadata = field['metadata']
                    namefield = field['namefield']
                    blank = field['blank']
                    
                    last_populated_idx = 0
                    
                    n = grid.GetNumberRows()
                    for idx in xrange(n):
                        name = grid.GetCellValue(idx, 0)
                        if name.rstrip():
                            last_populated_idx = idx # trim empty entries from end
                    
                    # remove unused slots (only if sample)
                    try:
                        last_sample_idx = last_populated_idx
                        for idx in range(last_populated_idx+1, len(metadata)):
                            if metadata[idx].IsSample:
                                last_sample_idx = idx
                        for idx in range(last_sample_idx+1, len(metadata)):
                            metadata.pop()
                    except AttributeError:
                        # no .IsSample, so we're looking at an instrument
                        pass
                    
                    # clear all entries, add empty spaces for additional required lines
                    for line in metadata:
                        #print "erasing", line.__dict__[namefield]
                        line.__dict__[namefield] = ''
                    while last_populated_idx+1 > len(metadata): # add samples
                        metadata.append(blank())
        
                    for idx in xrange(last_populated_idx+1):
                        metadata[idx].__dict__[namefield] = grid.GetCellValue(idx, 0).encode(mod_encoding, "replace")
                itf.write(filespec)
                
                self.checked_files.remove(filespec)
            
            except:
                # queue errors
                errors = errors + u'[' + filespec + u']\n' + traceback.format_exc() + u'\n' 
                
        #self.checked_files = []
        if self.checked_files:
            msg = u"An error occurred processing the following files:\n\n"
            for filespec in self.checked_files:
                msg = msg + filespec + u'\n'
            if errors: 
                msg = msg + u"\nFeel like saving a stack trace?"
                mdlg = wx.MessageDialog(self, msg, "Some great reward", style=wx.ICON_ERROR|wx.YES_NO)
                if wx.ID_YES == mdlg.ShowModal():
                    fdlg = wx.FileDialog(self, "Save a stack trace to...", defaultFile="bitesy_stack.txt", wildcard="Text files (*.txt)|*.txt", style=wx.FD_SAVE)
                    if wx.ID_OK == fdlg.ShowModal():
                        f = file(fdlg.GetPath(), "w")
                        f.write(errors)
                    
        
        self.loadDir()
        event.Skip()
    
    def onRevertChecked(self, event):
        print "no revert no"
        event.Skip()
    
    def onCommitFile(self, event):
        if not self.opened:
            return
        filespec = self.opened['filespec']
        if filespec in self.modified_files:
            del self.modified_files[filespec]
        else:
            print "warning:", filespec, 'not modified; committing anyway'
        
        self.opened['data'].write(filespec)
        
        # reopen file
        self.open_it(filespec)
        
        event.Skip()
 
    def onRevertFile(self, event):
        # reopen file
        if not self.opened:
            return
        filespec = self.opened['filespec']
        if filespec in self.modified_files:
            del self.modified_files[filespec]
        else:
            print "warning:", filespec, 'not modified; reverting anyway'
        
        self.open_it(filespec)
        
        event.Skip()
 
# end of class EditFrame
 
 
class Bitesy(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        startFrame = EditFrame(None, -1, "")
        self.SetTopWindow(startFrame)
        startFrame.Show()
        return 1
 
# end of class Bitesy
 
if __name__ == "__main__":
    try:
        bitesy = Bitesy(0)
        bitesy.MainLoop()
    except:
        traceback.print_exc()
        raw_input("\n\nPress enter to exit...")
