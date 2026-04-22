#!/usr/bin/env python
# -*- coding: utf-8 -*-
import rospy
import math
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from new_tinkin import LineFinder
import time

round = False
entry = True

circle_flag=1
right_flag=0
left_flag=0

class CloseRangeDetector:
    def __init__(self):
        # rospy.init_node('close_range_detector')
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
                rospy.loginfo("右移完成，前进中...")
                self.move_state = "AVOID_FORWARD"
                self.action_start_time = current_time

        elif self.move_state == "AVOID_FORWARD":
            move_cmd.linear.x = self.forward_speed
            if elapsed >= self.forward_duration:
                rospy.loginfo("前进完成，开始左移")
                self.move_state = "LATERAL_LEFT"
                self.action_start_time = current_time

        elif self.move_state == "LATERAL_LEFT":
            move_cmd.linear.y = -self.lateral_speed
            if elapsed >= self.lateral_duration:
                rospy.loginfo("避障完成，停止机器人并退出")
                self.move_state = "STOP"
                self.avoidance_completed = True  # 设置退出标志
                move_cmd = Twist()  # 停止运动

        self.cmd_vel_pub.publish(move_cmd)

    def run(self):
        rate = rospy.Rate(10)
        while not rospy.is_shutdown():
            if self.avoidance_completed:
                # 退出前发送停止指令一次
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


class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint):
        self.Kp = Kp  # 比例系数
        self.Ki = Ki  # 积分系数
        self.Kd = Kd  # 微分系数
        self.setpoint = setpoint  # 设定值

        self.prev_error = 0  # 上一次误差
        self.integral = 0  # 积分值

    def update(self, feedback):
        global circle_flag
        if left_flag and circle_flag:
            circle_flag=0
            # self.setpoint=0.4
            self.prev_error = 0  # 上一次误差
            self.integral = 0  # 积分值
        if right_flag and circle_flag:
            circle_flag=0
            # self.setpoint=0.75
            self.prev_error = 0  # 上一次误差
            self.integral = 0  # 积分值
        error = self.setpoint - feedback  # 计算误差
        
        self.integral += error  # 计算积分项
        derivative = error - self.prev_error # 计算微分项
        self.prev_error = error # 更新上一次误差
        control = self.Kp * error + self.Ki * self.integral + self.Kd * derivative # 计算控制量
        return control


class line_finder:
    def __init__(self):
        # 设置PID参数
        Kp = 4#7
        Ki = 0#0
        Kd = 2#2
        setpoint = 0.5  # 设定值
        # 创建PID控制器实例
        self.pid_controller = PIDController(Kp, Ki, Kd, setpoint)

        # 初始化ROS节点
        rospy.init_node('line_patrol_node', anonymous=True)
        # 创建一个Publisher，用于发布速度命令到机器人底盘
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        # 创建一个Twist消息，用于控制机器人的线速度和角速度
        self.cmd_vel = Twist()
        # 设置机器人的线速度和角速度
        self.cmd_vel.linear.x = 0.0000000005# 设置线速度为0.2 m/s
        self.cmd_vel.angular.z = 0  # 设置角速度为0.5 rad/s
        self.turn_times = 2
        self.last_turn = 0

    def line_main(self):
        try:
        
            # rospy.init_node('line_patrol', anonymous=True)
             
            line = LineFinder()
            turn_times = 2#I`M STUPID
            start_time = time.time()
            circle_time=time.time()
            left_time=time.time()
            right_time=time.time()
            last_turn_end = time.time()
            while True:
                result = line.process("cam")
                
                # 检查返回结果类型
                if len(result) == 4:
                    line_left, line_right, line_mid, flag = result
                    if_turn = False  # 默认设为False
                else:
                    # 回退处理（防止返回值格式再次变化）
                    line_left = result[0] if len(result) > 0 else 0
                    line_right = result[1] if len(result) > 0 else 0
                    line_mid = result[2] if len(result) > 0 else 0
                    flag = result[3] if len(result) > 1 else None
                    if_turn = result[4] if len(result) > 2 else False
                print(line_left,line_right,line_mid,flag)
                # 原有的PID和电机控制逻辑保持不变
                
                
                # print("output:", output, "Feedback:", feedback)
                # self.cmd_vel.linear.x = 0.3
                # self.cmd_vel.angular.z= -output
                
                rate_valuez = 0.15
                # rate_valuey = 0.05
                #rate_value = -0.05
                # 在大幅度转弯（直角弯）时拒绝y方向的移动
                #if (flag=='left' or flag == 'right') or time.time()-start_time <= 8:
               # 1.6 for origin value`` 
                if round == False:  #################不转圈
                    feedback = line_mid
                    control = self.pid_controller.update(feedback)
                    output = control
                    self.cmd_vel.linear.x = 0.2 + abs(output*0.05)
                    self.cmd_vel.angular.z = -output
                    # self.cmd_vel.linear.z =  rate_valuez * output * 1
                    # self.cmd_vel.linear.y =  rate_valuey * output * 1
                    print(1)

                elif round:  #################转圈
                    if entry:  #################路口1
                        global left_flag
                        if time.time()-circle_time<=10 or time.time()-circle_time>=21:
                            feedback = line_mid
                            control = self.pid_controller.update(feedback)
                            output = control
                            self.cmd_vel.linear.x = 0.2 + abs(output*0.05)
                            self.cmd_vel.angular.z = -output
                            
                        else :
                            if left_flag==0:
                                left_time=time.time()
                                left_flag=1
                            elif left_flag==1 and time.time()-left_time>=0.2:
                                self.cmd_vel.linear.x = 0.2
                                self.cmd_vel.angular.z = 0.54
                            else:
                                self.cmd_vel.linear.x = 0.2
                                self.cmd_vel.angular.z = 0
                        # global right_flag
                        # if flag=="left":
                        #     right_flag=-1
                        # elif (flag=="right") and right_flag==1:
                        #     circle_time=time.time()
                        # elif time.time()-circle_time>=0.5 and flag=="right":
                        #     right_flag=1
                        # self.cmd_vel.angular.z = rate_valuez * output * 1 * right_flag
                        # if time.time()-circle_time<=15:
                        # self.cmd_vel.angular.z = rate_valuez * abs(output) * 1
                        # else:
                        #     self.cmd_vel.angular.z = rate_valuez * output * 1
                        print(2)
                    else:  #################路口2
                        global right_flag
                        if time.time()-circle_time<=10 or time.time()-circle_time>=20:
                            feedback = line_mid
                            control = self.pid_controller.update(feedback)
                            output = control
                            self.cmd_vel.linear.x = 0.2 + abs(output*0.05)
                            self.cmd_vel.angular.z = -output
                            
                        else :
                            
                            if right_flag==0:
                                right_time=time.time()
                                right_flag=1
                            elif right_flag==1 and time.time()-right_time>=0.2:
                                self.cmd_vel.linear.x = 0.2
                                self.cmd_vel.angular.z = -0.54
                            else:
                                self.cmd_vel.linear.x = 0.2
                                self.cmd_vel.angular.z = 0
                            # feedback = line_right
                            # control = self.pid_controller.update(feedback)
                            # output = control
                            # self.cmd_vel.linear.x = 0.2 + abs(output*0.05)
                            # self.cmd_vel.angular.z = -output
                        # if flag != "left" and time.time() - circle_time <= 0.2:
                        #     self.cmd_vel.linear.z = rate_valuez * output * 1
                        # elif flag != "left":
                        #     self.cmd_vel.linear.z = 0
                        # else:
                        #     circle_time = time.time()
                        print(3)

                else:
                    pass
                    self.cmd_vel.linear.x = 0.1
                    '''
                    self.cmd_vel.linear.y =  rate_value * output * 1.2
                    self.cmd_vel.angular.z= -output *8
                    self.cmd_vel.linear.x = 0.2
                    '''
    
                    

                '''
                if (-output) > 0.4:
                    self.cmd_vel.linear.y = -0.10
                elif (-output) < -0.4:
                    self.cmd_vel.linear.y = 0.10
                else:
                    self.cmd_vel.linear.y = 0
                '''

                self.cmd_vel_pub.publish(self.cmd_vel)
                # if 0:
                # # if (if_turn) and time.time()-self.last_turn >= 5:
                #     #break
                #     self.last_turn = time.time()
                #     if self.turn_times == 0 :
                #         break
                #     self.turn_times -= 1
                #     print("直角")
                #     #break 
                #     start_time = time.time()
                #     # TRUN SHARP RIGHT/LEFT

                #     while time.time() - start_time <= 1: # turn time
                #         self.cmd_vel.linear.x = 0.25
                #         if flag == "left":
                #             self.cmd_vel.angular.z= -0.1
                #         else:
                #             self.cmd_vel.angular.z= 0.1
                        
                #         self.cmd_vel_pub.publish(self.cmd_vel)
                #     start_time = time.time()
                #     # TRUN SHARP RIGHT/LEFT

                #     while time.time() - start_time <= 0.8: # turn time
                #         if flag == "left":

                #             self.cmd_vel.angular.z= -1.5
                #         else:
                #             self.cmd_vel.angular.z= 1.5
                #         self.cmd_vel.linear.x = 0
                #         self.cmd_vel_pub.publish(self.cmd_vel)
                #     # GO FORWARD
                    
                if flag=="end" and time.time()-start_time>=2.4:
                    stop_time = time.time()
                    while time.time()- stop_time < 0.2:
                        self.cmd_vel.linear.x = 0.2
                        self.cmd_vel_pub.publish(self.cmd_vel)
                    print("结束")
                    
                    break
                elif flag!="end" and time.time()-start_time<=1.9:
                    start_time=time.time()
        except rospy.ROSInterruptException:
            pass
if __name__ == "__main__":
    line = line_finder()
    line.line_main()
