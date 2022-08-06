#The MIT License (MIT)
#
#Copyright (c) 2015 Robert Anthony Bouterse, WD8RDE
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
import os
import time
import usb.core
import usb.util
from usb.backend import libusb0
from usb.backend import libusb1
import hid
import math
import threading
from .g59_si570 import Si570Utils

FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])

class g59_cmd:

    def dump(self, src, length=8):
        N=0; result=''
        if self.dump_usb:
            if(self.use_pyusb):
                while src:
                   s,src = src[:length],src[length:]
                   hexa = ' '.join(["%02X"%ord(str(x)) for x in s])
                   s = s.translate(FILTER)
                   result += "%04X   %-*s   %s\n" % (N, length*3, hexa, s)
                   N+=length
                return result
            else:
                hexa=''
                cp=''
                while src:
                    s,src = src[:length],src[length:]
                    hexa=''
                    cp=''
                    for x in s:
                        hexa += ' ' + format(x,'02x')
                        c = chr(x)
                        cp += c.translate(FILTER)
                    result += "%04X   %-*s   %s\n" % (N, length*3, hexa, cp)
                    N+=length
        return result

    def __init__(self, dummy_usb = False, dump_usb = False):
        self.dummy_usb = dummy_usb
        self.dump_usb = dump_usb
        self.use_pyusb = False
        self.timeout = 500
        self.xtal_offset = 0
        self.lock = threading.Lock()
        self.usb_connect()
        time.sleep(1.0)

    def usb_connect(self):
        if self.dummy_usb:
            return
        self.lock.acquire()
        # find our device
        if(self.use_pyusb):
            self.be = libusb1.get_backend()
            self.dev = usb.core.find(idVendor=0xfffe, idProduct=0x1970, backend=self.be)
            # was it found?
            if self.dev is None:
                raise ValueError('Device not found')

            self.interface = 0
            c = 1
            for config in self.dev:
                print('config',c)
                print('Interfaces', config.bNumInterfaces)
                for iface in range(config.bNumInterfaces):
                    print('interface',iface)
                    #if self.dev.is_kernel_driver_active(iface):
                    try:
                        print('Detaching kernel driver')
                        self.dev.detach_kernel_driver(iface)
                        usb.util.claim_interface(self.dev,iface)
                    except:
                        print('Failed detaching kernel driver')
                c+=1


            self.dev.reset()
            # set the active configuration. With no arguments, the first
            # configuration will be the active one
            self.dev.set_configuration()

            # get an endpoint instance
            self.cfg = self.dev.get_active_configuration()
            self.intf = self.cfg[(0,0)]

            self.ep_out = usb.util.find_descriptor(
                self.intf,
                # match the first OUT endpoint
                custom_match = \
                lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_OUT)

            assert self.ep_out is not None

            self.ep_in = usb.util.find_descriptor(
                self.intf,
                # match the first IN endpoint
                custom_match = \
                lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_IN)

            assert self.ep_in is not None

#           print('dev',self.dev)
#           print('configuration',self.cfg)
#           print('interface',self.intf)
#           print('ep_out',self.ep_out)
#           print('ep_in',self.ep_in)

        else:
            self.dev = hid.device()
            self.dev.open(vendor_id=0xfffe, product_id=0x1970)
        # was it found?
        if self.dev is None:
            raise ValueError('Device not found')
        self.lock.release()

    def usb_disconnect(self):
        if(self.use_pyusb):
            if self.dummy_usb:
                return
            self.lock.acquire()
            c = 1
            for config in self.dev:
                print('config',c)
                print('Interfaces', config.bNumInterfaces)
                for iface in range(config.bNumInterfaces):
                    print('release interface',iface)
                    usb.util.release_interface(self.dev,iface)
                c+=1
            usb.util.dispose_resources(self.dev)
            self.lock.release()
        else:
            self.dev.close()

    def usb_write(self,pct):
        self.lock.acquire()
        #self.usb_connect()
        if(self.use_pyusb):
            self.ep_out.write(pct, timeout=self.timeout)
        else:
            self.dev.write(pct)
        self.lock.release()
        #self.usb_disconnect()

    def __send_cmd(self, cmd, param):
        if self.dummy_usb:
            return
        cmd_array = self.__str2array(cmd)
        cmd_packet = self.__pack_cmd(cmd_array)
        packet = self.__pack_request(cmd_packet, param)
        print(self.dump(packet))
        self.usb_write(packet)

    def __pack_request(self,cmd,args):
        packet=[]
        for i in range(0,64):
            packet.append(0x00)

        i = 0
        for byte in cmd:
            packet[i] = byte
            i += 1

        if args is not None:
            i = 8
            for byte in args:
                packet[i] = byte
                i += 1

        if(self.use_pyusb):
            return ''.join([chr(c) for c in packet])
        else:
            return packet

    def __pack_cmd(self, cmd):
        packet=[]
        for i in range(8):
            packet.append(0x20)

        i=0
        for byte in cmd:
            packet[i] = byte
            i += 1
            if i > 7:
                break
        return packet

    def __str2array(self, strng):
        arry = []
        for c in strng:
            arry.append(ord(c))
        return arry

    def __send_freq_cmd(self,cmd,freq):
        if self.dummy_usb:
            return
        #convert freq to MHz
        freq = (float(freq)/(10**6))
        si570 = Si570Utils(verbose=0, xtal_offset=self.xtal_offset)
        print('freq',freq)
        registers = si570.setFreq(freq)
        cmd_array = self.__str2array(cmd)
        cmd_packet = self.__pack_cmd(cmd_array)

        freq_str = str(int(freq * 1000000))
        freq_str = '00000000' + freq_str
        freq_str = freq_str[-8:]
        freq_array = self.__str2array(freq_str)

        param = []
        for i in range(56):
            param.append(0x00)

        for i in range(8):
            param[i] = freq_array[i]

        param[10] = 0xaa # i2c address

        param[12] = registers[0] #0xe7
        param[13] = registers[1] #0x42
        param[14] = registers[2] #0xb2
        param[15] = registers[3] #0x8b
        param[16] = registers[4] #0x24
        param[17] = registers[5] #0xe0

        packet = self.__pack_request(cmd_packet, param)
        self.usb_write(packet)

    def att_on(self):
        self.__send_cmd("ATT_ON",None)
        return

    def att_off(self):
        self.__send_cmd("ATT_OFF",None)
        return

    def set_name(self, name):
        return

    def set_xtal_offset(self, offset):
        self.xtal_offset = offset

    def set_freq(self, freq):
        if 0 < freq:
            self.__send_freq_cmd('SET_FREQ', int(freq))
        return

    def smooth(self, freq):
        self.__send_freq_cmd('SMOOTH', freq)
        return

    def set_filt(self,fltr_arg):
        #filter values
        # 0,"gen",
        # 1,"160m",
        # 2,"80m",
        # 3,"60-40m",
        # 4,"30-20m",
        # 5,"17-15m",
        # 6,"12-10m",
        # 7,"6m",
        fltr = int(fltr_arg)
        if (fltr < 0) or (fltr > 7):
            raise ValueError("set_filt argument out of range(0-7)",filtr_arg)
        param = []
        for i in range(56):
            param.append(0x00)
        param[12] = fltr
        self.__send_cmd("SET_FILT", param)
        return

    def af_on(self):
        self.__send_cmd("AF_ON",None)
        return

    def af_off(self):
        self.__send_cmd("AF_OFF",None)
        return

    def mute_on(self):
        self.__send_cmd("MUTE_ON",None)
        return

    def mute_off(self):
        self.__send_cmd("MUTE_OFF",None)
        return

    def trv_on(self):
        self.__send_cmd("TRV_ON",None)
        return

    def trv_off(self):
        self.__send_cmd("TRV_OFF",None)
        return

    def rf_on(self):
        self.__send_cmd("RF_ON",None)
        return

    def rf_off(self):
        self.__send_cmd("RF_OFF",None)
        return

    def tx_on(self):
        self.__send_cmd("TX_ON",None)
        return

    def tx_off(self):
        self.__send_cmd("TX_OFF",None)
        return

    def k_speed(self,wpm):
        divisor = int(520/wpm)
        param = []
        for i in range(56):
            param.append(0x00)

        param[12] = divisor
        self.__send_cmd("K_SPEED", param)
        return

    def k_mode(self,mode):
        param = []
        for i in range(56):
            param.append(0x00)

        param[12] = int(mode)
        self.__send_cmd("K_SPEED", param)
        return

    def k_ratio(self,ratio):
        param = []
        for i in range(56):
            param.append(0x00)

        param[12] = int(ratio)
        self.__send_cmd("K_SPEED", param)
        return

    def pa10_on(self,on_off):
        param = []
        for i in range(56):
            param.append(0x00)

        if on_off:
            param[12] = 0x01

        self.__send_cmd("PA10_ON", param)
        return

    def line_mic(self,on_off):
        param = []
        for i in range(56):
            param.append(0x00)

        if on_off:
            param[12] = 0x01

        self.__send_cmd("LINE/MIC", param)
        return

    def auto_cor(self, on_off):
        param = []
        for i in range(56):
            param.append(0x00)

        if on_off:
            param[12] = 0x01

        self.__send_cmd("AUTO_COR", param)
        return

    def sec_rx2(self, on_off):
        param = []
        for i in range(56):
            param.append(0x00)

        if on_off:
            param[12] = 0x01

        self.__send_cmd("SEC_RX2", param)
        return

    def monitor(self):
        self.__send_cmd("MONITOR",None)
        return

if __name__ == "__main__":
    m_g59 = g59_cmd()
    m_g59.set_filt(4)
    #import sys
    #sys.stdin.readline()



