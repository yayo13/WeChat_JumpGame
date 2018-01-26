#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import cv2
import time
from algrithm import jump_object

MODE_LIST = ['AUTO', 'STEP']

MODE = MODE_LIST[0]
WINDOW_NAME = 'result'

class wechat_jump(object):
    def __init__(self):
        self._algrithm = jump_object(WINDOW_NAME)
        
        img_name = 'jump.jpg'
        self._cmd_save_img = 'adb -s emulator-5554 \
                        shell screencap -p /sdcard/windows/BstSharedFolder/' + img_name
        self._cmd_jump = 'adb -s emulator-5554 \
                        shell input swipe 300 1500 400 1500 '
        self._path_img = 'E:/BluestacksCN/Engine/ProgramData/UserData/SharedFolder/' + img_name
        
        self._img = 0
        self._timeout = 0
        self._distance = 0
        self._count_jumps = 0
        
        
    def get_img_from_device(self):
        time.sleep(2)
        if os.path.exists(self._path_img):
            os.remove(self._path_img)
        os.popen(self._cmd_save_img)
        print 'android image saved!'
        
        
    def read_img(self):
        self._img = cv2.imread(self._path_img)

        size = self._img.shape
        self._img = cv2.transpose(self._img)
        self._img = cv2.flip(self._img, 0)
        
        
    def calc_timeout(self):
        self._distance, self._timeout = self._algrithm.calc_timeout(self._img)
        
    def jump(self):
        print '####################################'
        print 'distance: %.2f, timeout: %.2f ms'%(self._distance, self._timeout)
        cmd_jump = self._cmd_jump + '%d'%self._timeout
        os.popen(cmd_jump)
        self._count_jumps += 1
        print 'jumps %d !'%self._count_jumps
        print '####################################'
        
def main():
    cv2.namedWindow(WINDOW_NAME)
    jp = wechat_jump()
    while True:
        jp.get_img_from_device()
        jp.read_img()
        jp.calc_timeout()
        
        if MODE == MODE_LIST[0]:
            jp.jump()
            continue
        
        #key = raw_input('press \'j\' to jump, \'q\' to exit, any other key to pass:\n ')
        print 'press \'j\' to jump, \'q\' to exit, any other key to pass:'
        key = cv2.waitKey(0) & 0xff
        if key == ord('j'):
            jp.jump()
        elif key == ord('q'):
            cv2.destroyAllWindows()
            break
            
            
if __name__ == '__main__':
    main()