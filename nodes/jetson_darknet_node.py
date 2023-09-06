#!/usr/bin/env python

import sys
import rospy
import math
import Jetson.GPIO as GPIO

from time import sleep
from darknet_ros_msgs.msg import BoundingBoxes

from oled_handler import OledHandler
from lamp_handler import LampHandler
from lamp_handler import Color, LampState, Lamp

class Detector:
    def __init__(self):
        self.is_ready = False 
        self.is_detected = False
        self.alarm_started = False
        self.alarm_count = 0

class BoxDetected:
    def __init__(self):
        self.time_last = 0
        self.width = 0
        self.height = 0
        self.x = 0
        self.y = 0
        self.count = 0
    def reset(self):
        self.time_last = 0
        self.width = 0
        self.height = 0
        self.x = 0
        self.y = 0
        self.count = 0

class JetsonDarknetNode:
    
    def __init__(self):
        self.timer = 0
        self.oled = OledHandler()
        #self.lamp = LampHandler()
        self.detector = Detector()
        self.box = BoxDetected()
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        self.lamp_red = Lamp(Color.RED, 11)
        self.lamp_grn = Lamp(Color.RED, 15)
        self.lamp_buz = Lamp(Color.RED, 12)
        self.led_onboard = Lamp(Color.RED, 18)

        rospy.Subscriber("/darknet_ros/bounding_boxes", BoundingBoxes, self.sub_boundingBoxes, queue_size=10)
        rospy.Timer(rospy.Duration(0.01), self.update_timer)
        self.timer1 = 0
        self.grn_timer = 0
        
        rate = rospy.Rate(5) # 5hz
        self.oled.WriteLine(0, "YOLO Standby")
        self.lamp_grn.On()
        #self.lamp.SetState(Color.GRN, LampState.ON)
        
        #self.lamp_red.On()
        while not rospy.is_shutdown():
            self.led_onboard.Toggle()
            self.oled.Update()
            #self.lamp.Update_5Hz()
            if self.detector.alarm_started == True:
                self.detector.alarm_count += 1
                if self.detector.alarm_count < 60:
                    self.lamp_red.Toggle()
                else:
                    self.detector.alarm_started = False
                    self.lamp_grn.On()
                    self.lamp_red.Off()
                    self.lamp_buz.Off()
            else:
                self.grn_timer += 1
                if self.grn_timer > 5:
                    self.lamp_grn.Toggle()
                    self.grn_timer = 0
            rate.sleep()
        GPIO.output(11, GPIO.LOW)
        GPIO.output(12, GPIO.LOW)
        GPIO.output(15, GPIO.LOW)

    def sub_boundingBoxes(self, bb_msg):
        bb_cnt = 0
        bb_found = False
        if not self.detector.is_ready:
            self.oled.WriteLine(0, "YOLO Ready")
            self.detector.is_ready = True
            self.lamp_red.Off()
            self.lamp_grn.On()
            #self.lamp.SetState(Color.RED, LampState.OFF)
            #self.lamp.SetState(Color.GRN, LampState.BLINK)
        for box in bb_msg.bounding_boxes:
            bb_cnt += 1
            if box.Class == "no_cover":
                bb_found = True
                width = box.xmax - box.xmin
                height = box.ymax - box.ymin
                posX = box.xmin + width/2
                posY = box.ymin + height/2
                # Do some filtering here
                if width > 130 and width < 200 and height > 60 and height < 150:
                    if self.box.time_last == 0:
                        self.box.time_last = self.timer1
                    else:
                        gap = self.timer1 - self.box.time_last
                        print("Time from last {}".format(gap))
                        if self.timer1 - self.box.time_last < 25:
                            self.box.time_last = self.timer1
                            self.box.count += 1
                            if self.box.count > 1:
                                if not self.detector.is_detected:
                                    self.detector.is_detected = True
                                    self.detector.alarm_started = True
                                    self.detector.alarm_count = 0
                                    self.lamp_red.On()
                                    self.lamp_buz.On()
                                    self.lamp_grn.Off()
                                    #self.lamp.SetState(Color.GRN, LampState.OFF)
                                    #self.lamp.SetState(Color.RED, LampState.BLINK)
                                    #self.lamp.SetState(Color.BUZZER, LampState.ON)
                                txt = "ERR: X{},Y{}, W:{},H:{}".format(posX, posY, width, height)
                                self.oled.WriteLine(1, txt)
                                rospy.loginfo(
                                    "X: {}, Y: {} Width: {}, Height: {}".format(
                                    box.xmin, box.ymin, width, height
                                    )
                                )
        txt2 = "Detected {}".format(bb_cnt)
        self.oled.WriteLine(2, txt2)
        if not bb_found:
            if self.detector.is_detected:
                self.detector.is_detected = False
            else:
                #print("Timeout:{}".format(self.timer1-self.box.time_last))
                if (self.timer1 - self.box.time_last)>200 :                    
                    self.box.reset()
		            #self.lamp_red.Off()
		            #self.lamp_grn.On()
		            #self.lamp_buz.Off()
                    #self.lamp.SetState(Color.GRN, LampState.BLINK)
                    #self.lamp.SetState(Color.RED, LampState.OFF)
                    #self.lamp.SetState(Color.BUZZER, LampState.OFF)
            self.oled.WriteLine(1,"Pass")

    def update_timer(self, event):
        self.timer1+=1

    def main(self):
        rospy.spin()

if __name__ == '__main__':
    try :
        rospy.init_node('jetson_darknet_node')
        node = JetsonDarknetNode()
        node.main()
    except rospy.ROSInterruptException:
        pass
