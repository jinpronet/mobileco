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
    DEBUG = True
    device_isalive = False
    device_sn = ''
    slog = None

    def __init__(self):
        self.connect_adb_server()
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
        s = self.__socketD
        try:
            s.connect(('127.0.0.1', 5037))
        except:
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
                else:
                    dev_sn = ''

                if self.DEBUG:
                    print 'dev serial: %s' % dev_sn

                self.device_islive = False
                self.dev_sn = dev_sn
                print s.recv(1024) # receive all rest data

                break
        s.close()
        print self.device_islive
        return self.device_islive

    # Send adb shell command
    def adbshellcommand(self,cmd):
        reply = None
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
            reply = s.recv(4096)
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

    # Read adb response, if 'OKAY' turn true
    def readAdbResponse(self,s):
            if s != None:
                resp = s.recv(4)
                if self.DEBUG:
                    print 'resp: %s' % repr(resp)

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
        log.logd( 'start sleep count:'+ str(cout))
        time.sleep(1)

