#!/usr/bin/env python3
# coding=utf-8

import time,os
import numpy as np
import math
import cv2
import rospy
import actionlib
from ucar_startup.msg import DetectResult
from geometry_msgs.msg import Twist
from rosgraph_msgs.msg import Clock
from actionlib_msgs.msg import GoalStatus
from sensor_msgs.msg import Image
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Int8
from std_msgs.msg import String
from std_srvs.srv import Trigger, TriggerRequest, TriggerResponse
from nav_msgs.msg import Odometry
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from threading import Thread
import qrcode
import barcode
from pyzbar.pyzbar import decode
import websocket
import json
import line

# 朝向 q=(0,0,sin(a/2),cos(a/2))
# 0° (0,0,0,1)
# 45° (0,0,0.3827,0.9239)
# 60° (0,0,0.5,0.866)
# 90° (0,0,0.7071,0.7071)
# 180° (0,0,1,0)
# 120° (0,0,0.8660,0.5)
# 270° (0,0,−0.7071,0.7071)

#各地点坐标
A = {"position": {"x": 0.97,"y": 0.626,"z": 0.0}, #二维码前
     "orientation": {"x": 0,"y":0,"z": 1,"w":0}}

B = {"position": {"x": 0.978,"y": 3.64,"z": 0.0}, #拣货区（找板前）
     "orientation": {"x":0,"y":0,"z": 0.7071,"w":0.7071}}

C = {"position": {"x": 0.978,"y": 3.64,"z": 0.0}, #拣货区中心（朝向灯）
     "orientation": {"x":0,"y":0,"z":0,"w":1}}

D = {"position": {"x": 2.97,"y": 4.25,"z": 0.0}, #灯1
     "orientation": {"x":0,"y":0,"z":0.7071,"w":0.7071}}

E = {"position": {"x": 3.94,"y": 4.25,"z": 0.0}, #灯2
     "orientation": {"x":0,"y":0,"z":0.7071,"w":0.7071}}

F = {"position": {"x": 2.62,"y": 3.2,"z": 0.0}, #入口1
     "orientation": {"x":0,"y":0,"z":0.573,"w":-0.819}}

G = {"position": {"x": 4.36,"y": 3.15,"z": 0.0}, #入口2
     "orientation": {"x":0,"y":0,"z":0.819,"w":-0.573}}

qrcode_result = None
room_result = None
gazebo_detect_class = None
detect_class = -1
gazebo_flag = False
total_money = 20
cost_money = 0
charge_money = 0
speech_flag = False
category_cn = {'Vegetable': '蔬菜','Fruit': '水果','Dessert': '甜品'}
class_money = {'辣椒': 2, '西红柿': 5, '土豆':2,'香蕉':2, '西瓜':5, '苹果':4,'可乐':3, '蛋糕':10, '牛奶':5}
class_cn = {0:"红灯",1:"绿灯",2:"辣椒",3:"土豆",4:"西红柿",5:"香蕉",6:"西瓜",7:"苹果",8:"可乐",9:"蛋糕",10:"牛奶"}

##============================================================
#-----------------------↓↓↓↓功能函数↓↓↓↓-----------------------
#============================================================================导航==================================================================
class Nav():
    def __init__(self):
        self.client = actionlib.SimpleActionClient('move_base', MoveBaseAction) #movebase的服务
        # self.imgsub = rospy.Subscriber("/usb_cam/image_raw", Image, self.imgupdate) #图像
        self.odomsub = rospy.Subscriber("/odom", Odometry, self.odomupdate) #里程计

        self.odom = Odometry()
        self.img = None
        self.detect = -1        
        self.client.wait_for_server()
        
    def odomupdate(self,data):
        self.odom = data
        
    def imgupdate(self,img_data):
        self.img = np.frombuffer(img_data.data, dtype=np.uint8).reshape(img_data.height, img_data.width, -1)

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
        rospy.loginfo('正在前往下一目标点...')
        self.client.send_goal(self.goal)
        
    def get_state(self):
        state = self.client.get_state()
        if state == GoalStatus.SUCCEEDED:
            # rospy.loginfo("reach")
            return True
        else:
            return False
#============================================================================导航==================================================================


#=========================================================================找板（方向）==============================================================
class AlignToCategory:
    def __init__(self, target_category):
        # rospy.init_node('align_to_category_node')

        # ROS 变量
        self.cmd_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        rospy.Subscriber('/rknn_detect_result', DetectResult, self.detect_callback)

        # 类别映射
        self.class_num = {
            "red":0, "green":1, "pepper":2, "tomato":3, "potato":4,
            "banana":5, "watermelon":6, "apple":7, "cola":8, "cake":9, "milk":10
        }
        self.category = {
            'pepper': 'Vegetable', 'tomato': 'Vegetable', 'potato': 'Vegetable',
            'banana': 'Fruit', 'watermelon': 'Fruit', 'apple': 'Fruit',
            'cola': 'Dessert', 'cake': 'Dessert', 'milk': 'Dessert'
        }

        self.class_id_to_name = {v: k for k, v in self.class_num.items()}
        self.target_category = target_category
        self.target_found = False

        # 旋转参数
        self.target_center = 0.0
        self.center_threshold = 24.0

        rospy.loginfo("Start rotating: %s", target_category)
        self.rotate()

    def rotate(self):
        rate = rospy.Rate(10)
        twist = Twist()
        twist.angular.z = 0.3

        while not rospy.is_shutdown() and not self.target_found:
            self.cmd_pub.publish(twist)
            rate.sleep()

        self.stop()

        twist.angular.z = -0.3  # 顺时针方向
        start_time = rospy.Time.now()

        while not rospy.is_shutdown() and (rospy.Time.now() - start_time).to_sec() < 0.3:
            self.cmd_pub.publish(twist)
            rate.sleep()

        self.stop()

    def stop(self):
        twist = Twist()
        self.cmd_pub.publish(twist)
        rospy.loginfo("Target aligned. Rotation stopped.")

    def detect_callback(self, msg):
        global detect_class
        class_id = msg.detect_class
        detect_class = class_id
        box_center = msg.box_center

        # 获取类别名称
        name = self.class_id_to_name.get(class_id, None)
        if not name:
            return

        # 判断类别是否属于目标大类
        obj_category = self.category.get(name, None)
        if obj_category == qrcode_result:
            rospy.loginfo("Detected: %s (class %d), box_center=%.2f, category=%s",
                        name, class_id, box_center, obj_category)
        else:
            pass

        if obj_category == self.target_category:
            if abs(box_center - self.target_center) <= self.center_threshold:
                self.target_found = True
#=========================================================================找板（方向）============================================================


#=========================================================================找板（距离）============================================================
class ForwardUntilObstacle:
    def __init__(self):
        # rospy.init_node('forward_until_obstacle')
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.scan_sub = rospy.Subscriber('/scan', LaserScan, self.scan_callback)
        
        self.forward_speed = 0.3       # 向前速度
        self.detection_range = 0.34    # 阈值20cm
        self.min_valid_range = 0.1
        self.scan_angle = 22.5           # 前方 ±30°

        self.obstacle_detected = False
        self.stopped = False           # 是否已发送停止并退出

    def scan_callback(self, scan_data):
        total_angles = len(scan_data.ranges)
        center_index = total_angles // 2
        start_idx = center_index - int(self.scan_angle / 2 * total_angles / 360)
        end_idx = center_index + int(self.scan_angle / 2 * total_angles / 360)

        for i in range(start_idx, end_idx):
            dist = scan_data.ranges[i]
            if not math.isnan(dist) and self.min_valid_range < dist <= self.detection_range:
                self.obstacle_detected = True
                return

        self.obstacle_detected = False

    def run(self):
        rate = rospy.Rate(10)
        move_cmd = Twist()
        # while not rospy.is_shutdown() and not self.stopped:

        while not rospy.is_shutdown():
            if self.obstacle_detected:
                rospy.logwarn("前方有障碍物，停止！")
                move_cmd.linear.x = 0.0
                self.cmd_vel_pub.publish(move_cmd)
                rospy.sleep(0.1)  # 确保停止指令被接收
                self.stopped = True
                break
                # rospy.signal_shutdown("检测到障碍，主动退出")
            else:
                move_cmd.linear.x = self.forward_speed
                self.cmd_vel_pub.publish(move_cmd)

            rate.sleep()
#=========================================================================找板（距离）============================================================


#=========================================================================找板（矫正）============================================================
class AlignToWallCenter:
    def __init__(self):
        # rospy.init_node("align_to_wall_center_node")

        # 发布速度控制
        self.cmd_pub = rospy.Publisher("/cmd_vel", Twist, queue_size=10)

        # 订阅雷达
        rospy.Subscriber("/scan", LaserScan, self.scan_callback)

        # 控制参数
        self.target_distance = 0.3  # 希望距离障碍板的距离（30cm）
        self.stop_threshold = 0.36  # 距离中点误差小于5cm停止
        self.k_linear = 0.3         # 线性速度比例系数

        self.reached = False
        self.rate = rospy.Rate(10)

    def scan_callback(self, scan):
        if self.reached:
            return

        ranges = np.array(scan.ranges)
        angle_min = scan.angle_min
        angle_increment = scan.angle_increment
        angle_max = scan.angle_max

        # 选取前方 ±30° 范围内的点
        points = []
        for i, r in enumerate(ranges):
            if np.isfinite(r) and 0.1 < r < 1.5:
                angle = angle_min + i * angle_increment
                if -math.pi / 6 <= angle <= math.pi / 6:
                    x = r * math.cos(angle)
                    y = r * math.sin(angle)
                    points.append((x, y))

        if len(points) < 10:
            rospy.logwarn("激光点不足，无法拟合直线")
            return

        xs, ys = zip(*points)
        A = np.vstack([xs, np.ones(len(xs))]).T
        m, c = np.linalg.lstsq(A, ys, rcond=None)[0]

        # 拟合直线：y = m * x + c
        # 求出端点（左右最远点）中点作为目标
        x_min, x_max = min(xs), max(xs)
        x_center = (x_min + x_max) / 2.0
        y_center = m * x_center + c

        # 计算与目标点（中点）的误差
        dx = x_center
        dy = y_center - self.target_distance  # 保持30cm距离
        distance = math.hypot(dx, dy)
        # print(dx,dy)
        # print(abs(dy) - dx)

        # 控制运动
        twist = Twist()

        # if distance > self.stop_threshold:
        if abs(dy) - dx > 0.07 and 0.27 < dx < 0.32 and 0.37 < abs(dy) < 0.41:
            twist.linear.x = 0.0
            twist.linear.y = 0.0
            self.reached = True
            rospy.loginfo("已到达障碍板中点位置，停止运动")
        elif 0.05 < dx < 0.22:
            twist.linear.x = 0.0
            twist.linear.y = 0.0
            self.reached = True
            rospy.loginfo("已到达障碍板中点位置，停止运动")
        else:
            twist.linear.x = self.k_linear * dx
            twist.linear.y = self.k_linear * dy
            rospy.loginfo("正在对准障碍板中点... dx=%.2f, dy=%.2f", dx, dy)

        self.cmd_pub.publish(twist)

    def run(self):
        rospy.loginfo("节点启动：板前矫正")
        while not rospy.is_shutdown():
            if self.reached:
                break
            self.rate.sleep()
#=========================================================================找板（矫正）============================================================


#=========================================================================语音唤醒============================================================
def get_test_client():
    global speech_flag
    rospy.wait_for_service('/speech_command_node/get_test_server')
    get_test = rospy.ServiceProxy('/speech_command_node/get_test_server', Trigger)

    while not rospy.is_shutdown():
        try:
            response = get_test()
            if response.success:
                speech_flag = response.message
                # print(speech_flag)
                return response.success, response.message
            else:
                rospy.logwarn("服务调用成功但还未唤醒，继续等待...")
        except rospy.ServiceException as e:
            rospy.logwarn("服务调用异常: %s，重试中...", e)
        time.sleep(1.0)  # 每秒重试一次
#=========================================================================语音唤醒============================================================


#=================================================================语音合成 tts_pub============================================================
def publish_tts_message(text):
    # rospy.init_node('tts_publisher', anonymous=True)
    pub = rospy.Publisher('/tts_input', String, queue_size=10)

    rospy.sleep(0.1)

    message = text
    msg = String()
    msg.data = message

    pub.publish(msg)
    rospy.loginfo("语音已合成: %s", message)
#=================================================================语音合成 tts_pub============================================================


#=====================================================================RKNN推理================================================================
def detect(): #RKNN推理
    os.system('python /home/iflytek/ucar_ws/src/ucar_startup/scripts/rk.py')

def stop_camera(): #释放摄像头资源
    # rospy.init_node('camera_controller', anonymous=True)
    # rospy.loginfo("初始化成功")
    pub = rospy.Publisher('/startup', String, queue_size=1)
    rospy.sleep(0.5)
    pub.publish("stop")
    rospy.sleep(0.5)
    rospy.loginfo("停止RKNN推理")
#=====================================================================RKNN推理================================================================


#=================================================================二维码识别结果================================================================
def qrcode_detect(): #二维码识别结果
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Camera Open Error.")
        return None

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        codes = decode(gray)

        if codes:
            results = [code.data.decode('utf-8') for code in codes]
            cap.release()
            return results
#=================================================================二维码识别结果================================================================


#=====================================================================通信=====================================================================
def publish_qrcode_result(): #发布二维码结果
    global gazebo_flag
    pub = rospy.Publisher('/qrcode_result', String, queue_size=1)
    rospy.sleep(0.5)  # 等待Publisher连接建立
    pub.publish(qrcode_result)

    rate = rospy.Rate(10)  # 发布频率为 10Hz

    while not rospy.is_shutdown():
        result_str = qrcode_result if qrcode_result is not None else "None"
        if gazebo_flag:
            pub.publish(result_str)
        # rospy.loginfo(f"识别结果: {qrcode_result}")
        rate.sleep()

def on_message(ws, message): #订阅仿真中的房间结果
    global room_result, gazebo_detect_class
    data = json.loads(message)
    if "msg" in data:
        result_raw = data['msg']
        result = result_raw["data"]
        room_result, gazebo_detect_class = result.split(',')

def on_error(ws, error):
    print(f"[WebSocket Error]: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed")

def on_open(ws):
    subscribe_message = {"op": "subscribe","topic": "/room_result"}
    ws.send(json.dumps(subscribe_message))
    print("Subscribed to /room_result")

def start_websocket():
    ws_url = "ws://192.168.31.249:9090" #虚拟机IP！！！！！
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()
#=====================================================================通信=====================================================================





##============================================================
#-----------------------↓↓↓↓主函数↓↓↓↓-------------------------
##============================================================
if __name__ =='__main__':
    rospy.init_node('startup')

    nav = Nav() #导航初始化
    detect = Thread(target=detect) #实例化RKNN推理多线程

    pub_thread = Thread(target=publish_qrcode_result) #实例化 qr_result发布 多线程
    pub_thread.daemon = True 
    pub_thread.start()

    rospy.loginfo("初始化完成！")

    rospy.loginfo("等待唤醒...")
    success, speech_flag = get_test_client() #语音唤醒
    rospy.loginfo("success=%s, message=%s" % (success, speech_flag)) #打印语音唤醒状态
    rospy.loginfo("唤醒状态:%s",speech_flag)
    time.sleep(2) #读

# =========调试时用，不调用语音唤醒===========
    # speech_flag = True
# =========调试时用，不调用语音唤醒===========

    if speech_flag:
        once = 0
        while not rospy.is_shutdown():
            if once == 0: # 前往目标点 --> 二维码前
                once += 1
                nav.get_pose(A)
                nav.send_goal()

            if nav.get_state() and once == 1: # 到达目标点 --> 二维码前
                once += 1
                rospy.loginfo("已到达目标点：二维码前")
                result = qrcode_detect()
                time.sleep(0.3)
                for code in result:
                    qrcode_result = code
                rospy.loginfo("二维码结果为：{}".format(qrcode_result))

                if qrcode_result == "Fruit":
                    publish_tts_message("本次采购任务为水果")
                elif qrcode_result == "Vegetable":
                    publish_tts_message("本次采购任务为蔬菜")
                elif qrcode_result == "Dessert":
                    publish_tts_message("本次采购任务为甜品")

                time.sleep(3.6) #等待语音播报

            if once == 2: # 前往目标点 --> 拣货区
                once += 1
                nav.get_pose(B)
                nav.send_goal()

                detect.start()

            if nav.get_state() and once == 3: # 到达目标点 --> 拣货区
                once += 1
                rospy.loginfo('已到达目标点：拣货区')

                try: #找板（方向）
                    AlignToCategory(target_category = qrcode_result) #"Fruit"、"Vegetable" 或 "Dessert"
                except rospy.ROSInterruptException:
                    pass

                try: #找板（距离）
                    node = ForwardUntilObstacle()
                    rospy.loginfo("向前移动直到检测到障碍物")
                    node.run()
                except rospy.ROSInterruptException:
                    pass

                try: #找板（矫正）
                    node = AlignToWallCenter()
                    node.run()
                except rospy.ROSInterruptException:
                    pass

                try: #语音播报
                    publish_tts_message("我已取到{}".format(class_cn[detect_class]))
                except rospy.ROSInterruptException:
                    pass

                goods_detect_result = detect_class

                time.sleep(3.3) #等待语音播报

            if once == 4: # 前往目标点 (从目标板前) --> 拣货区中心
                once += 1
                nav.get_pose(C)
                nav.send_goal()

            if nav.get_state() and once == 5: # 到达目标点 --> 拣货区中心
                once += 1
                rospy.loginfo('已到达目标点：拣货区')
                rospy.loginfo('即将开始仿真任务')

#================================仿真======================================
                gazebo_flag = True
            
                rospy.loginfo(f"已发布识别二维码识别结果: {qrcode_result}")

                ws_thread = Thread(target=start_websocket) #实例化 通信 多线程（获取仿真信息）
                ws_thread.daemon = True  # 设置为守护线程，主线程结束它也会退出
                ws_thread.start()

                #等待仿真结果
                while room_result not in ["A", "B", "C"]: 
                    # print(room_result)
                    time.sleep(0.1)

                rospy.loginfo(f"仿真任务已完成，目标货物位于{room_result}房间")

                try: #语音播报
                    if room_result == "A":
                        publish_tts_message("仿真任务已完成 目标货物位于AE房间")
                    elif room_result == "B":
                        publish_tts_message("仿真任务已完成 目标货物位于B房间")
                    elif room_result == "C":
                        publish_tts_message("仿真任务已完成 目标货物位于C房间")
                except rospy.ROSInterruptException:
                    pass
                time.sleep(7.5) #等待语音播报
#================================仿真======================================

            if once == 6: # 前往目标点 --> 灯1
                once += 1
                nav.get_pose(D)
                nav.send_goal()
                
            if nav.get_state() and once == 7: # 到达目标点 --> 灯1
                rospy.loginfo("已到达灯1")
        
                stop_camera() #停止识别

                if detect_class == 1:
                    try: #语音播报
                        publish_tts_message("路口一可通过")
                    except rospy.ROSInterruptException:
                       pass
                    time.sleep(3) #等待语音播报

                    once += 3 #once = 10 去入口1
                else:
                    once += 1 #once = 8 去灯2

            if once == 8: # 前往目标点 --> 灯2
                once += 1
                nav.get_pose(E)
                nav.send_goal()

            if nav.get_state() and once == 9: # 到达目标点 --> 灯2
                once += 3

                try: #语音播报
                    publish_tts_message("路口二可通过")
                except rospy.ROSInterruptException:
                    pass

                time.sleep(3) #等待语音播报

            if once == 10: # 前往目标点 --> 入口1
                once += 1
                nav.get_pose(F)
                nav.send_goal()

            if nav.get_state() and once == 11: # 到达目标点 --> 入口1
                once += 3
                rospy.loginfo('已到达一号路口')

                rospy.loginfo('开始巡线')
                line.run(True) #绕圈先改line.py
                rospy.loginfo('巡线结束')

            if once == 12: # 前往目标点 --> 入口2
                once += 1
                nav.get_pose(G)
                nav.send_goal()

            if nav.get_state() and once == 13: # 到达目标点 --> 入口2
                once += 1
                rospy.loginfo('已到达二号路口')

                rospy.loginfo('开始巡线')
                line.run(False) #绕圈先改line.py
                rospy.loginfo('巡线结束')

            if once == 14:
                rospy.loginfo(f"实际货物：{class_cn[goods_detect_result]},实际货物费用：{class_money[class_cn[goods_detect_result]]}")
                rospy.loginfo(f"仿真货物：{class_cn[int(gazebo_detect_class)]},仿真货物费用：{int(class_money[class_cn[int(gazebo_detect_class)]])}")
                #花费
                cost_money = (int(class_money[class_cn[goods_detect_result]]) + int(class_money[class_cn[int(gazebo_detect_class)]]))
                rospy.loginfo(f"总花费花费：{cost_money}")
                #找零
                charge_money = total_money - cost_money
                rospy.loginfo(f"找零：{charge_money}")
                rospy.loginfo(f"我已完成货物采购任务，本次采购货物为{category_cn[qrcode_result]},总计花费{cost_money}元，需找零{charge_money}元")

                try: #语音播报
                    publish_tts_message(f"我已完成货物采购任务，本次采购货物为{category_cn[qrcode_result]},总计花费{cost_money}元，需找零{charge_money}元")
                except rospy.ROSInterruptException:
                    pass

                time.sleep(15) #等待语音播报

                break

 
 