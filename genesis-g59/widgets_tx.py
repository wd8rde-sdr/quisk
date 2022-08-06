# Please do not change this widgets module for Quisk.  Instead copy
# it to your own quisk_widgets.py and make changes there.
#
# This module is used to add extra widgets to the QUISK screen.

import wx
import _quisk as QS
import math

class BottomWidgets:	# Add extra widgets to the bottom of the screen
    def __init__(self, app, hardware, conf, frame, gbs, vertBox):
        print("app", app,'\n',
              "hardware", hardware,'\n',
              "conf", conf,'\n',
              "frame", frame,'\n',
              "gbs", gbs,'\n',
              "vertBox", vertBox,'\n')
        #self.info_text = app.QuiskText(frame, 'Info',1)
        #gbs.Add(self.info_text, (4, 0), (1, 27), flag=wx.EXPAND)
        self.config = conf
        self.hardware = hardware
        self.application = app
        row = 4			# The next available row
        b = app.QuiskCheckbutton(frame, self.OnBtnPa, '10W PA')
        bw, bh = b.GetMinSize()
        b.Enable(1)
        gbs.Add(b, (row, 1), (1, 2), flag=wx.EXPAND)
        b = app.QuiskCheckbutton(frame, self.OnBtnRfPre, 'RF Preamp')
        gbs.Add(b, (row, 3), (1, 2), flag=wx.EXPAND)
        b = app.QuiskCheckbutton(frame, self.OnBtnAfPre, 'AF Preamp')
        gbs.Add(b, (row, 5), (1, 2), flag=wx.EXPAND)
        b = app.QuiskCheckbutton(frame, self.OnBtnAutoCorr, 'Auto Corr')
        gbs.Add(b, (row, 7), (1, 2), flag=wx.EXPAND)
    def OnBtnPa(self, event):
        print("OnBtnpa event", event)
        value = event.GetIsDown()
        self.hardware.OnButtonPA(value)
    def OnBtnRfPre(self, event):
        print("OnBtnRfPre event", event)
        value = event.GetIsDown()
        self.hardware.OnButtonRfPre(value)
    def OnBtnAfPre(self, event):
        print("OnBtnAfPre event", event)
        value = event.GetIsDown()
        self.hardware.OnButtonAfPre(value)
    def OnBtnAutoCorr(self, event):
        print("OnBtnAutoCorr event", event)
        value = event.GetIsDown()
        self.hardware.OnButtonAutoCorr(value)
    def OnBtnNext(self, event):
        print("OnBtnNext")

