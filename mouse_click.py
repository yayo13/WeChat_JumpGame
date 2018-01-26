#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import cv2

class mouse(object):
    def __init__(self, window_name):
        self._window_name = window_name
        
        self._count = 0
        self._active_mouse = False
        self._position = [[0,0],[0,0]]

        cv2.setMouseCallback(window_name, self.onMouse)
        

    def update_message(self, image, size_rate, shift):
        self._img = image
        self._size_rate = size_rate 
        self._shift = shift                 # (x_shift, y_shift)


    def activate_mouse(self):
        self._active_mouse = True    
    
    
    def onMouse(self, event, x, y, flags, param):
        if self._active_mouse:
            if event == cv2.EVENT_LBUTTONUP:
                self._position[self._count] = [int(x/self._size_rate+self._shift[0]), \
                                                            int(y/self._size_rate+self._shift[1])]
                cv2.circle(self._img, (x, y), 3, (0,0,255), thickness=-1)
                
                cv2.imshow(self._window_name, self._img)
                cv2.waitKey(1)
                
                self._count += 1
                if self._count > 1:
                    self._active_mouse = False
                    self._count = 0
                    
