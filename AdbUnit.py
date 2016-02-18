#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# File: AdbUnit.py
# Desp:
#   This File for adb control unit
#
# Author: youjin
# Bug report: jinrich@126.com
# Date: 2016.1.31
# ---------------------------------------------------------------------------
import socket
import subprocess,os
import threading
import socket,sys
import time
import Slogy


class AdbUnit:
    '''
    class of Unit for adb transfor
    '''

    __socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    __socketD = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    DEBUG = False
    device_isalive = False
    device_sn = ''
    slog = None

    def __init__(self):
        #self.connect_adb_server()
        self.slog = Slogy.Slogy("adbunit")
        pass

    #connect the adb server
    def connect_adb_server(self):
        """
        Test to connect the adb server ,if not server start
        then start it
        """
        while True:
            try:
                self.__socket.connect(('127.0.0.1', 5037))

            except:
                os.system('adb start-server')
                time.sleep(2)
                continue
            else:
                break

        #
    def device_exist(self):
        """
        Test for the adb devcies have online
        """
        req_msg = 'host:devices'
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(('127.0.0.1', 5037))
        except Exception,e:
            print e
            os.system('adb start-server')
            self.device_islive = False
            self.device_sn = ''
            return False
        #send and get device
        while True:
            s.sendall('%04x' % len(req_msg))
            s.sendall(req_msg)
            if self.readAdbResponse(s):
                len_str = s.recv(4)
                if len(len_str) < 4:
                    continue
                length = int(len_str, 16)
                dev_info = s.recv(length)
                if '\t' in dev_info:
                    dev_sn = dev_info[0:dev_info.index('\t')]
                    self.device_islive = True
                else:
                    self.device_islive = False
                    dev_sn = ''

                if self.DEBUG:
                    print 'dev serial: %s' % dev_sn


                self.dev_sn = dev_sn
                print "exist device: "+s.recv(1024) # receive all rest data

                break
        s.close()
        print self.device_islive
        return self.device_islive

    # Send adb shell command
    def adbshellcommand(self,cmd):
        """
        Send a command to adb mobile
        """
        reply = ""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # waiting adb server start
        while True:
            try:
                s.connect(('127.0.0.1', 5037))
            except:
                os.system('adb start-server')
                time.sleep(2)
                continue
            else:
                break

        req_msg = 'host:transport-any'
        s.sendall('%04x' % len(req_msg))
        s.sendall(req_msg)
        if not self.readAdbResponse(s):
            return None

        req_msg = 'shell:%s' % cmd
        if self.DEBUG:
            print '%s' % req_msg
        s.sendall('%04x' % len(req_msg))
        s.sendall(req_msg)

        if self.readAdbResponse(s):
            while True:
                rp = s.recv(4096)
                print "reply:",len(rp)
                if len(rp)== 0:
                    break
                reply = reply + rp

            print "reply2:",len(reply)

            if self.DEBUG:
                self.hexdump(bytearray(reply))
        s.close()

        return reply
    # Print Hex Buffer
    def hexdump(self,buf = None):
        if buf != None:
            pstr = ''
            cnt = 0
            for x in buf:
                if (cnt + 1) % 8 == 0:
                    pstr = '%s%02X\n' % (pstr, x)
                else:
                    pstr = '%s%02X ' % (pstr, x)
                cnt = cnt + 1
            print pstr

    def sendKey(self,key):
        if self.device_exist() :
            self.adbshellcommand('input keyevent %s' % key)
        else:
            self.slog.loge("device not online for key:[%s] input" % key)


    def readAdbResponse(self,s):
        """
        Read adb response, if 'OKAY' turn true
        """
        if s is not None:
            resp = s.recv(4)
            if self.DEBUG:
                print 'resp: %s ' % repr(resp)

        if len(resp) != 4:
            print 'protocol fault (no status)'
            return False

        if resp == 'OKAY':
            return True
        elif resp == 'FAIL':
            resp = s.recv(4)
            if len(resp) < 4:
                print 'protocol fault (status len)'
                return False
            else:
                length = int(resp, 16)
                resp = s.recv(length)
                if len(resp) != length:
                    print 'protocol fault (status read)'
                    return False
                else:
                    print resp
                    return False
        else:
            print "protocol fault (status %02x %02x %02x %02x?!)", (resp[0], resp[1], resp[2], resp[3])
            return False

        return False

    # Print Hex Buffer
    def hexdump(self,buf = None):
        if buf != None:
            pstr = ''
            cnt = 0
            for x in buf:
                if (cnt + 1) % 8 == 0:
                    pstr = '%s%02X\n' % (pstr, x)
                else:
                    pstr = '%s%02X ' % (pstr, x)
                cnt = cnt + 1
            self.slog.logd(pstr)

    # Convert buffer to Int
    def getInt(self,tbuf = None):
        if (tbuf != None):

            self.hexdump(bytearray(tbuf))
            if len(tbuf) < 4:
                print 'buff len < 4'
                return 0
            else:
                self.slog.logd('parse: %02x %02x %02x %02x' % (tbuf[0],tbuf[1],tbuf[2],tbuf[3]))
                intnum = tbuf[0]
                intnum = intnum + tbuf[1]*0x100
                intnum = intnum + tbuf[2]*0x10000
                intnum = intnum + tbuf[3]*0x1000000
                self.slog.logd('INT: %08x' % intnum)
                return intnum
        else:
            return 0


    def readHeader(self,tfb, ver, buf):
        """
        Parse fb header from buffer
        """
        self.slog.logd('readHeader: ver = ' + str(ver))
        if ver == 16:
            tfb.fb_bpp = 16
            tfb.fb_size = self.getInt(buf[0:4])
            tfb.fb_width = self.getInt(buf[4:8])
            tfb.fb_height = self.getInt(buf[8:12])
            tfb.red_offset = 11
            tfb.red_length = 5
            tfb.blue_offset = 5
            tfb.blue_length = 6
            tfb.green_offset = 0
            tfb.green_length = 5
            tfb.alpha_offset = 0
            tfb.alpha_length = 0
        elif ver == 1:
            tfb.fb_bpp = self.getInt(bytearray(buf[0:4]))
            tfb.fb_size = self.getInt(bytearray(buf[4:8]))
            tfb.fb_width = self.getInt(bytearray(buf[8:12]))
            tfb.fb_height = self.getInt(bytearray(buf[12:16]))
            tfb.red_offset = self.getInt(bytearray(buf[16:20]))
            tfb.red_length = self.getInt(bytearray(buf[20:24]))
            tfb.blue_offset = self.getInt(bytearray(buf[24:28]))
            tfb.blue_length = self.getInt(bytearray(buf[28:32]))
            tfb.green_offset = self.getInt(bytearray(buf[32:36]))
            tfb.green_length = self.getInt(bytearray(buf[36:40]))
            tfb.alpha_offset = self.getInt(bytearray(buf[40:44]))
            tfb.alpha_length = self.getInt(bytearray(buf[44:48]))
        else:
            return False
        return True


    def get_touch_event(self):
        """
        Find the Touch input device and event
        """
        tp_names = ['ft5x06', 'gt818']
        output = self.adbshellcommand('getevent -S')
        if output == None:
            return None

        self.slog.logd(output)
        dev = ''
        name = ''
        for line in output.splitlines():
            if '/dev/input/event' in line:
                line = line.split(':')
                if len(line) == 2:
                    line = line[1]
                    line = line.strip(' ')
                    line = line.strip('"')
                    dev = line
            elif 'name:' in line:
                line = line.split(':')
                if len(line) == 2:
                    line = line[1]
                    line = line.strip(' ')
                    line = line.strip('"')
                    name = line

            if (dev != '') and (name in tp_names):
                break

        self.slog.logd('%s : %s' % (name, dev))

        if name in tp_names:
            return (name, dev)
        else:
            return None

    def send_touch_event(self,action, x0, y0, x1 = None, y1 = None):
        """
        Do the touch action
        Note: input support tap & swipe after 4.1
        so we need emulate TP via sendevent if tap or swipe fail
        """

        if action == 'tap':
            resp = self.adbshellcommand('input tap %d %d' % (x0, y0))
            if 'Error' in resp:
                print 'Not support tap command'

                # get tp device
                tp = self.get_touch_event()

                if tp == None:
                    return

                # down
                cmd_str = ''
                cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 3, 53, x0)
                cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 3, 54, y0)
                cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 3, 57, 0)
                cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 3, 48, 0)
                cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 0, 2, 0)
                cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 1, 330, 1)
                cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 0, 0, 0)

                # up
                cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 1, 330, 0)
                cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 0, 2, 0)
                cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 0, 0, 0)

                self.slog.logd(cmd_str)
                self.adbshellcommand(cmd_str)
        elif action == 'swipe':
            resp = self.adbshellcommand('input swipe %d %d %d %d' % (x0, y0, x1, y1))
            if 'Error' in resp:
                print 'Not support tap command'

                # get tp device
                tp = self.get_touch_event()

                if tp == None:
                    return

                step = 3
                stepx = abs(x1 - x0) / step
                stepy = abs(y1 - y0) / step
                x = x0
                y = y0

                for i in range(0, step + 1):
                    if x0 < x1:
                        x = x0 + i * stepx
                    else:
                        x = x0 - i * stepx

                    if y0 < y1:
                        y = y0 + i * stepy
                    else:
                        y = y0 - i * stepy

                    cmd_str = ''
                    cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 3, 53, x)
                    cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 3, 54, y)
                    cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 3, 57, 0)
                    cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 3, 48, 0)
                    cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 0, 2, 0)
                    cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 1, 330, 1)
                    cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 0, 0, 0)
                    self.adbshellcommand(cmd_str)

                # up
                cmd_str = ''
                cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 1, 330, 0)
                cmd_str += 'sendevent %s %d %d %d;' % (tp[1], 0, 2, 0)
                cmd_str += 'sendevent %s %d %d %d' % (tp[1], 0, 0, 0)
                self.slog.logd(cmd_str)
                self.adbshellcommand(cmd_str)




if __name__ == '__main__':

    adb = AdbUnit()
    cout = 0
    log = Slogy.Slogy("good")
    while cout < 10:
        cout += 1
        print 'begin'
        adb.device_exist()
        log.logi( 'start sleep 1234 count:'+ str(cout))
        #time.sleep(1)

