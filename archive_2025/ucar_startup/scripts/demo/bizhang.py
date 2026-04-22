#!/usr/bin/env python
import rospy
import math
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
import time

class CloseRangeDetector:
    def __init__(self):
        rospy.init_node('close_range_detector')
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.scan_sub = rospy.Subscriber('/scan', LaserScan, self.scan_callback)

        self.min_valid_range = 0.1
        self.scan_angle = 30
        self.detection_range = 0.35
        self.obstacle_detected = False

        self.lateral_speed = 0.3
        self.forward_speed = 0.3
        self.move_state = "FORWARD"  # 默认状态

        self.lateral_duration = 1.75
        self.forward_duration = 2.1
        self.action_start_time = 0

        self.avoidance_completed = False  # ✅ 新增：避障完成标志

    def scan_callback(self, scan_data):
        total_angles = len(scan_data.ranges)
        center_index = total_angles // 2
        start_idx = center_index - int(self.scan_angle / 2 * total_angles / 360)
        end_idx = center_index + int(self.scan_angle / 2 * total_angles / 360)

        valid_ranges = []
        for i in range(start_idx, end_idx):
            dist = scan_data.ranges[i]
            if not math.isnan(dist) and self.min_valid_range < dist <= self.detection_range:
                valid_ranges.append(dist)

        if valid_ranges and self.move_state == "FORWARD":
            rospy.logwarn("⚠️ 前方20cm内检测到障碍物，启动避障！")
            self.move_state = "LATERAL_RIGHT"
            self.action_start_time = time.time()

    def execute_avoidance_sequence(self):
        current_time = time.time()
        elapsed = current_time - self.action_start_time
        move_cmd = Twist()

        if self.move_state == "LATERAL_RIGHT":
            move_cmd.linear.y = self.lateral_speed
            if elapsed >= self.lateral_duration:
                rospy.loginfo("✅ 右移完成，前进中...")
                self.move_state = "AVOID_FORWARD"
                self.action_start_time = current_time

        elif self.move_state == "AVOID_FORWARD":
            move_cmd.linear.x = self.forward_speed
            if elapsed >= self.forward_duration:
                rospy.loginfo("✅ 前进完成，开始左移")
                self.move_state = "LATERAL_LEFT"
                self.action_start_time = current_time

        elif self.move_state == "LATERAL_LEFT":
            move_cmd.linear.y = -self.lateral_speed
            if elapsed >= self.lateral_duration:
                rospy.loginfo("✅ 避障完成，停止机器人并退出")
                self.move_state = "STOP"
                self.avoidance_completed = True  # ✅ 设置退出标志
                move_cmd = Twist()  # 停止运动

        self.cmd_vel_pub.publish(move_cmd)

    def run(self):
        rate = rospy.Rate(10)
        while not rospy.is_shutdown():
            if self.avoidance_completed:
                # ✅ 退出前发送停止指令一次
                self.cmd_vel_pub.publish(Twist())
                rospy.signal_shutdown("避障结束，节点退出")
                break

            if self.move_state == "FORWARD":
                move_cmd = Twist()
                move_cmd.linear.x = self.forward_speed
                self.cmd_vel_pub.publish(move_cmd)

            elif self.move_state in ["LATERAL_RIGHT", "AVOID_FORWARD", "LATERAL_LEFT"]:
                self.execute_avoidance_sequence()

            rate.sleep()

if __name__ == '__main__':
    try:
        detector = CloseRangeDetector()
        rospy.loginfo("🚀 节点启动，机器人默认前进中...")
        rospy.sleep(1)
        detector.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("节点终止。")
