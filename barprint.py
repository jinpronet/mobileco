# -*- coding:utf8 -*-
from ctypes import *
import platform

class Barprint:
    '''
    This class for tp printer dll
    '''
    #load dll
    error = False
    dll2 = None
    def __init__(self):
        try:
            if '64bit' in platform.architecture():
                self.dll2 = cdll.LoadLibrary("TSCLIB_x64.dll")
            else:
                print "get x32"
                self.dll2 = cdll.LoadLibrary("TSCLIB.dll")
        except Exception, e:
            print Exception,":",e
            self.error = True

    def print_bar(self,tstr):
        if self.error or tstr == '':
            return
        try:
            self.dll2.openport("Gprinter  GP-3120TL")
        except Exception,e:
            print Exception,":",e
        #对打印机进行设置
        #a 宽度 mm,b高度 mm,c速度 Inch/s，d打印浓度0-15,e传感器类别，f垂直间距gap,f偏移
        self.dll2.setup("30","20","5","8","0","1","0")
        #
        self.dll2.sendcommand("SET CUTTER OFF")
        #设置打印文字方向 1,表示正向
        self.dll2.sendcommand("DIRECTION 1")
        self.dll2.clearbuffer()

        #打印二维码,测试不成功，gp3120TL不支持该方式
        #self.dll2.sendcommand("QRCODE 10,10,H,4,A,0,M1,S7,'123456789012345'")
        #打印条形码
        self.dll2.barcode("1","8","128","60","0","0","2","16",tstr[5:])
        self.dll2.printerfont("6","80","1","0","2","1",tstr[5:])
        #绘制矩形
        #dll2.sendcommand("BOX 50,10,600,280,5")
        #使用windows字体打印,中文字体注意转换为unicode
        str = c_char_p(u"激活码")
        print str.value.decode('gb2312')
        self.dll2.windowsfont(70,110,30,0,0,0,"Arial",str)
        self.dll2.printlabel("1","1")
        self.dll2.closeport()

if  __name__ == "__main__":
    print "test myself "
    c = Barprint()
    c.print_bar("123456789012345")
    print "exit"



