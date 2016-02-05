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
    class

    '''

    __socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    __socketD = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    DEBUG = False
    device_isalive = False
    device_sn = ''
    slog = None

    def __init__(self):
        self.connect_adb_server()
        self.slog = Slogy.Slogy("adbunit")
        pass

    #connect the adb server
    def connect_adb_server(self):

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

    # Read adb response, if 'OKAY' turn true
    def readAdbResponse(self,s):
            if s != None:
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

if __name__ == '__main__':
    adb = AdbUnit()
    cout = 0
    log = Slogy.Slogy("good")
    while True:
        cout += 1
        print 'begin'
        adb.device_exist()
        log.logi( 'start sleep 1234 count:'+ str(cout))
        #time.sleep(1)

