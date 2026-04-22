#!/usr/bin/env python3
# coding=utf-8

import numpy as np
import pandas as pd
import time
import os
import math
import cv2
import rospy
import torch
import actionlib
from rosgraph_msgs.msg import Clock
from actionlib_msgs.msg import GoalStatus
from sensor_msgs.msg import Image
from std_msgs.msg import Int8
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from threading import Thread
import websocket
import json
import shutil


S = {"position": {"x": 0.01,"y":-0.01,"z": 0.0},
     "orientation": {"x": 0,"y":0,"z": 1,"w":0}}

A = {"position": {"x": 0.875,"y": 1.2,"z": 0.0},
     "orientation": {"x": 0.0,"y":0.0,"z": 0.7071,"w":0.7071}}

B = {"position": {"x": 2.65,"y": 0.87,"z": 0.0},
     "orientation": {"x": 0.0,"y":0,"z":0.7071,"w":0.7071}}

C = {"position": {"x": 3.59,"y": 1.07,"z": 0.0},
     "orientation": {"x": 0.0,"y": 0,"z":0.5,"w":0.8660}}

C_b = {"position": {"x": 3.86,"y":0.85,"z": 0.0},
       "orientation": {"x": 0,"y":0,"z": 0,"w":1}}

#各地点坐标 L->R A-B-C  q=(0,0,sin(a/2),cos(a/2))
# 0° (0,0,0,1)
# 45° (0,0,3827,0.9239)
# 90° (0,0,0.7071,0.7071)
# 180° (0,0,1,0)(0,0,1,0)
# 120° (0,0,0.8660,0.5)
# 270° (0,0,−0.7071,0.7071)

target_category = None
detect_result = None #如0
Room = None
Room_A = None
Room_B = None
Room_C = None

result_path = "/home/iflytek-car/gazebo_test_ws/src/gazebo_pkg/result/"
detect_result_path = "/home/iflytek-car/gazebo_test_ws/src/gazebo_pkg/result/detect/"
class_num = {"red":0, "green":1, "pepper":2, "tomato":3, "potato":4,
            "banana":5, "watermelon":6, "apple":7, "cola":8, "cake":9, "milk":10}
category = {
    'pepper': 'Vegetable','tomato': 'Vegetable','potato': 'Vegetable',
    'banana': 'Fruit','watermelon': 'Fruit','apple': 'Fruit',
    'cola': 'Dessert','cake': 'Dessert','milk': 'Dessert'}


class Nav():
    def __init__(self):
        self.client = actionlib.SimpleActionClient('move_base', MoveBaseAction)#movebase的服务
        self.imgsub = rospy.Subscriber("/cam", Image, self.imgupdate)#图像
        self.odomsub = rospy.Subscriber("/odom", Odometry, self.odomupdate)#里程计
        self.odom = Odometry()
        self.img = None
    
    def odomupdate(self,data):
        self.odom = data
        
    def imgupdate(self,img_data):
        self.img = np.frombuffer(img_data.data, dtype=np.uint8).reshape(img_data.height, img_data.width, -1)
        self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        
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
        # rospy.loginfo('Sending goal...')
        self.client.send_goal(self.goal)
        
    def get_state(self):
        state = self.client.get_state()
        if state == GoalStatus.SUCCEEDED:
            # rospy.loginfo("GOAL Reached!")
            return True
        else:
            return False  
      
# =========================================目标检测及处理==========================================================================
def get_latest_modified_folder(parent_path):
    folders = [os.path.join(parent_path, name) for name in os.listdir(parent_path)
               if os.path.isdir(os.path.join(parent_path, name))]
    if not folders:
        print("No folder.")
        return None
    latest_folder = max(folders, key=os.path.getmtime)
    latest_folder_name = os.path.basename(latest_folder)
    for folder in folders:
        if folder != latest_folder:
            try:
                shutil.rmtree(folder)
            except Exception as e:
                print(e)

    return latest_folder_name

def posscess(target_category):
    global Room_A,Room_B,Room_C,detect_result
    latest_folder = get_latest_modified_folder(detect_result_path)
    df = pd.read_csv(detect_result_path + latest_folder + "/predictions.csv")
    df['Category'] = df['Prediction'].map(category)
    df['Room'] = df['Image Name'].str.extract(r'([A-Z])')

    room_dict = dict(zip(df['Room'], df['Prediction']))

    Room_A = room_dict.get('A', 'Unknown')
    Room_B = room_dict.get('B', 'Unknown')
    Room_C = room_dict.get('C', 'Unknown')

    filtered = df[df['Category'] == target_category]

    detect_class = filtered[filtered['Room'] == filtered['Room'].tolist()[0]]['Prediction'].values[0]
    detect_result = class_num[detect_class]

    return filtered['Room'].tolist()[0]

def detect():
    global Room
    os.system("python /home/iflytek-car/gazebo_test_ws/src/gazebo_pkg/yolov5/detect.py --weights /home/iflytek-car/gazebo_test_ws/src/gazebo_pkg/weights/best.pt --source /home/iflytek-car/gazebo_test_ws/src/gazebo_pkg/result/ --save-csv --project /home/iflytek-car/gazebo_test_ws/src/gazebo_pkg/result/detect/")
    Room = posscess(target_category)

def publish_room_result():
    pub = rospy.Publisher('/room_result', String, queue_size=1)
    rospy.sleep(0.5)  # 等待Publisher连接建立
    pub.publish("publish in /room_result...")

    rate = rospy.Rate(10)  # 发布频率为 10Hz

    while not rospy.is_shutdown():
        # result_str = Room
        if Room is not None and detect_result is not None:
            pub.publish(f"{Room},{detect_result}") 
        else:
            pass
            # rospy.logwarn("Room 或 detect_result 为 None，无法发布")
        # pub.publish(Room + "," + detect_result)
        # rospy.loginfo(f"识别结果: {result_str}")
        rate.sleep()

# =============================================通讯======================================================================
def on_message(ws, message):
    global target_category
    data = json.loads(message)
    if "msg" in data:
        qr_data = data['msg']
        target_category = qr_data["data"]
        # print(target_category)
        # print(qr_data["data"])

def on_error(ws, error):
    print(f"[WebSocket Error]: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed")

def on_open(ws):
    subscribe_message = {
        "op": "subscribe",
        "topic": "/qrcode_result"  # 修改为实际需要订阅的ROS话题（例如/imu）
    }
    ws.send(json.dumps(subscribe_message))
    print("Subscribed to /qrcode_result")

def start_websocket():
    # websocket.enableTrace(True)  # 启用调试日志（可选）
    ws_url = "ws://192.168.31.177:9090"

    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()
# ===================================================================================================================
def stay_time():
    time.sleep(0.3)
i = 0
if __name__ =='__main__': #target_category:Dessert,Vegetable,Fruit
    rospy.init_node('game')

    nav = Nav()
    yolo_dec = Thread(target=detect)

    rospy.loginfo("Initialization successl!")

    # target_category = "Dessert"
    # time.sleep(0.5)

    pub_thread = Thread(target=publish_room_result) #room_result发布
    pub_thread.daemon = True 
    pub_thread.start()
    time.sleep(15)

    ws_thread = Thread(target=start_websocket)
    ws_thread.daemon = True  # 设置为守护线程，主线程结束它也会退出
    ws_thread.start()

    rospy.loginfo("waiting for respond!")

    time.sleep(0.3) #不要改
    while target_category not in ["Vegetable", "Fruit", "Dessert"]:
        i += 1
        # print(str(target_category) + " times " +str(i))
        time.sleep(0.1)

    rospy.loginfo(f"需要识别的类别为：{target_category}")
        
    if target_category:
        time.sleep(2)
        rospy.loginfo("target_category:{}".format(target_category))
        rospy.loginfo("Race start!")

        start_time = time.time()
        once = 0
        while not rospy.is_shutdown():
            if once == 0:
                once += 1
                nav.get_pose(C)
                nav.send_goal()

            if nav.get_state() and once == 1:
                once += 1
                rospy.loginfo("Reach Room_C!")
                stay_time() #!!!!!!!!!!!!!!!!
                cv2.imwrite(result_path + "C.jpg",nav.img)
                
            if once == 2:
                once += 1
                nav.get_pose(B)
                nav.send_goal()

            if nav.get_state() and once == 3:
                once += 1
                rospy.loginfo("Reach Room_B!")
                stay_time() #!!!!!!!!!!!!!!!!
                cv2.imwrite(result_path + "B.jpg",nav.img)
                yolo_dec.start()

            if once == 4:
                once += 1
                nav.get_pose(A)
                nav.send_goal()

            if nav.get_state() and once == 5:
                once += 1
                rospy.loginfo("Reach Room_A!")
                stay_time() #!!!!!!!!!!!!!!!!
                cv2.imwrite(result_path + "A.jpg",nav.img)

            if once == 6:
                once += 1
                nav.get_pose(C_b)
                nav.send_goal()

            if nav.get_state() and once == 7:
                once += 1

            if once == 8:
                once += 1
                nav.get_pose(S)
                nav.send_goal()

            if nav.get_state() and once == 9:
                once += 1
                rospy.loginfo("Reach Destination!")
                time.sleep(1)

                yolo_dec.join()

                rospy.loginfo("Detect Result:Room_A : {} ,Room_B : {} ,Room_C : {}".format(Room_A,Room_B,Room_C))
                rospy.loginfo("目标货物位于{}房间".format(Room))

                break
        end_time = time.time()
        elapsed_time = end_time - start_time
        rospy.loginfo(f"耗时：{elapsed_time:.2f} s")
        rospy.loginfo(f"已发布结果: 识别结果{list(filter(lambda k: class_num[k] == detect_result, class_num.keys()))[0]},房间{Room}")

    else:
        rospy.loginfo("结果获取失败")


    rospy.spin()

