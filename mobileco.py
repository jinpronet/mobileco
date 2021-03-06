#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Android Mobileco 0.5
# This is a free software under GPL.
#
# Author: youjin
# Bug report: jinrich@126.com
# ---------------------------------------------------------------------------

__author__ = 'youjin'
__version__ = '0.8'

import subprocess,os
import threading
import socket,sys
import time
import Slogy

import AdbUnit
import qrcode
from barprint import *

try:
    import Tkinter as tk
    import ttk
    from ScrolledText import ScrolledText
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

glog = None

# A global var for control thread exit ok
gexit = False

gevent = threading.Event()

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
              17, 7,18,
            ]


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


class send_key_thread(threading.Thread):
    """
    This class for send key to adb mobile
    """
    __tkapp = None
    __root = None
    __key = None
    adb = None
    log = None
    def __init__(self, key):
        """
        This init nend a key for send,detail in keynames list
        """
        self.log = Slogy.Slogy("mobileco")
        self.log.logd("send_key_thread init")
        threading.Thread.__init__(self)
        self.thread_stop = False
        self.__key = key
        self.adb = AdbUnit.AdbUnit()

    def sendKey(self):
        """
        Find a keyname and transfor to sacn code ,then send it by adb
        """
        self.log.logd('send_key: %s' % self.__key)
        if self.__key in keynames:
            if self.adb.device_exist():
                if self.__key != 'none':
                    self.adb.adbshellcommand('input keyevent %s' % str(keyvalues[keynames.index(self.__key)]))
        else :
            if self.adb.device_exist():
                if self.__key != "none":
                    self.adb.adbshellcommand('input keyevent %s' % (self.__key).upper())
                    print 'input keyevent %s' % (self.__key).upper()

    def run(self):
        self.log.logd('send_key_thread run')
        self.sendKey()

    def stop(self):
        self.log.logd('stop send_key_thread')
        self.thread_stop = True

class ttkTestApplication(ttk.Frame):
    """
    This class for design a Test Pad
    """
    _adb = None
    _entry = None
    _text = None

    def __init__(self, master=None):
        self._adb = AdbUnit.AdbUnit()
        ttk.Frame.__init__(self, master, class_='ttktestApplication')

        #Set the windows title
        title = 'mobileco '+ __version__+ '-Test'
        self.master.title(title)
        self.create_test()

        #Set the pad position
        master.geometry("+%d+%d" % (300, 200))
        self.grid()

    def create_test(self):
        """
        Build widgets for pad
        """

        #add test button
        cl = 0
        for bn in ['enginner','gps','validation','test','catlog','setting']:
            g_button = ttk.Button(self,name = bn,text = bn)
            g_button.bind('<ButtonRelease-1>', self._test_func)
            g_button.grid(row = 0,column = cl)
            cl +=1
        #add command line
        t = ttk.Label(self,text = "命令：")
        t.grid(row = 1,column = 0)
        self._entry = ttk.Entry(self,width = 25)
        self._entry.grid(row = 1,column = 1,columnspan=cl-1)
        self._entry.bind("<Return>",self.get_cmd)

        self._text = ScrolledText(self,width = cl*10,height = 20)
        self._text.grid(row = 2,column =0,columnspan =cl)
        self.master.bind('<Configure>',self.resize)

        pass

    def get_cmd(self,event):
        """
        Get the Entry text for cmd ,And send to mobile
        """

        str_cmd = event.widget.get()
        self.show_respon("youjin# "+ str_cmd + '\n')
        self._entry.delete('0','end')
        self._entry.update()
        rep = self._adb.adbshellcommand(str_cmd)

        if rep is None:
            rep = "more than one device and emulator"
        self.show_respon("adb#"+ rep )
        self._text.configure(width = 50,height = 30)

    def show_respon(self,str):
        """
        Place the text in a Text widget for show
        """
        self._text.insert('end',str)
        self._text.yview_moveto(1)
        pass

    def _test_func(self,event):
        """
        implement the Fix button widget function
        """
        bn =  event.widget.winfo_name()
        print bn

        cmd = "none"
        if bn == "enginner":
            cmd = "am start -n  com.sprd.engineermode/.EngineerModeActivity"
            pass
        elif bn == "gps":
            cmd = "am start -n com.spreadtrum.sgps/.SgpsActivity"
            pass
        elif bn == "validation":
            cmd = "am start -n com.sprd.validationtools/.ValidationToolsMainActivity"
            pass
        elif bn == "test":
            cmd = "input keyevent 60;am force-stop test.zhlt.g1;am start -n test.zhlt.g1/.TestActivity"
            pass
        elif bn == "catlog":
            cmd = "cat /sdcard/test.log"
            pass
        elif bn == "setting":
            cmd = "am start -n com.android.settings/com.android.settings.Settings"
            pass
        if self._adb.device_exist():
            self.show_respon(cmd)
            rep =  self._adb.adbshellcommand(cmd)
            self.show_respon(rep)
        pass

    def resize(self,event):
        print event.width,' ',event.height

        pass


class ttkKeypadApplication(ttk.Frame):
    """
    Kaypad Tkinter-Based GUI application
    """
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master, class_='ttkKeypadApplication')
        title = 'mobileco '+ __version__+ '-Keypad'
        self.master.title(title)
        self.createkeypad()
        self.grid()

    def createkeypad(self):
        """
        creat buttons from keymap with 4 buttons each row
        """
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


    def sendKey(self, event=None):
        keyname = event.widget.winfo_name()
        if keyname in keynames:
            sender = send_key_thread(keyname)
            sender.start()


class LcdApplication(tk.Frame):
    """
    LCD Tkinter-Based GUI application
    """
    __img_factor = 1.00 # image resize rate
    __lcd = None # the label widget
    __keepupdate = True # control the socket update while
    __im = None # cache the lable backimage
    __imsc = None # copy the socket update image for show
    __rotate = 0 # rotate the image for show

    __screen = None
    # record mouse start & end point location
    __start = [0, 0]
    __end = [0, 0]
    __master= None

    #recod the cricle for show mouse click
    mx = 0
    my = 0
    mx1 = 0
    my1 = 0
    swip = False

    log = None # the log instanse
    adb = None # the adb Unit

    def __init__(self, master,glog):
        """
        should have master and glog
        """
        self.log = glog
        self.adb = AdbUnit.AdbUnit()

        tk.Frame.__init__(self, master, class_='LcdApplication')
        self.__master = master
        self.__rotate = 0
        self.createlcd()
        self.grid()

    def createlcd(self):
        # creat label as lcd
        self.log.logd( 'LcdApplication: createlcd')

        # make default image display on label
        image = Image.new(mode = 'RGB', size = (320, 320), color = '#000000')
        self.screen = image
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


    def rightclick_label(self, event=None):
        """
        To serve right click on label widget
        """
        self.log.logd('Type: %s' % event.type)
        self.__rotate = (self.__rotate + 90) % 360
        self.log.logi("rotate: %d" % self.__rotate)


    def click_label(self, event=None):
        """
        To serve left click on label widget
        """
        global gevent
        self.log.logd('Type: %s' % event.type)
        if event.type == '4':
            # record mouse left button down
            self.log.logd('Click at: (%d, %d)' % (event.x, event.y))
            self.__start[0] = int(float(event.x) / float(self.__img_factor))
            self.__start[1] = int(float(event.y) / float(self.__img_factor))
            self.__end = None
        elif event.type == '5':
            # record mouse left button up
            self.log.logd('Release at: (%d, %d)' % (event.x, event.y))
            self.__end = [0, 0]
            self.__end[0] = int(float(event.x) / float(self.__img_factor))
            self.__end[1] = int(float(event.y) / float(self.__img_factor))

        # Do not report touch event during mouse down
        if self.__end == None:
            return

        if abs(self.__start[0] - self.__end[0]) < 2 and \
          abs(self.__start[1] - self.__end[1]) < 2 :
            # mouse action: tap
            self.adb.send_touch_event('tap', self.__start[0], self.__start[1])
            self.mx = int(self.__start[0]*float(self.__img_factor))
            self.my = int(self.__start[1]*float(self.__img_factor))
            self.swip = False
        else:
            # mouse action: swipe
            self.adb.send_touch_event('swipe', self.__start[0], self.__start[1], self.__end[0], self.__end[1])
            self.mx = int(self.__start[0]*float(self.__img_factor))
            self.my = int(self.__start[1]*float(self.__img_factor))
            self.mx1 = int(self.__end[0]*float(self.__img_factor))
            self.my1 = int(self.__end[1]*float(self.__img_factor))
            self.swip = True

        gevent.set()



    def stop(self):
        self.log.logd('LcdApplication: stop')
        self.__keepupdate = False

        global gevent
        gevent.set()

    def update_screen(self):
        """
        update screen for event
        """
        while self.__keepupdate:
            global gevent
            gevent.wait()

            global gexit
            if gexit:
                break
            if self.__imsc == None:
                break
            draw = ImageDraw.Draw(self.__imsc)
            if self.swip:
                draw.line((self.mx,self.my,self.mx1,self.my1),fill = 'red',width = 2)
            else:
                draw.ellipse((self.mx-10,self.my-10, self.mx+10, self.my+10), outline ='red')
            #draw.text((30,30),"hell",fill='red')
            del draw
            new_image = ImageTk.PhotoImage(self.__imsc)
            #print "update_screen"
            self.__lcd['image'] = new_image
            gevent.clear()


        print "update_screen thread exit"
        pass

    def updatelcd_sock(self):
        """
        get the image from the socket with adb
        """
        self.log.logd( 'LcdApplication: updatelcd_sock')
        # Max display area size on label widget
        # We Must set if the area size less than screen of mobile
        max_lcd_w = 1024
        max_lcd_h = 600
        #max_lcd_w = 1440
        #max_lcd_h = 720


        dev_sn = ''
        hdrsize = 0
        myfb = fb()
        refresh_count = 0 # record refresh count

        while self.__keepupdate:

            start_cpu = time.clock()
            # Get device SerialNumber from ADB server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect(('127.0.0.1', 5037))
            except:
                os.system('adb start-server')
                time.sleep(2)
                s.close()
                continue

            req_msg = 'host:devices'
            s.sendall('%04x' % len(req_msg))
            s.sendall(req_msg)
            if self.adb.readAdbResponse(s):
                len_str = s.recv(4)
                if len(len_str) < 4:
                    continue
                length = int(len_str, 16)
                dev_info = s.recv(length)
                if '\t' in dev_info:
                    dev_sn = dev_info[0:dev_info.index('\t')]
                else:
                    dev_sn = ''
                self.log.logd('dev serial: %s' % dev_sn)
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
            if not self.adb.readAdbResponse(s):
                s.close()
            else:
                if DEBUG:
                    print 'ready to transport'
                req_msg = 'framebuffer:'
                s.sendall('%04x' % len(req_msg))
                s.sendall(req_msg)
                if not self.adb.readAdbResponse(s):
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
                    self.log.logd('fb header size: %d' % hdrsize)

                    # read the header
                    header = s.recv(hdrsize * 4)
                    if len(header) < (hdrsize * 4):
                        continue

                    self.adb.hexdump(bytearray(header))
                    self.adb.readHeader(myfb, fbver, header)
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
                    #print "end1 time :%f " % (end1_cpu - start_cpu)
                    # read fb buffer
                    rcvcnt = 0
                    imagebuff = []
                    #print "begin read fb time :%f " % (end2_cpu - end1_cpu)
                    #print "fb_size :%d " % myfb.fb_size

                    while True:
                        if rcvcnt < myfb.fb_size:
                            readbyte = myfb.fb_size - rcvcnt
                        else:
                            break
                        resp = s.recv(readbyte)
                        if DEBUG:
                            print 'read byte: %d' % len(resp)
                        rcvcnt += len(resp)
                        imagebuff.extend(resp)
                        if len(resp) == 0:
                            break

                    self.log.logd('total rcv byte: %d' % rcvcnt)
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
                    self.log.logd('LCD size: %d x %d' % (lcd_w,lcd_h))
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
                    self.log.logd('Image size: %d x %d' % (img_w, img_h))
                    # resize image
                    if factor < 1.00:
                        image = image.resize((img_w, img_h))
                    end3_cpu = time.clock()

                    # rotate image
                    if self.__rotate != 0:
                        image = image.rotate(self.__rotate)

                    if self.__lcd is not None:
                        try:
                            # save image to local path
                            if DEBUG:
                                refresh_count += 1
                                image_name = 'image/image_%d.png' % refresh_count
                                image.save(image_name, format='PNG')

                            draw = ImageDraw.Draw(image)
                            draw.text((5, 30), 'Fbps:%f S'%(end3_cpu - end1_cpu),fill = "#ff0000")
                            draw.text((5,40),'USB Speed:%f MB/s '%(((myfb.fb_size)/(1024*1024))/(end3_cpu - end1_cpu)),fill = "#ff0000")

                            new_image = image.copy()
                            new_image1 = ImageTk.PhotoImage(new_image)

                            self.__imsc = new_image
                            self.__im = new_image1


                            global gevent
                            gevent.set()

                        except:
                            continue



class mobileco_lcd_update(threading.Thread):
    """
    Thread for start the screen update
    """
    __tkapp = None
    __root = None
    global gevent
    def __init__(self,root):
        threading.Thread.__init__(self)
        self.thread_stop = False
        self.__tkapp = root
    def run(self):

        title = 'mobileco '+ __version__+ '-LCD'
        self.__tkapp.master.title(title)
        t = threading.Timer(1, self.__tkapp.updatelcd_sock)
        t.start()

        self.__tkapp.update_screen()

        print 'exit mobileco_lcd_update '


    def stop(self):
        print 'stop mobileco_lcd'
        self.thread_stop = True
        if self.__tkapp != None:
            self.__tkapp.stop()
            self.__tkapp.quit()


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

class mobileco:
    global glog
    gresult=None
    def __init__(self,debug = False):
        if debug:
            self.glog = Slogy.Slogy("mobileco",debug = True)
        else:
            self.glog = Slogy.Slogy("mobileco")
        self.gresult = Slogy.Result("IMEI")
        pass
    def printkey(self,event):
        print event.char
        print event.keycode
        self.sendKey_int(event.keycode)

    def mobileco_main(self):
        b_root = tk.Tk()
        tklcd = LcdApplication(master=b_root,glog=self.glog)

        self.add_menu(b_root)
        self.add_button(b_root)
        #b_root.bind('<Key>', self.printkey)
        #thread for read data from Android
        lcd_thread = mobileco_lcd_update(tklcd)
        lcd_thread.start()

        self.glog.loge("show loop")
        b_root.mainloop()


        #stop=============
        global gexit
        gexit = True

        # Make sure stop First for None Resource
        time.sleep(1)
        # Stop lcd screen update thread
        lcd_thread.stop()

        #stop the
        tklcd.stop()

    def add_menu(self,root):
        '''
        make menu for keypad
        '''
        menu_key = tk.Menu(root)
        menu_key.add_command(label="键盘",command = self.show_keypad )
        menu_key.add_command(label="测试",command = self.show_test )
        menu_key.add_command(label="打印IMEI",command = self.pull_file )
        menu_key.add_command(label="帮助",command = self.show_about )
        root.config(menu=menu_key)

    def add_button(self,root):
         #make button
        b_frame = tk.Frame(root,bg ='red')
        b1 = ttk.Button(b_frame,name = "menu",text = "menu")
        b2 = ttk.Button(b_frame,name = "home",text = "home")
        b3 = ttk.Button(b_frame,name = "back",text = "back")
        b4 = ttk.Button(b_frame,name = "power",text = "power")
        b1.bind("<Button-1>",self.sendKey)
        b2.bind("<Button-1>",self.sendKey)
        b3.bind("<Button-1>",self.sendKey)
        b4.bind("<Button-1>",self.sendKey)
        b1.grid(row = 0,column =0)
        b2.grid(row = 0,column =1)
        b3.grid(row = 0,column =2)
        b4.grid(row = 0,column =3)

        b_frame.grid()

    def show_keypad(self):
        b_rootTop = tk.Toplevel()
        tkapp = ttkKeypadApplication(master=b_rootTop)

    def show_test(self):
        b_rootTop = tk.Toplevel()
        tkapp = ttkTestApplication(master=b_rootTop)

    def show_about(self):
        print "help"
        showinfo(title='帮助',message="联系人:youjin\n联系方式:https://github.com/jinpronet/mobileco")

    def get_imei2(self):
        ''''
        This is a method for get imei with adb shell getprop
        '''
        imei = ''
        adbtool = AdbUnit.AdbUnit()
        imei = adbtool.adbshellcommand("getprop persist.support.test.imei")
        print imei
        return imei

        pass
    def get_imei(self):
        ''''
        This is a method for get imei with adb pull
        '''
        os.system("adb pull /sdcard/test.log .")
        try:
            f = open('test.log')
        except IOError:
            print IOError
            showwarning("ERROR!","No Test Result Data Get\nCheck The USB or Device")
            return -1
        while True:
            line = f.readline()
            if line:
                pass
                content = line.replace('\n','')
                test1 =content.split(":")[1]
                test2 = content.split(":")[0]
                if test2.find("IMEI")!=-1:
                    pass
                    deviceimei = test1
                    print deviceimei
                    # qr = qrcode.QRCode(
                    # version=2,
                    #  error_correction=qrcode.constants.ERROR_CORRECT_L,
                    #  box_size=10,
                    #  border=1
                    # )
                    # qr.add_data(deviceimei)
                    # qr.make(fit=True)
                    # img = qr.make_image()
                    # img.save("image/"+deviceimei+".png")

                    self.gresult.save("IMEI:"+deviceimei)
                else:
                    print test1
            else:
                print "break"
                break
        f.close()
        return deviceimei
        pass

    def show_warn(self,strwarn):
        strwarn = str(strwarn)
        showwarning(title="WARN",message=strwarn)

    def print_imei(self):
        deviceimei = self.get_imei2()
        print "["+deviceimei+"]"
        if deviceimei.lstrip() != "":
            c = Barprint()
            c.print_bar(deviceimei,"2")
        else:
            self.glog.loge( "No IMEI Get ")
        pass


    def pull_file(self):
        threading.Thread(target=self.print_imei).start()

    def sendKey_int(self,key):
        print "key:"+str(key)
        send_key_thread(str(key))

    def sendKey(self,event):
            print "event"

            print event.widget.winfo_name()
            keyname = event.widget.winfo_name()
            if keyname in keynames or keyname == "power":
                sender = send_key_thread(keyname)
                sender.start()
    def __del__(self):
        self.gresult.close()



if __name__ == '__main__':
    prog_name = sys.argv[0]

    if '--debug' in  sys.argv:
        DEBUG = True

    #init the mobileco and log object
    mob = mobileco(DEBUG)

    #if run as command , and with help ,show the help message
    if ('-h' in sys.argv) or ('--help' in sys.argv):
        usage()
        exit()

    #main function start
    mob.mobileco_main()

    #run end
    sys.exit()

