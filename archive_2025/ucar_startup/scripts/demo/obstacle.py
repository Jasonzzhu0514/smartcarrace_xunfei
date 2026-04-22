#!/usr/bin/env python
import rospy
import math
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist

class ForwardUntilObstacle:
    def __init__(self):
        rospy.init_node('forward_until_obstacle')
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.scan_sub = rospy.Subscriber('/scan', LaserScan, self.scan_callback)
        
        self.forward_speed = 0.3       # 向前速度
        self.detection_range = 0.28    # 阈值20cm
        self.min_valid_range = 0.1
        self.scan_angle = 30           # 前方 ±30°

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

        while not rospy.is_shutdown() and not self.stopped:
            if self.obstacle_detected:
                rospy.logwarn("⚠️ 前方20cm内有障碍物，停止并退出脚本！")
                move_cmd.linear.x = 0.0
                self.cmd_vel_pub.publish(move_cmd)
                rospy.sleep(0.1)  # 确保停止指令被接收
                self.stopped = True
                rospy.signal_shutdown("检测到障碍，主动退出")
            else:
                move_cmd.linear.x = self.forward_speed
                self.cmd_vel_pub.publish(move_cmd)

            rate.sleep()

if __name__ == '__main__':
    try:
        node = ForwardUntilObstacle()
        rospy.loginfo("🚀 向前移动直到检测到障碍物")
        node.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("节点已终止")
