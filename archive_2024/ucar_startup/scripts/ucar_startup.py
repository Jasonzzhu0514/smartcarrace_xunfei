#!/usr/bin/env python3
# coding=utf-8

import time,os
import numpy as np
import math
import cv2
import rospy
import actionlib
from rosgraph_msgs.msg import Clock
from actionlib_msgs.msg import GoalStatus
from sensor_msgs.msg import Image
from std_msgs.msg import Int8
from std_msgs.msg import String
# from detect import main
from nav_msgs.msg import Odometry
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from std_srvs.srv import Trigger, TriggerRequest, TriggerResponse
from threading import Thread


def open_terminal(commands):
    cmd_list = []
    for cmd in commands:
        cmd_list.append(""" gnome-terminal --tab -e "bash -c '%s;exec bash'" >/dev/null  2>&1 """ %cmd)

    os.system(';'.join(cmd_list))

#各地点坐标
A = {
    "position": 
    {
        "x": -0.08,
        "y": 0.0,
        "z": 0.0
    },
    "orientation": 
    {
        "x": 0.0,
        "y": 0.0,
        "z": 0,
        "w": 1
    }
    }
    
B = {
    "position": 
    {
        "x": 0.965,
        "y": -1.28,
        "z": 0.00454
    },
    "orientation": 
    {
        "x": 0.0,
        "y": 0.0,
        "z": 0,
        "w": 1
    }
    }
    
C = {
    "position": 
    {
        "x": 1.93,
        "y": -0.1,
        "z": 0.00554
    },
    "orientation": 
    {
        "x": 0.0,
        "y": 0.0,
        "z": 0,
        "w": 1
    }
    }
    
xiepo1 = {
    "position": 
    {
        "x": -0.08,
        "y": 0.0,
        "z": 0.0
    },
    "orientation": 
    {
        "x": 0.0,
        "y": 0.0,
        "z": 1,
        "w": 0
    }
    }

xiepo2 = {
    "position": 
    {
        "x": -1.88,
        "y": 0.051,
        "z": 0.00702
    },
    "orientation": 
    {
        "x": 0.0,
        "y": 0.0,
        "z": 0,
        "w": 1
    }
    }

jjb = {
    "position": 
    {
        "x": -2.53,
        "y": 1.91,
        "z": 0.000869
    },
    "orientation": 
    {
        "x": 0.0,
        "y": 0.0,
        "z": 0.707,
        "w": 0.707
    }
    }

class Nav():
    def __init__(self):
        self.client = actionlib.SimpleActionClient('move_base', MoveBaseAction)#movebase的服务
        # self.imgsub = rospy.Subscriber("/cam", Image, self.imgupdate)#图像
        self.yolosub = rospy.Subscriber('/detect',String,self.detectupdate)#识别的图片标签
        self.odomsub = rospy.Subscriber("/odom", Odometry, self.odomupdate)#里程计
        self.terrorist = None #一人 1 ，两人 2，三人 3
        self.wuziflag = 0
        self.odom = Odometry()
        self.img = None
        self.detect = -1        
        self.client.wait_for_server()
        
    def odomupdate(self,data):
        self.odom = data
        
        
    def imgupdate(self,img_data):
        self.img = np.frombuffer(img_data.data, dtype=np.uint8).reshape(img_data.height, img_data.width, -1)
        
    def detectupdate(self,msg):
        client = msg.data
        classes = client.split(':')[-1]
        if classes == '4':
            rospy.loginfo('result:terrorist1')
        elif classes == '5':
            rospy.loginfo('result:terrorist2')
        elif classes == '6':
            rospy.loginfo('result:terrorist3')
        self.detect = classes
    

    def get_pose(self,data):
        text = data.copy()
        self.pos_x = text['position']['x']
        self.pos_y = text['position']['y']
        self.pos_z = text['position']['z']
        self.ori_x = text['orientation']['x']
        self.ori_y = text['orientation']['y']
        self.ori_z = text['orientation']['z']
        self.ori_w = text['orientation']['w']
        
    def goal_pose(self):
        self.goal = MoveBaseGoal()
        self.goal.target_pose.header.frame_id = 'map'
        self.goal.target_pose.pose.position.x = self.pos_x
        self.goal.target_pose.pose.position.y = self.pos_y
        self.goal.target_pose.pose.position.z = self.pos_z
        self.goal.target_pose.pose.orientation.x = self.ori_x
        self.goal.target_pose.pose.orientation.y = self.ori_y
        self.goal.target_pose.pose.orientation.z = self.ori_z
        self.goal.target_pose.pose.orientation.w = self.ori_w
        
    def send_goal(self):
        self.goal_pose()
        print('send goal...')
        self.client.send_goal(self.goal)
        
    def get_state(self):
        state = self.client.get_state()
        if state == GoalStatus.SUCCEEDED:
            rospy.loginfo("reach")
            return True
        else:
            return False
    
def get_test_client():
    rospy.wait_for_service('/speech_command_node/get_test_server')
    try:
        get_test = rospy.ServiceProxy('/speech_command_node/get_test_server', Trigger)
        response = get_test()
        return response.success, response.message
    except rospy.ServiceException as e:
        print("Service call failed: %s" % e)


def detect():
    os.system('python /home/iflytek/ucar_ws/src/ucar_startup/scripts/rk.py')

if __name__ =='__main__':
    rospy.init_node('predict')
    rospy.loginfo("init successl!")

    detect = Thread(target=detect)
    detect.start()
    
    # rospy.loginfo("Calling get_test service...  Waiting response!!!")
    # success, message = get_test_client()
    # print(" success=%s, message=%s" % (success, message))
    # rospy.loginfo("wake:%s",message)

    time.sleep(1)
    success = True
    if success == True:
        nav = Nav()
        once = 0
        while not rospy.is_shutdown():
            if once == 0:
                once += 1
                nav.get_pose(B)
                nav.send_goal()
            if nav.get_state() and once == 1:
                once += 1
                print('reach B')
                print(nav.detect)
                if nav.detect == '4':
                    nav.terrorist = 1
                    os.system("aplay /home/iflytek/ucar_ws/src/ucar_startup/mp3/terrorist1.wav")
                elif nav.detect == '5':
                    nav.terrorist = 2
                    os.system("aplay /home/iflytek/ucar_ws/src/ucar_startup/mp3/terrorist2.wav")
                elif nav.detect == '6':
                    nav.terrorist = 3
                    os.system("aplay /home/iflytek/ucar_ws/src/ucar_startup/mp3/terrorist3.wav")
                detect.join()
                break
            # if once == 2:
            #     once += 1
            #     nav.get_pose(xiepo1)
            #     nav.send_goal()
            # if nav.get_state() and once == 3:
            #     once += 1
            #     print('reach xiepo1')
            #     time.sleep(3)
            # if once == 4:
            #     once += 1
            #     nav.get_pose(jjb)
            #     nav.send_goal()
            # if nav.get_state() and once == 5: #get fir_aid_kit
            #     once += 1
            #     print('reach jjb')
            #     os.system("aplay /home/iflytek/ucar_ws/src/ucar_startup/mp3/first_aid_kit.wav")
            #     time.sleep(3)
            # if once == 6:
            #     once += 1
            #     nav.get_pose(xiepo2)
            #     nav.send_goal()
            # if nav.get_state() and once == 7:
            #     once += 1
            #     print('reach xiepo2')
            #     if nav.terrorist == 1:
            #         os.system("aplay /home/iflytek/ucar_ws/src/ucar_startup/mp3/spontoon.wav")
            #     elif nav.terrorist == 2:
            #         os.system("aplay /home/iflytek/ucar_ws/src/ucar_startup/mp3/bulletproof_vest.wav")
            #     elif nav.terrorist == 3:
            #          os.system("aplay /home/iflytek/ucar_ws/src/ucar_startup/mp3/teargas.wav")
            #     time.sleep(1)
            # if once == 8:
            #     once += 1
            #     nav.get_pose(A)
            #     nav.send_goal()
            # if nav.get_state() and once == 9:
            #     once += 1
            #     print('reach A')
            #     time.sleep(3)
            # if once == 10:
            #     once += 1
            #     nav.get_pose(C)
            #     nav.send_goal()
            # if nav.get_state() and once == 11:
            #     once += 1
            #     print('reach C')
            #     time.sleep(1)
            # if once == 12:
            #     os.system("aplay /home/iflytek/ucar_ws/src/ucar_startup/mp3/finish.wav")

            #     detect.join()
            #     break

