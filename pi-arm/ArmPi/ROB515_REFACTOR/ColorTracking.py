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

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

AK = ArmIK()

range_rgb = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}

__target_color = ('red',)

def setTargetColor(target_color):
    """ Set Detection Color"""
    global __target_color

    #print("COLOR", target_color)
    __target_color = target_color
    return (True, ())


def getAreaMaxContour(contours):
    """ Find the contour with the largest area
    parameter is list of contours to compare"""
    contour_area_temp = 0
    contour_area_max = 0
    area_max_contour = None

    # iterate over all contours
    for c in contours:
        contour_area_temp = math.fabs(cv2.contourArea(c))  # Calculate area of contour
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp > 300:  # Only when the area > 300, the contour of the largest area is valid to filter interference
                area_max_contour = c

    return area_max_contour, contour_area_max  # returns largest contour

# the angle at which the gripper closes when griping
servo1 = 500

def initMove():
    """ Initial Position"""
    Board.setBusServoPulse(1, servo1 - 50, 300)
    Board.setBusServoPulse(2, 500, 500)
    AK.setPitchRangeMoving((0, 10, 10), -30, -30, -90, 1500)

def setBuzzer(timer):
    Board.setBuzzer(0)
    Board.setBuzzer(1)
    time.sleep(timer)
    Board.setBuzzer(0)

def set_rgb(color):
    """Set the rgb light color of the expansion board to match the color to be tracked"""
    if color == "red":
        Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(255, 0, 0))
        Board.RGB.show()
    elif color == "green":
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 255, 0))
        Board.RGB.show()
    elif color == "blue":
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 255))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 255))
        Board.RGB.show()
    else:
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
        Board.RGB.show()

count = 0
track = False
_stop = False
get_roi = False
center_list = []
first_move = True
__isRunning = False
detect_color = 'None'
action_finish = True
start_pick_up = False
start_count_t1 = True

def reset():
    """Variable Reset"""
    global count
    global track
    global _stop
    global get_roi
    global first_move
    global center_list
    global __isRunning
    global detect_color
    global action_finish
    global start_pick_up
    global __target_color
    global start_count_t1
    
    count = 0
    _stop = False
    track = False
    get_roi = False
    center_list = []
    first_move = True
    __target_color = ()
    detect_color = 'None'
    action_finish = True
    start_pick_up = False
    start_count_t1 = True

def init():
    """App initialization call"""
    print("ColorTracking Init")
    initMove()

def start():
    """App starts the game call"""

    global __isRunning
    reset()
    __isRunning = True
    print("ColorTracking Start")


def stop():
    """App stops gameplay call"""
    global _stop 
    global __isRunning
    _stop = True
    __isRunning = False
    print("ColorTracking Stop")


def exit():
    """App exits the gameplay call"""
    global _stop
    global __isRunning
    _stop = True
    __isRunning = False
    print("ColorTracking Exit")

rect = None
size = (640, 480)
rotation_angle = 0
unreachable = False
world_X, world_Y = 0, 0
world_x, world_y = 0, 0

def move():
    """Robot arm movement thread"""
    global rect
    global track
    global _stop
    global get_roi
    global unreachable
    global __isRunning
    global detect_color
    global action_finish
    global rotation_angle
    global world_X, world_Y
    global world_x, world_y
    global center_list, count
    global start_pick_up, first_move

    # Placement coordinates of wooden blocks of different colors (x,y,z)
    coordinate = {
        'red':   (-15 + 0.5, 12 - 0.5, 1.5),
        'green': (-15 + 0.5, 6 - 0.5,  1.5),
        'blue':  (-15 + 0.5, 0 - 0.5,  1.5),
    }
    while True:
        if __isRunning:

            # When an object is first detected
            if first_move and start_pick_up:
                action_finish = False
                set_rgb(detect_color)
                setBuzzer(0.1)

                # Do not fill the running time parameter, adaptive running time
                result = AK.setPitchRangeMoving((world_X, world_Y - 2, 5), -90, -90, 0)
                if result == False:
                    unreachable = True
                else:
                    unreachable = False

                # The third time of the return is time
                time.sleep(result[2]/1000)
                start_pick_up = False
                first_move = False
                action_finish = True

            # Object not detected for the first time
            elif not first_move and not unreachable:
                set_rgb(detect_color)
                # If the tracking phase
                if track:
                    # Stop and exit flag detection
                    if not __isRunning:
                        continue
                    AK.setPitchRangeMoving((world_x, world_y - 2, 5), -90, -90, 0, 20)
                    time.sleep(0.02)                    
                    track = False

                # If object hasnt moved for a wile
                if start_pick_up:
                    action_finish = False

                    # Stop and exit flag detection
                    if not __isRunning:
                        continue
                    Board.setBusServoPulse(1, servo1 - 280, 500)  # Paws open
                    # Calculate the angle the gripper needs to rotate
                    servo2_angle = getAngle(world_X, world_Y, rotation_angle)
                    Board.setBusServoPulse(2, servo2_angle, 500)
                    time.sleep(0.8)
                    
                    if not __isRunning:
                        continue
                    AK.setPitchRangeMoving((world_X, world_Y, 2), -90, -90, 0, 1000)  # lower the altitude
                    time.sleep(2)
                    
                    if not __isRunning:
                        continue
                    Board.setBusServoPulse(1, servo1, 500)  # gripper closed
                    time.sleep(1)
                    
                    if not __isRunning:
                        continue
                    Board.setBusServoPulse(2, 500, 500)
                    AK.setPitchRangeMoving((world_X, world_Y, 12), -90, -90, 0, 1000)  # arm raised
                    time.sleep(1)
                    
                    if not __isRunning:
                        continue
                    # Classify and place blocks of different colors
                    result = AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], 12), -90, -90, 0)   
                    time.sleep(result[2]/1000)
                    
                    if not __isRunning:
                        continue
                    servo2_angle = getAngle(coordinate[detect_color][0], coordinate[detect_color][1], -90)
                    Board.setBusServoPulse(2, servo2_angle, 500)
                    time.sleep(0.5)

                    if not __isRunning:
                        continue
                    AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], coordinate[detect_color][2] + 3), -90, -90, 0, 500)
                    time.sleep(0.5)
                    
                    if not __isRunning:
                        continue
                    AK.setPitchRangeMoving((coordinate[detect_color]), -90, -90, 0, 1000)
                    time.sleep(0.8)
                    
                    if not __isRunning:
                        continue
                    Board.setBusServoPulse(1, servo1 - 200, 500)  # Open paws and drop objects
                    time.sleep(0.8)
                    
                    if not __isRunning:
                        continue                    
                    AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], 12), -90, -90, 0, 800)
                    time.sleep(0.8)

                    initMove()  # back to initial position
                    time.sleep(1.5)

                    detect_color = 'None'
                    first_move = True
                    get_roi = False
                    action_finish = True
                    start_pick_up = False
                    set_rgb(detect_color)
                else:
                    time.sleep(0.01)
        else:
            if _stop:
                _stop = False
                Board.setBusServoPulse(1, servo1 - 70, 300)
                time.sleep(0.5)
                Board.setBusServoPulse(2, 500, 500)
                AK.setPitchRangeMoving((0, 10, 10), -30, -30, -90, 1500)
                time.sleep(1.5)
            time.sleep(0.01)

# run child thread
th = threading.Thread(target=move)
th.setDaemon(True)
th.start()

t1 = 0
roi = ()
last_x, last_y = 0, 0
def run(img):
    global roi
    global rect
    global count
    global track
    global get_roi
    global center_list
    global __isRunning
    global unreachable
    global detect_color
    global action_finish
    global rotation_angle
    global last_x, last_y
    global world_X, world_Y
    global world_x, world_y
    global start_count_t1, t1
    global start_pick_up, first_move
    
    img_copy = img.copy()
    img_h, img_w = img.shape[:2]
    cv2.line(img, (0, int(img_h / 2)), (img_w, int(img_h / 2)), (0, 0, 200), 1)
    cv2.line(img, (int(img_w / 2), 0), (int(img_w / 2), img_h), (0, 0, 200), 1)
    
    if not __isRunning:
        return img
     
    frame_resize = cv2.resize(img_copy, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (11, 11), 11)
    # if a recognized object is detected in a certain area, the area will be detected until there is no
    if get_roi and start_pick_up:
        get_roi = False
        frame_gb = getMaskROI(frame_gb, roi, size)    
    
    frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)  # convert image to lab space
    
    area_max = 0
    areaMaxContour = 0
    if not start_pick_up:
        for i in color_range:
            if i in __target_color:
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
                areaMaxContour, area_max = getAreaMaxContour(contours)
        if area_max > 2500:  # Have found the largest area
            rect = cv2.minAreaRect(areaMaxContour)
            box = np.int0(cv2.boxPoints(rect))

            roi = getROI(box) # Get ROI area
            get_roi = True

            # Get the coordinates of the center of the block
            img_centerx, img_centery = getCenter(rect, roi, size, square_length)
            # Convert to real world coordinates
            world_x, world_y = convertCoordinate(img_centerx, img_centery, size)
            
            
            cv2.drawContours(img, [box], -1, range_rgb[detect_color], 2)
            cv2.putText(img, '(' + str(world_x) + ',' + str(world_y) + ')', (min(box[0, 0], box[2, 0]), box[2, 1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, range_rgb[detect_color], 1) # draw center point
            # Compare the last coordinates to determine whether to move
            distance = math.sqrt(pow(world_x - last_x, 2) + pow(world_y - last_y, 2))
            last_x, last_y = world_x, world_y
            track = True
            #print(count,distance)
            # Cumulative judgement
            if action_finish:
                if distance < 0.3:
                    center_list.extend((world_x, world_y))
                    count += 1
                    if start_count_t1:
                        start_count_t1 = False
                        t1 = time.time()
                    if time.time() - t1 > 1.5:
                        rotation_angle = rect[2]
                        start_count_t1 = True
                        world_X, world_Y = np.mean(np.array(center_list).reshape(count, 2), axis=0)
                        count = 0
                        center_list = []
                        start_pick_up = True
                else:
                    t1 = time.time()
                    start_count_t1 = True
                    count = 0
                    center_list = []
    return img

if __name__ == '__main__':
    init()
    start()
    __target_color = ('red', )
    my_camera = Camera.Camera()
    my_camera.camera_open()
    while True:
        img = my_camera.frame
        if img is not None:
            frame = img.copy()
            Frame = run(frame)           
            cv2.imshow('Frame', Frame)
            key = cv2.waitKey(1)
            if key == 27:
                break
    my_camera.camera_close()
    cv2.destroyAllWindows()
