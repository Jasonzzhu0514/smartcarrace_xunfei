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
import start

#=========================================================================找板（方向）==============================================================
class AlignToCategory:
    def __init__(self, target_category):
        rospy.init_node('align_to_category_node')

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
        rospy.loginfo("Detected: %s (class %d), box_center=%.2f, category=%s",
                      name, class_id, box_center, obj_category)

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
        self.detection_range = 0.32    # 阈值20cm
        self.min_valid_range = 0.1
        self.scan_angle = 15           # 前方 ±30°

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
        print(dx,dy)
        print(abs(dy) - dx)

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
            self.rate.sleep()



def detect(): #RKNN推理
    os.system('python /home/iflytek/ucar_ws/src/ucar_startup/scripts/rk.py')


if __name__ == '__main__':
    detect = Thread(target=detect)
    detect.start()

    time.sleep(2)

    try: #找板（方向）
        AlignToCategory("Dessert") #"Fruit"、"Vegetable" 或 "Dessert"
    except rospy.ROSInterruptException:
        pass

    try: #找板（距离）
        node = ForwardUntilObstacle()
        rospy.loginfo("向前移动直到检测到障碍物")
        node.run()
    except rospy.ROSInterruptException:
        pass
    
    try:
        node = AlignToWallCenter()
        node.run()
    except rospy.ROSInterruptException:
        pass
        

    start.stop_camera()

