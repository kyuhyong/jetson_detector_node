#!/usr/bin/env python
# license removed for brevity

import rospy
import cv2

from sensor_msgs.msg import Image
from cv_bridge import CvBridge


import sys, select, os
if os.name == 'nt':
  import msvcrt
else:
  import tty, termios

class ImageCaptureNode:
    def __init__(self, arg_fname):
        self.msg_count = 0
        if os.name != 'nt':
            self.settings = termios.tcgetattr(sys.stdin)
        
        self.cv_image = None
        self.br = CvBridge()
        cv2.startWindowThread()
        cv2.namedWindow("Image window")
        rospy.loginfo("Starting: image capture node")
        self.fname = rospy.get_param("~file_name")
        self.dir_name = os.path.join(os.path.expanduser('~')+"/image_capture/", self.fname)
        rospy.loginfo("Save files to : "+self.dir_name)
        if not os.path.exists(self.dir_name):
            rospy.loginfo("Create directory for "+self.dir_name)
            os.makedirs(self.dir_name)

        self.image_path = "/image_raw"
        if rospy.has_param("~image_path"):
            self.image_path = rospy.get_param("~image_path")
        rospy.loginfo("Subscribe image to : " + self.image_path)

        self.image_count = 0
        if rospy.has_param("~image_count_from"):
            self.image_count = rospy.get_param("~image_count_from")
        rospy.loginfo("Image count start from: {0}".format(self.image_count))
        rospy.loginfo("Press [ c ] to capture image")
        rospy.loginfo("Press [ q ] to quit program")
        # Subscribers
        rospy.Subscriber(self.image_path, Image, self.cb_image)
    
    def cb_image(self, msg):
        #rospy.loginfo("New image:")
        self.cv_image = self.br.imgmsg_to_cv2(msg, "bgr8")
        cv2.imshow("Image window", self.cv_image)
        self.msg_count+=1

    def get_fname(self):
        return self.fname


    def getKey(self):
        if os.name == 'nt':
            return msvcrt.getch()

        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            key = sys.stdin.read(1)
        else:
            key = ''

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key
    
    def main(self):
        #rospy.spin()
        br = CvBridge()
        save_count = self.image_count
        while not rospy.is_shutdown():
            key = self.getKey()
            if key == 'c':
                fileName = self.fname+'_'+str(save_count)+'.jpg'
                rospy.loginfo("Save image as "+self.dir_name+'/'+fileName)
                cv2.imwrite(self.dir_name+'/'+fileName, self.cv_image)
                save_count+=1
            elif key == 'q':
                rospy.signal_shutdown("User Quit")
        
        exit()
            #self.loop_rate.sleep()

if __name__ == '__main__':
    fname = None
    # Check argument
    if len(sys.argv)>1:
        print(sys.argv[1])
        if sys.argv[1].startswith("__"):
            fname = ""
        else:
            fname = sys.argv[1]
    else:
        print('Error: No file name is given as param. ')
        exit()
    try :
        rospy.init_node('image_capture_node')
        node = ImageCaptureNode(fname)
        node.main()
    except rospy.ROSInterruptException:
        pass