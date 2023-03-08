#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/ArmPi/')
import cv2
import time
import Camera
import threading
from LABConfig import *
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board
from CameraCalibration.CalibrationConfig import *

import rossros as rr
import concurrent.futures



if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)


class ArmSensing():
    """ This class and its methods return the image sensed by the camera
    and its respective filterings"""

    def __init__(self, task):
        self.task = task
        self.my_camera = Camera.Camera()
        self.my_camera.camera_open()
        self.img = self.my_camera.frame

    def mask_image(self):
        self.img = self.my_camera.frame

        if img is not None:
            self.cross_hair()
            frame_lab = self.filter()
            return frame_lab

    def cross_hair(self):
        """Applies CrossHair to image """
        img_h, img_w = self.img.shape[:2]
        cv2.line(img, (0, int(img_h / 2)), (img_w, int(img_h / 2)), (0, 0, 200), 1)
        cv2.line(img, (int(img_w / 2), 0), (int(img_w / 2), img_h), (0, 0, 200), 1)

    def filter(self):
        """Applies filter"""
        frame_resize = cv2.resize(self.img, self.task.size, interpolation=cv2.INTER_NEAREST)
        frame_gb = cv2.GaussianBlur(frame_resize, (11, 11), 11)

        # TODO (line 346) of ColorTracking.py
        if self.get_roi and self.start_pick_up:
            self.get_roi = False
            frame_gb = getMaskROI(frame_gb, roi, size)

        frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)  # convert image to lab space

        return frame_lab


class ArmInterpretation():
    """ This class and its methods return the x,y location of the object"""

    def __init__(self, task):
        self.task = task
        self.area_max = 0
        self.areaMaxContour = 0
        self.rect = None


    def function(self):

        self.area_max = 0
        self.areaMaxContour = 0
        if not self.task.start_pick_up:
            for i in color_range:  #color range comes from LABconfig.py
                if i in self.task.__target_color:
                    detect_color = i

                    # Perform bitwise operations on original image and mask
                    frame_mask = cv2.inRange(frame_lab, color_range[detect_color][0], color_range[detect_color][1])
                    # Open Operation
                    opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((6, 6), np.uint8))
                    # Close Operation
                    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((6, 6), np.uint8))
                    # Find the outline
                    contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]
                    # Find the largest contour
                    self.reaMaxContour, self.area_max = getAreaMaxContour(contours)

            if self.area_max > 2500:
                self.rect = cv2.minAreaRect(areaMaxContour)
                self.box = np.int0(cv2.boxPoints(rect))

                # TODO
                self.roi = getROI(self.box)
                self.get_roi = True

                # Get the coordinates of the center of the block
                img_centerx, img_centery = getCenter(self.rect, self.roi, self.task.size, square_length)
                # Convert to real world coordinates
                world_x, world_y = convertCoordinate(img_centerx, img_centery, size)

                # Draw Contours
                cv2.drawContours(img, [box], -1, range_rgb[detect_color], 2)
                cv2.putText(img, '(' + str(world_x) + ',' + str(world_y) + ')',
                            (min(box[0, 0], box[2, 0]), box[2, 1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, range_rgb[detect_color], 1)  # draw center point


class ArmController():
    """Given the x,y location of an object, the controller takes the object into
    the respective color bin"""

    def __init__(self):


class ArmTask():

    def __init__(self):
        self.count = 0
        self.track = False
        self.roi = ()
        self.get_roi = False
        self.first_move = True
        self.detect_color = 'None'
        self.action_finish = True
        self.start_pick_up = False
        self.start_count_t1 = True
        self.center_list = []

        # General Variables
        self.__isRunning = False
        self.__target_color = ('red')
        self._stop = False

        # Perception Parameters
        self.range_rgb = {
            'red': (0, 0, 255),
            'blue': (255, 0, 0),
            'green': (0, 255, 0),
            'black': (0, 0, 0),
            'white': (255, 255, 255)
        }
        self.size = (640, 480)



        # Actuation Variables
        self.rotation_angle = 0
        self.unreachable = False
        self.world_X, self.world_Y = 0, 0
        self.world_x, self.world_y = 0, 0
        self.last_x, self.last_y = 0, 0


    def reset(self):
        ...
        # TODO



def main():
    """Perception Assignment 1: Set up a simple program that uses this class to identify the location of a block in the pickup
    area and labels it on the video display from the camera."""

    # Instances of Sensor, interpreter and controller


    # Instances of Buses


    # Wrap Sensor, Interpreter and Controller function into RossROS objects


    # Create RossROS Timer Object


    # Concurrent Execution


    # Start Camera
    camera = Camera.Camera()
    camera.camera.open()

    # Loop
    while True:
        # Picture of what the camera is currently looking
        img = camera.frame
        if img is not None:
            frame = img.copy()
            perception = ArmPerception(frame, tar)



if __name__ == '__main__':
    main()