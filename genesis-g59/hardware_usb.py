from quisk_hardware_model import Hardware as BaseHardware
import sys,os
import pdb
sys.path.append('./genesis-g59')
print(sys.path)
from g59_control import g59_cmd

class Hardware(BaseHardware):
    def __init__(self, app, conf):
        print("G59 Hardware", app, conf)
        BaseHardware.__init__(self, app, conf)
        self.g59 = g59_cmd(dummy_usb=False, dump_usb = False)
        self.vfo = 0
        self.g59.tx_off()
        self.g59.pa10_on(False)
        self.g59.rf_off()
        self.g59.af_off()
        self.g59.auto_cor(False)
        self.g59.auto_cor(False)
        print("si570_xtal_freq", conf.si570_xtal_freq)
        self.g59.set_xtal_offset(-0.0275)
        #pdb.set_trace()

    def open(self):
        print("open")

    def close(self):
        print("close")
        if self.g59:
            self.g59.usb_disconnect()
            self.g59 = None

    def ChangeFrequency(self, tune, vfo, source='', band='', event=None):
        print("ChangeFrequency", "tune",tune, "vfo",vfo, "source",source, "band",band)
        if self.g59:
            if vfo != self.vfo:
                self.g59.set_freq(vfo)
                self.vfo = vfo

        #self.g59.smooth(tune)
        return tune, vfo

    def ChangeBand(self, band):
        band = band.lower()
        print("ChangeBand",band)

        #Genesis G59 accepts the following
        # filter values:
        # 0,"gen",
        # 1,"160m",
        # 2,"80m",
        # 3,"60-40m",
        # 4,"30-20m",
        # 5,"17-15m",
        # 6,"12-10m",
        # 7,"6m",

        #_BAND_MAP {<QUISK BAND>:<G59 BAND>}
        _BAND_MAP = {"audio":0,
                     "time":0,
                     "160":1,
                     "80":2,
                     "60":3,
                     "40":3,
                     "30":4,
                     "20":4,
                     "17":5,
                     "15":5,
                     "12":6,
                     "10":6,
                     "6":7}
        filt = 0
        if _BAND_MAP.get(band):
            filt = _BAND_MAP[band]
        if self.g59:
            self.g59.set_filt(filt)

    def OnButtonPTT(self, event):
        print("OnButtonPTT", event)
        if event:
            if self.g59:
                if event.GetEventObject().GetValue():
                    self.g59.tx_on()
                else:
                    self.g59.tx_off()

    def OnButtonPA(self, value):
        print("OnButtonPA", value)
        if self.g59:
            if value:
                self.g59.pa10_on(True)
            else:
                self.g59.pa10_on(False)

    def OnButtonRfPre(self, value):
        print("OnButtonRfPre", value)
        if self.g59:
            if value:
                self.g59.rf_on()
            else:
                self.g59.rf_off()

    def OnButtonAfPre(self, value):
        print("OnButtonAfPre", value)
        if self.g59:
            if value:
                self.g59.af_on()
            else:
                self.g59.af_off()

    def OnButtonAutoCorr(self, value):
        print("OnButtonPA", value)
        if self.g59:
            if value:
                self.g59.auto_cor(True)
            else:
                self.g59.auto_cor(False)

    def OnSpot(self, level):
        # level is -1 for Spot button Off; else the Spot level 0 to 1000.
        print("OnSpot",level)


