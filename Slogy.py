#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time
from datetime import *
import logging

class Slogy():
    '''
    save log
    '''

    name_fd = None
    lg = None

    def __init__(self,Name="",debug=logging.DEBUG):

        curDate = date.today() - timedelta(days=0)
        if Name == "" :
            Name = "err_"+str(curDate)+".log"
        else:
            Name = Name+"_err_"+str(curDate)+".log"

        LOG_FILE = Name
        #logging class 使用
        handler = logging.FileHandler(LOG_FILE) # 实例化handler
        fmt = '%(asctime)s - %(message)s'

        formatter = logging.Formatter(fmt)   # 实例化formatter
        handler.setFormatter(formatter)      # 为handler添加formatter

        logger = logging.getLogger('tst')    # 获取名为tst的logger
        logger.addHandler(handler)           # 为logger添加handler
        logger.setLevel(logging.DEBUG)
        self.lg = logger

    def logd(self,str):
        self.lg.debug(str)
        pass
    def outp(self,str):
        pass
