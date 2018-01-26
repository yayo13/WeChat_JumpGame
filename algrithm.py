#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import cv2
import copy
import math
import numpy as np
from mouse_click import mouse
import pdb

class jump_object(object):
    def __init__(self, window_name):
        # image size: 1600*900
        self._roi = (300, 0, 1480, 900)             # y_start, x_start, y_end, x_end
        self._point_background = (425, 61)      # position
        self._distance_max_box = 200
        self._bgr_background = [0, 0, 0]           
        self._bgr_human = (64, 52, 51)
        self._hue_human = (100, 140)        

        self._tolerate_background = 36                       # distance
        self._tolerate_human = 36                              # distance
        self._human_top_shift = 165
        self._human_center_shift = 138
        self._top_corner_shift = 4                               # y-shift

        self._distance2time = 1.67 #1.35                    # ms
        self._window_name = window_name
        self._show_rate = 0.5
        
        self._bgr_img = 0
        self._hue_img = 0
        self._next_pos = list()
        self._now_pos = list()
        
        self._mouse = mouse(window_name)
        self.create_filter()

    
    def extract_background(self):
        self._bgr_background = self._bgr_img[self._point_background[1], self._point_background[0], :]
        
        
    def create_filter(self):
        '''
        00011111000
        '''
        self._filter = np.zeros((1,11), dtype=np.uint8)
        for i in range(3, 7):
            self._filter[0, i] = 1
        
    
    def compare_array(self, array_mask, array_set, standard, tolerate, condition):
        '''
        array_mask.shape == array_set.shape == (M, N, 3)
        standard == (b, g, r)
        tolerate == float, distance
        condition == ('close', 'open')
        '''
        result = cv2.cvtColor(array_set, cv2.COLOR_BGR2GRAY)
        
        for i in range(array_mask.shape[0]):
            for j in range(array_mask.shape[1]):
                distance = math.sqrt(math.pow(float(array_mask[i, j, 0])-standard[0],2) + \
                                                 math.pow(float(array_mask[i, j, 1])-standard[1],2) + \
                                                 math.pow(float(array_mask[i, j, 2])-standard[2],2))
                if distance <= tolerate:
                    result[i, j] = 0 if condition == 'close' else 255
                else:
                    result[i, j] = 255 if condition == 'close' else 0
        return result
        
        
    def locate_next_box(self, foreground):
        # find top corner
        is_find = False
        for row in range(foreground.shape[0]):
            statistic = np.zeros((1, foreground.shape[1]), dtype=np.uint8)
            for col in range(5, foreground.shape[1]-5-1):
                sum_value = 0
                for index in range(11):
                    sum_value += self._filter[0, index] * foreground[row,col-5+index]
                statistic[0,col] = sum_value
            
            maxvalue = np.max(statistic)
            if maxvalue >= 1:
                x = np.where(statistic == maxvalue)[1][0] + 5
                top_corner = (x, row)
                
                # distance to human
                value = self._bgr_img[row, x, :]
                distance_human = math.sqrt(math.pow(float(value[0])-self._bgr_human[0],2) + \
                                             math.pow(float(value[1])-self._bgr_human[1],2) + \
                                             math.pow(float(value[2])-self._bgr_human[2],2))
                if distance_human > self._tolerate_human:
                    is_find = True
                    break
        if not is_find:
            # failed
            return False
            
        # locate box center
        bgr_box = self._bgr_img[top_corner[1]+self._top_corner_shift, top_corner[0], :]
        vec_point = [0, 0]
        count = 0
        
        y_end = min(top_corner[1]+self._distance_max_box, foreground.shape[0])
        x_start = max(0, top_corner[0]-self._distance_max_box)
        x_end = min(top_corner[0]+self._distance_max_box, foreground.shape[1])
        for row in range(top_corner[1], y_end):
            for col in range(x_start, x_end):
                if self._bgr_img[row,col,0] == bgr_box[0] and \
                   self._bgr_img[row,col,1] == bgr_box[1] and \
                   self._bgr_img[row,col,2] == bgr_box[2]:
                    vec_point[0] += col
                    vec_point[1] += row
                    count += 1
        if count > 0:
            vec_point[0] /= count
            vec_point[1] /= count
        
            self._next_pos = [int(vec_point[0]), int(vec_point[1])]
            return True
        return False
    
    
    def locate_human(self, foreground):
        # filter by hue
        filted = np.zeros(self._hue_img.shape, dtype=np.uint8)
        for row in range(self._hue_img.shape[0]):
            for col in range(self._hue_img.shape[1]):
                if self._hue_img[row, col] >= self._hue_human[0] and \
                   self._hue_img[row,col] <= self._hue_human[1]:
                    if foreground[row,col] == 255:
                        filted[row,col] = 255

        circles = cv2.HoughCircles(filted, cv2.cv.CV_HOUGH_GRADIENT, 1, 100, \
                                                param1=200, param2=15, minRadius=20, maxRadius=30)[0]
        if len(circles) > 0:
            # sucess
            self._now_pos = [int(circles[0][0]), int(circles[0][1]+self._human_center_shift)]
            return True
        else:
            # another method
            vec_point = [0,0]
            count = 0
            to_break = False
            for row in range(foreground.shape[0]):
                for col in range(foreground.shape[1]):
                    distance = math.sqrt(math.pow(float(self._bgr_img[row, col, 0])-self._bgr_human[0],2) + \
                                                 math.pow(float(self._bgr_img[row, col, 1])-self._bgr_human[1],2) + \
                                                 math.pow(float(self._bgr_img[row, col, 2])-self._bgr_human[2],2))
                    if distance <= self._tolerate_human:
                        # in bgr range
                        if self._hue_img[row, col] >= self._hue_human[0] and \
                           self._hue_img[row,col] <= self._hue_human[1]:
                           # in hue range
                            vec_point[0] += col
                            vec_point[1] += row
                            count += 1
                            to_break = True
                if to_break:
                    vec_point[0] /= count
                    vec_point[1] /= count
                    break
            if count < 1:
                # failed
                return False
                
            self._now_pos = [int(vec_point[0]), int(vec_point[1]+self._human_top_shift)]
        return True
         
       
    def show_image(self):
        # remap to whole image
        self._next_pos[0] += self._roi[1]
        self._next_pos[1] += self._roi[0]
        self._now_pos[0] += self._roi[1]
        self._now_pos[1] += self._roi[0]
        
        self._next_pos[0] = int(self._next_pos[0] * self._show_rate)
        self._next_pos[1] = int(self._next_pos[1] * self._show_rate)
        self._now_pos[0] = int(self._now_pos[0] * self._show_rate)
        self._now_pos[1] = int(self._now_pos[1] * self._show_rate)
        
        # draw
        cv2.circle(self._to_show, tuple(self._next_pos), 3, (0,0,255), -1)
        cv2.circle(self._to_show, tuple(self._now_pos), 3, (0,255,0), -1)
        cv2.line(self._to_show, tuple(self._next_pos), tuple(self._now_pos), (255,0,0), thickness=2)
        
        # show
        cv2.imshow(self._window_name, self._to_show)
        cv2.waitKey(1)
    
    
    def calc_timeout(self, image):
        self._bgr_img = image[self._roi[0]:self._roi[2], self._roi[1]:self._roi[3], :]
        self._hue_img = cv2.cvtColor(self._bgr_img, cv2.COLOR_BGR2HSV)[:,:,0]
        self._to_show = cv2.resize(image, (int(image.shape[1]*self._show_rate), int(image.shape[0]*self._show_rate)))
        cv2.imshow(self._window_name, self._to_show)
        cv2.waitKey(1)

        self.extract_background()
        mask_foreground = self.compare_array(self._bgr_img, self._bgr_img, self._bgr_background, self._tolerate_background, 'close')      
        
        # auto mode
        auto_mode = True
        while True:
            if not self.locate_next_box(mask_foreground):
                auto_mode = False
                break
            if not self.locate_human(mask_foreground):
                auto_mode = False
                break
            break
            
        # manual mode
        if not auto_mode:
            print 'Failed to locate human or box, choose them by mouse orderly...'
            self._mouse.update_message(self._to_show, self._show_rate, (-self._roi[1], -self._roi[0]))
            self._mouse.activate_mouse()
            while self._mouse._active_mouse:
                cv2.waitKey(1)
            self._now_pos = self._mouse._position[0]
            self._next_pos = self._mouse._position[1]
                
        distance = math.sqrt(math.pow(self._next_pos[0]-self._now_pos[0], 2) +\
                                         math.pow(self._next_pos[1]-self._now_pos[1], 2))
                                         
        timeout = distance * self._distance2time
        self.show_image()
        return distance, timeout
        #cv2.imwrite('po.jpg', po)
        #cv2.imwrite('hu.jpg', mask_human)