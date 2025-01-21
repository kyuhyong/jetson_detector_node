#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import rospy
import math
import Jetson.GPIO as GPIO

from time import sleep
from darknet_ros_msgs.msg import BoundingBoxes
from sensor_msgs.msg import Image

from oled_handler import OledHandler
from lamp_handler import LampHandler
from lamp_handler import Color, LampState, Lamp
import threading

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
        self.bb_watchdog = 0
        self.bb_timeout = False
        self.oled = OledHandler()

        self.detector = Detector()
        self.box = BoxDetected()
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        self.lamp_red = Lamp(Color.RED, 11)
        self.lamp_grn = Lamp(Color.RED, 15)
        self.lamp_buz = Lamp(Color.RED, 12)
        self.led_onboard = Lamp(Color.RED, 18)
        GPIO.setup(16, GPIO.OUT)    #ADDED FOR RELAY
        GPIO.output(16, GPIO.LOW)   #ADDED FOR RELAY
        self.relay_state = 0        #ADDED FOR RELAY
        self.relay_delay_cnt = 0    #ADDED FOR RELAY
        self.relay_on_delay = 30  #RELAY ON DELAY 1/10 seconds
        self.relay_off_delay = 30    #RELAY OFF DELAY 1/10 seconds
        self.lock = threading.Lock()  # 스레드 락 추가
        self.timer1 = 0
        self.grn_timer = 0
        
        rospy.Subscriber("/image_raw", Image, self.cb_image)
        rospy.Subscriber("/darknet_ros/bounding_boxes", BoundingBoxes, self.sub_boundingBoxes, queue_size=10)
        rospy.Timer(rospy.Duration(0.01), self.update_timer)
        rospy.Timer(rospy.Duration(0.1), self.update_relay) #ADDED FOR RELAY
        
        
        
        rate = rospy.Rate(10) # Changed 5 Hz --> 10 Hz
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
                if self.grn_timer > 9:
                    self.lamp_grn.Toggle()
                    self.grn_timer = 0
            rate.sleep()
        GPIO.output(11, GPIO.LOW)
        GPIO.output(12, GPIO.LOW)
        GPIO.output(15, GPIO.LOW)

    def cb_image(self, msg):
        self.bb_watchdog = 0

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
                                    self.relay_state = 1        # ADDED FOR RELAY
                                    self.relay_delay_cnt = 0    # ADDED FOR RELAY
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

    # ADDED FOR RELAY
    def update_relay(self, event):
        with self.lock:  # 락으로 보호
            if self.relay_state == 1:
                self.relay_delay_cnt += 1
                if self.relay_delay_cnt > self.relay_on_delay:  # RELAY ON, after delay
                    GPIO.output(16, GPIO.HIGH)
                    self.relay_state = 2
                    self.relay_delay_cnt = 0
            elif self.relay_state == 2:
                self.relay_delay_cnt += 1
                if self.relay_delay_cnt > self.relay_off_delay:   # RELAY OFF, after delay
                    GPIO.output(16, GPIO.LOW)
                    self.relay_state = 0        # Reset RELAY state
                    self.relay_delay_cnt = 0 
            
    def update_timer(self, event):
        self.timer1+=1
        self.bb_watchdog+=1
        if self.bb_watchdog>500:
            self.bb_timeout = True
            self.lamp_red.On()
        else:
            if self.bb_timeout:
                self.bb_timeout = False
                self.lamp_red.Off()

    def main(self):
        rospy.spin()

if __name__ == '__main__':
    try :
        rospy.init_node('jetson_darknet_node')
        node = JetsonDarknetNode()
        node.main()
    except rospy.ROSInterruptException:
        pass
