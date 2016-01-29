#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Android Mobileco 0.1
# This is a free software under GPL.
#
# Author: youjin
# Bug report: jinrich@126.com
# ---------------------------------------------------------------------------

__author__ = 'youjin'
__version__ = '0.1'

import subprocess,os
import threading
import socket,sys
import time
import Slogy

try:
    import Tkinter as tk
    import ttk
    from tkMessageBox import *
    from PIL import Image,ImageTk,ImageDraw
except:
    print 'Following module is needed:'
    print '- Tkinter: sudo apt-get install python-tk'
    print '- PIL: sudo apt-get install python-imaging-tk'
    sys.exit()

# Set DEBUG to True if you need know more running message
DEBUG = False

# Set USE_TTK to False if you need classic Tk/Tcl GUI-style
USE_TTK = True


# keynames is the key name list
# 'none': no keys in this grid
keynames = ['home', 'menu',  'back',  'srch',
            'call',    '^',    'end',  'none',
              '<',  'ok',      '>',  'vol+',
            'none',    'v',  'none',  'vol-',
              '1',    '2',      '3',  'none',
              '4',    '5',      '6',  'cam',
              '7',    '8',      '9', 'enter',
              '*',    '0',      '#'
            ]

# keyvalues is the key value list map with the keynames
# 0: no keys here
keyvalues = [ 3, 82, 4, 84,
              5, 19, 6,  0,
              21,23,22, 24,
              0, 20, 0, 25,
              8,  9,10, 0,
              11,12,13, 27,
              14,15,16, 66,
              17, 7,18
            ]

# Print Hex Buffer
def hexdump(buf = None):
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
def readAdbResponse(s):
    if s != None:
        resp = s.recv(4)
        if DEBUG:
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

# Send adb shell command
def adbshellcommand(cmd):
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
    if not readAdbResponse(s):
        return None

    req_msg = 'shell:%s' % cmd
    if DEBUG:
        print '%s' % req_msg
    s.sendall('%04x' % len(req_msg))
    s.sendall(req_msg)
    if readAdbResponse(s):
        reply = s.recv(4096)
        if DEBUG:
            hexdump(bytearray(reply))
    s.close()

    return reply

# Convert buffer to Int
def getInt(tbuf = None):
    if (tbuf != None):
        if DEBUG:
            hexdump(bytearray(tbuf))
        if len(tbuf) < 4:
            print 'buff len < 4'
            return 0
        else:
            if DEBUG:
                print 'parse: %02x %02x %02x %02x' % (tbuf[0],tbuf[1],tbuf[2],tbuf[3])
            intnum = tbuf[0]
            intnum = intnum + tbuf[1]*0x100
            intnum = intnum + tbuf[2]*0x10000
            intnum = intnum + tbuf[3]*0x1000000
            if DEBUG:
                print 'INT: %08x' % intnum
            return intnum
    else:
        return 0

# Parse fb header from buffer
def readHeader(tfb, ver, buf):
    if DEBUG:
        print 'readHeader: ver = %d' % ver
    if ver == 16:
        tfb.fb_bpp = 16
        tfb.fb_size = getInt(buf[0:4])
        tfb.fb_width = getInt(buf[4:8])
        tfb.fb_height = getInt(buf[8:12])
        tfb.red_offset = 11
        tfb.red_length = 5
        tfb.blue_offset = 5
        tfb.blue_length = 6
        tfb.green_offset = 0
        tfb.green_length = 5
        tfb.alpha_offset = 0
        tfb.alpha_length = 0
    elif ver == 1:
        tfb.fb_bpp = getInt(bytearray(buf[0:4]))
        tfb.fb_size = getInt(bytearray(buf[4:8]))
        tfb.fb_width = getInt(bytearray(buf[8:12]))
        tfb.fb_height = getInt(bytearray(buf[12:16]))
        tfb.red_offset = getInt(bytearray(buf[16:20]))
        tfb.red_length = getInt(bytearray(buf[20:24]))
        tfb.blue_offset = getInt(bytearray(buf[24:28]))
        tfb.blue_length = getInt(bytearray(buf[28:32]))
        tfb.green_offset = getInt(bytearray(buf[32:36]))
        tfb.green_length = getInt(bytearray(buf[36:40]))
        tfb.alpha_offset = getInt(bytearray(buf[40:44]))
        tfb.alpha_length = getInt(bytearray(buf[44:48]))
    else:
        return False
    return True

# Find the Touch input device and event
def get_touch_event():
    tp_names = ['ft5x06', 'gt818']
    output = adbshellcommand('getevent -S')
    if output == None:
        return None

    if DEBUG:
        print output
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

    if DEBUG:
        print '%s : %s' % (name, dev)

    if name in tp_names:
        return (name, dev)
    else:
        return None

# Do the touch action
def send_touch_event(action, x0, y0, x1 = None, y1 = None):
    # Note: input support tap & swipe after 4.1
    # so we need emulate TP via sendevent if tap or swipe fail
    if action == 'tap':
        resp = adbshellcommand('input tap %d %d' % (x0, y0))
        if 'Error' in resp:
            print 'Not support tap command'

            # get tp device
            tp = get_touch_event()

            if tp == None:
                return

            # down
            cmd_str = ''
            cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 3, 53, x0)
            cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 3, 54, y0)
            cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 3, 57, 0)
            cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 3, 48, 0)
            cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 0, 2, 0)
            cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 1, 330, 1)
            cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 0, 0, 0)

            # up
            cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 1, 330, 0)
            cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 0, 2, 0)
            cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 0, 0, 0)

            if DEBUG:
                print cmd_str
            adbshellcommand(cmd_str)
    elif action == 'swipe':
        resp = adbshellcommand('input swipe %d %d %d %d' % (x0, y0, x1, y1))
        if 'Error' in resp:
            print 'Not support tap command'

            # get tp device
            tp = get_touch_event()

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
                cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 3, 53, x)
                cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 3, 54, y)
                cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 3, 57, 0)
                cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 3, 48, 0)
                cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 0, 2, 0)
                cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 1, 330, 1)
                cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 0, 0, 0)
                adbshellcommand(cmd_str)

            # up
            cmd_str = ''
            cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 1, 330, 0)
            cmd_str = cmd_str + 'sendevent %s %d %d %d;' % (tp[1], 0, 2, 0)
            cmd_str = cmd_str + 'sendevent %s %d %d %d' % (tp[1], 0, 0, 0)
            if DEBUG:
                print cmd_str
            adbshellcommand(cmd_str)

# Framebuffer Class
# Only record framebuffer attributs
class fb:
    fb_bpp = 0
    fb_size = 0
    fb_width = 0
    fb_height = 0
    red_offset = 0
    red_length = 0
    blue_offset = 0
    blue_length = 0
    green_offset = 0
    green_length = 0
    alpha_offset = 0
    alpha_length = 0
    fb_data = None

    def __init__(self):
        fb_bpp = 0
        fb_size = 0
        fb_width = 0
        fb_height = 0
        red_offset = 0
        red_length = 0
        blue_offset = 0
        blue_length = 0
        green_offset = 0
        green_length = 0
        alpha_offset = 0
        alpha_length = 0
        fb_data = None

# send key thread
class send_key_thread(threading.Thread):
    __tkapp = None
    __root = None
    __key = None

    def __init__(self, key):
        if DEBUG:
            print 'send_key_thread init'
        threading.Thread.__init__(self)
        self.thread_stop = False
        self.__key = key

    def devexist(self):
        p = subprocess.Popen("adb devices", shell=True, stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
        p.wait()
        devList = p.communicate()
        devList = devList[0].splitlines()
        if 'device' in devList[1]:
            if DEBUG:
                print devList[1]
            return True
        else:
            if DEBUG:
                print 'No adb device found'
            return False
        p.stdout.close()
        p.stderr.close()
        
    def sendKey(self):
        if DEBUG:
            print 'send_key: %s' % self.__key
        if self.__key in keynames:
            if self.devexist():
                if self.__key != 'none':
                    adbshellcommand('input keyevent %s' % str(keyvalues[keynames.index(self.__key)]))

    def run(self):
        if DEBUG:
            print 'send_key_thread run'
        self.sendKey()

    def stop(self):
        if DEBUG:
            print 'stop send_key_thread'
        self.thread_stop = True

# Kaypad Tkinter-Based GUI application
class ttkKeypadApplication(ttk.Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master, class_='ttkKeypadApplication')
        title = 'mobileco '+ __version__+ '-Keypad'
        self.master.title(title)
        self.createkeypad()
        self.grid()

    def createkeypad(self):
        # creat buttons from keymap with 4 buttons each row
        for btn_name in keynames:
            row_id = keynames.index(btn_name) / 4
            col_id = keynames.index(btn_name) % 4

            if btn_name != 'none':
                self.tbutton = ttk.Button(self, name = btn_name, text=btn_name)
            else:
                self.tbutton = ttk.Button(self, name = btn_name, text='')

            self.tbutton['width'] = 10
            if btn_name != 'none':
                self.tbutton.bind('<ButtonRelease-1>', self.sendKey)
                self.tbutton.grid(padx = 5, pady = 1, column = col_id, row = row_id)

    def devexist(self):
        p = subprocess.Popen("adb devices", shell=True, stdout=subprocess.PIPE)
        p.wait()
        devList = p.communicate()
        devList = devList[0].splitlines()
        if 'device' in devList[1]:
            if DEBUG:
                print devList[1]
            return True
        else:
            if DEBUG:
                print 'No adb device found'
            return False

    def sendKey(self, event=None):
        if DEBUG:
            print event.widget.winfo_name()
        keyname = event.widget.winfo_name()
        if keyname in keynames:
            sender = send_key_thread(keyname)
            sender.start()

# LCD Tkinter-Based GUI application
class LcdApplication(tk.Frame):
    __img_factor = 1.00 # image resize rate
    __lcd = None # the label widget
    __keepupdate = True
    __im = None
    __rotate = 0

    # record mouse start & end point location
    __start = [0, 0]
    __end = [0, 0]
    __master= None
    def __init__(self, master):
        if DEBUG:
            print 'LcdApplication: __init__'

        tk.Frame.__init__(self, master, class_='LcdApplication')
        self.__master = master
        self.__rotate = 0
        self.createlcd()
        self.grid()

    def createlcd(self):
        # creat label as lcd
        if DEBUG:
            print 'LcdApplication: createlcd'

        # make default image display on label
        image = Image.new(mode = 'RGB', size = (240, 320), color = '#000000')
        draw = ImageDraw.Draw(image)
        draw.text((80, 100), 'Connecting...')
        self.__im = ImageTk.PhotoImage(image)

        # create label with image option
        self.__lcd = tk.Label(self, image=self.__im)
        self.__lcd.bind('<Button-1>', self.click_label)
        self.__lcd.bind('<ButtonRelease-1>', self.click_label)
        self.__lcd.bind('<ButtonRelease-3>', self.rightclick_label)

        # disply label on frame
        self.__lcd.grid()

    # To serve right click on label widget
    def rightclick_label(self, event=None):
        if DEBUG:
            print 'Type: %s' % event.type
        self.__rotate = (self.__rotate + 90) % 360
        print "rotate: %d" % self.__rotate

    # To serve left click on label widget
    def click_label(self, event=None):
        if DEBUG:
            print 'Type: %s' % event.type
        if event.type == '4':
            # record mouse left button down
            if DEBUG:
                print 'Click at: (%d, %d)' % (event.x, event.y)
            self.__start[0] = int(float(event.x) / float(self.__img_factor))
            self.__start[1] = int(float(event.y) / float(self.__img_factor))
            self.__end = None
        elif event.type == '5':
            # record mouse left button up
            if DEBUG:
                print 'Release at: (%d, %d)' % (event.x, event.y)
            self.__end = [0, 0]
            self.__end[0] = int(float(event.x) / float(self.__img_factor))
            self.__end[1] = int(float(event.y) / float(self.__img_factor))

        # Do not report touch event during mouse down
        if self.__end == None:
            return

        if abs(self.__start[0] - self.__end[0]) < 2 and \
          abs(self.__start[1] - self.__end[1]) < 2 :
            # mouse action: tap
            send_touch_event('tap', self.__start[0], self.__start[1])
        else:
            # mouse action: swipe
            send_touch_event('swipe', self.__start[0], self.__start[1], self.__end[0], self.__end[1])



    def stop(self):
        if DEBUG:
            print 'LcdApplication: stop'
        self.__keepupdate = False
        self.__im.__del__()

    # screen capture via socket from adb server
    def updatelcd_sock(self):
        if DEBUG:
            print 'LcdApplication: updatelcd_sock'
        # Max display area size on label widget
        #max_lcd_w = 1024
        #max_lcd_h = 600
        max_lcd_w = 1440
        max_lcd_h = 720


        dev_sn = ''
        hdrsize = 0
        myfb = fb()
        refresh_count = 0 # record refresh count
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while self.__keepupdate:
            #print "begin time"
            start_cpu = time.clock()
            # Get device SerialNumber from ADB server

            try:
                s.connect(('127.0.0.1', 5037))
            except:
                os.system('adb start-server')
                time.sleep(2)
                continue

            req_msg = 'host:devices'
            s.sendall('%04x' % len(req_msg))
            s.sendall(req_msg)
            if readAdbResponse(s):
                len_str = s.recv(4)
                if len(len_str) < 4:
                    continue
                length = int(len_str, 16)
                dev_info = s.recv(length)
                if '\t' in dev_info:
                    dev_sn = dev_info[0:dev_info.index('\t')]
                else:
                    dev_sn = ''
                if DEBUG:
                    print 'dev serial: %s' % dev_sn
            s.recv(1024) # receive all rest data
            s.close()

            if dev_sn == '':
                print "no device"
                continue

            # Get framebuffer from ADB server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('127.0.0.1', 5037))
            req_msg = 'host:transport:%s' % dev_sn
            s.sendall('%04x' % len(req_msg))
            s.sendall(req_msg)
            if not readAdbResponse(s):
                s.close()
            else:
                if DEBUG:
                    print 'ready to transport'
                req_msg = 'framebuffer:'
                s.sendall('%04x' % len(req_msg))
                s.sendall(req_msg)
                if not readAdbResponse(s):
                    s.close()
                else:
                    reply = s.recv(4)
                    if len(reply) < 4:
                        continue

                    fbver = ord(reply[0]) + \
                            ord(reply[1]) * 0x100 + \
                            ord(reply[2]) * 0x10000 + \
                            ord(reply[3]) * 0x1000000
                    if DEBUG:
                        print 'fbver: %08x' % fbver

                    # Get fb header size
                    if fbver == 16:
                        hdrsize = 3
                    elif fbver == 1:
                        hdrsize = 12
                    else:
                        hdrsize = 0;
                    if DEBUG:
                        print 'fb header size: %d' % hdrsize

                    # read the header
                    header = s.recv(hdrsize * 4)
                    if len(header) < (hdrsize * 4):
                        continue

                    if DEBUG:
                        hexdump(bytearray(header))
                    readHeader(myfb, fbver, header)
                    if DEBUG:
                        print 'bpp: %d' % myfb.fb_bpp
                        print 'size: %d' % myfb.fb_size
                        print 'width: %d' % myfb.fb_width
                        print 'height: %d' % myfb.fb_height
                        print 'red_offset: %d' % myfb.red_offset
                        print 'red_length: %d' % myfb.red_length
                        print 'blue_offset: %d' % myfb.blue_offset
                        print 'blue_length: %d' % myfb.blue_length
                        print 'green_offset: %d' % myfb.green_offset
                        print 'green_length: %d' % myfb.green_length
                        print 'alpha_offset: %d' % myfb.alpha_offset
                        print 'alpha_length: %d' % myfb.alpha_length

                    end1_cpu = time.clock()
                    print "end1 time :%f " % (end1_cpu - start_cpu)
                    # read fb buffer
                    rcvcnt = 0
                    readbyte = 0
                    imagebuff = []
                    end2_cpu = time.clock()
                    print "begin read fb time :%f " % (end2_cpu - end1_cpu)
                    print "fb_size :%d " % myfb.fb_size

                    while True:
                        if (rcvcnt < myfb.fb_size):
                            readbyte = myfb.fb_size - rcvcnt
                        else:
                            break
                        resp = s.recv(readbyte)
                        if DEBUG:
                            print 'read byte: %d' % len(resp)
                        rcvcnt = rcvcnt + len(resp);
                        imagebuff.extend(resp)
                        if len(resp) == 0:
                            break

                    if True:
                        print 'total rcv byte: %d' % rcvcnt
                    reply = s.recv(10)
                    s.close()
                    myfb.fb_data = bytearray(imagebuff)

                    if len(imagebuff) < myfb.fb_size:
                        continue

                    # convert raw-rgb to image
                    image = Image.frombuffer('RGBA',
                                            (myfb.fb_width, myfb.fb_height),
                                            myfb.fb_data,
                                            'raw',
                                            'RGBA',
                                            0,
                                            1)

                    lcd_w = image.size[0]
                    lcd_h = image.size[1]
                    if DEBUG:
                        print 'LCD size: %d x %d' % (lcd_w,lcd_h)
                    factor_w = 1.00
                    factor_h = 1.00
                    if lcd_w > max_lcd_w:
                        img_w = max_lcd_w
                        factor_w = float(img_w)/float(lcd_w)
                    if lcd_h > max_lcd_h:
                        img_h = max_lcd_h
                        factor_h = float(img_h)/float(lcd_h)
                    factor = min([factor_w, factor_h])
                    self.__img_factor = factor

                    # Keep the rate of w:h
                    img_w = int(lcd_w * factor)
                    img_h = int(lcd_h * factor)
                    if DEBUG:
                        print 'Image size: %d x %d' % (img_w, img_h)

                    # resize image
                    if (factor < 1.00):
                        image = image.resize((img_w, img_h))
                    end3_cpu = time.clock()
                    print "read buf time :%f " %(end3_cpu - end2_cpu)
                    # rotate image
                    if self.__rotate != 0:
                        image = image.rotate(self.__rotate)

                    if self.__lcd != None:
                        try:
                            # save image to local path
                            if DEBUG:
                                refresh_count = refresh_count + 1
                                image_name = 'image_%d.png' % refresh_count
                                image.save(image_name, format='PNG')

                            draw = ImageDraw.Draw(image)
                            draw.text((5, 30), 'read fb time:%f S'%(end3_cpu - end1_cpu),fill = "#ff0000")
                            del draw
                            new_image = ImageTk.PhotoImage(image)

                            self.__im = new_image
                            self.__lcd['image'] = self.__im
                            del image
                            end_cpu = time.clock()
                            print "end time :%f " % (end_cpu - start_cpu)
                        except:
                            continue


# screen windows thread
class mobileco_lcd_update(threading.Thread):
    __tkapp = None
    __root = None

    def __init__(self,root):
        threading.Thread.__init__(self)
        self.thread_stop = False
        self.__tkapp = root
    def run(self):
        if DEBUG:
            print 'run mobileco_lcd'
        #self.__tkapp = LcdApplication(master=self.__root)
        title = 'mobileco '+ __version__+ '-LCD'
        self.__tkapp.master.title(title)
        t = threading.Timer(1, self.__tkapp.updatelcd_sock)
        t.start()
        #self.__tkapp.grid()
        #self.__tkapp.mainloop()
        if DEBUG:
            print 'exit mobileco_lcd mainloop'


    def stop(self):
        if DEBUG:
            print 'stop mobileco_lcd'
        self.thread_stop = True
        if self.__tkapp != None:
            self.__tkapp.stop()
            self.__tkapp.quit()



def show_keypad():
    b_rootTop = tk.Toplevel()
    tkapp = ttkKeypadApplication(master=b_rootTop)

def show_about():
    print "help"
    showinfo(title='帮助',message="联系人:youjin\n联系方式:https://github.com/jinpronet/mobileco")

def sendKey(event):
        print "event"

        print event.widget.winfo_name()
        keyname = event.widget.winfo_name()
        if keyname in keynames:
            sender = send_key_thread(keyname)
            sender.start()

def add_menu(root):
    '''
    make menu for keypad
    '''
    menu_key = tk.Menu(root)
    menu_key.add_command(label="键盘",command = show_keypad )
    menu_key.add_command(label="帮助",command = show_about )
    root.config(menu=menu_key)

def add_button(root):
     #make button
    b_frame = tk.Frame(root,bg ='red')
    b1 = ttk.Button(b_frame,name = "menu",text = "menu")
    b2 = ttk.Button(b_frame,name = "home",text = "home")
    b3 = ttk.Button(b_frame,name = "back",text = "back")
    b1.bind("<Button-1>",sendKey)
    b2.bind("<Button-1>",sendKey)
    b3.bind("<Button-1>",sendKey)
    b1.grid(row = 0,column =0)
    b2.grid(row = 0,column =1)
    b3.grid(row = 0,column =2)
    b_frame.grid()


def mobileco_main():
    b_root = tk.Tk()

    tklcd = LcdApplication(master=b_root)
    add_menu(b_root)
    add_button(b_root)

    #thread for read data from Android
    lcd_thread = mobileco_lcd_update(tklcd)
    lcd_thread.start()

    print "show loop"
    b_root.mainloop()

    #stop=============
    lcd_thread.stop()
    tklcd.stop()

def usage():
    print '--------------------------------------------'
    print 'mobileco %d',__version__
    print 'This is a tool to control Android device via ADB'
    print 'usage: python %s [option]' % sys.argv[0]
    print 'option:'
    print '  --debug    run as debug mode'
    print '  --help    run as debug mode'
    print '  -h    run as debug mode'
    print 'Author : jinrich@126.com'
    print '--------------------------------------------'

if __name__ == '__main__':
    prog_name = sys.argv[0]
    if '--debug' in  sys.argv:
        DEBUG = True

    if ('-h' in sys.argv) or ('--help' in sys.argv):
        usage()
        exit()
    #main function
    mobileco_main()

