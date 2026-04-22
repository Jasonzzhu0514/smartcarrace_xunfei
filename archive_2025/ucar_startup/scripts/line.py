#!/usr/bin/env python
# -*- coding: utf-8 -*-
import rospy
import math
import time
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from new_tinkin import LineFinder

# 全局标志变量
round = True
circle_flag = 1
right_flag = 0
left_flag = 0
bizhang_start_flag = 0
bizhang_end_flag = 0
bizhang_flag = 0

class CloseRangeDetector:
    def __init__(self):
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.scan_sub = rospy.Subscriber('/scan', LaserScan, self.scan_callback)

        self.min_valid_range = 0.1
        self.scan_angle = 30
        self.detection_range = 0.26

        self.lateral_speed = 0.3
        self.forward_speed = 0.3
        self.move_state = "FORWARD"
        self.action_start_time = 0

        self.trigger_avoidance = False  # ✅ 外部使用：是否进入避障状态

    def scan_callback(self, scan_data):
        total_angles = len(scan_data.ranges)
        center_index = total_angles // 2
        start_idx = center_index - int(self.scan_angle / 2 * total_angles / 360)
        end_idx = center_index + int(self.scan_angle / 2 * total_angles / 360)

        valid_ranges = [
            dist for dist in scan_data.ranges[start_idx:end_idx]
            if not math.isnan(dist) and self.min_valid_range < dist <= self.detection_range
        ]

        if valid_ranges and self.move_state == "FORWARD" and not self.trigger_avoidance:
            rospy.logwarn("⚠️ 前方检测到障碍物，启动避障！")
            self.move_state = "LATERAL_RIGHT"
            self.action_start_time = time.time()
            self.trigger_avoidance = True

    def execute_avoidance_sequence(self):
        current_time = time.time()
        elapsed = current_time - self.action_start_time
        move_cmd = Twist()

        if self.move_state == "LATERAL_RIGHT":
            move_cmd.linear.y = self.lateral_speed
            if elapsed >= 1.7:
                rospy.loginfo("✅ 右移完成，前进中...")
                self.move_state = "AVOID_FORWARD"
                self.action_start_time = current_time

        elif self.move_state == "AVOID_FORWARD":
            move_cmd.linear.x = self.forward_speed
            if elapsed >= 1.9:
                rospy.loginfo("✅ 前进完成，开始左移")
                self.move_state = "LATERAL_LEFT"
                self.action_start_time = current_time

        elif self.move_state == "LATERAL_LEFT":
            move_cmd.linear.y = -self.lateral_speed
            if elapsed >= 1.9:
                rospy.loginfo("✅ 避障完成，恢复巡线")
                self.move_state = "FORWARD"
                self.trigger_avoidance = False  # ✅ 解除避障标志
                move_cmd = Twist()

        self.cmd_vel_pub.publish(move_cmd)


class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.prev_error = 0
        self.integral = 0

    def update(self, feedback):
        global circle_flag
        if left_flag and circle_flag:
            circle_flag = 0
            self.prev_error = 0
            self.integral = 0
        if right_flag and circle_flag:
            circle_flag = 0
            self.prev_error = 0
            self.integral = 0

        error = self.setpoint - feedback
        self.integral += error
        derivative = error - self.prev_error
        self.prev_error = error
        return self.Kp * error + self.Ki * self.integral + self.Kd * derivative


class line_finder:
    def __init__(self,entry):
        self.pid_controller = PIDController(Kp=4, Ki=0, Kd=2, setpoint=0.5)
        rospy.init_node('line_patrol_node', anonymous=True) #节点初始化！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.cmd_vel = Twist()
        self.detector = CloseRangeDetector()  # ✅ 避障模块
        self.turn_times = 2
        self.entry = entry

    def line_main(self):
        try:
            line = LineFinder()
            start_time = time.time()
            circle_time = time.time()
            left_time = time.time()
            right_time = time.time()
            # bizhang_time = time.time()

            rate = rospy.Rate(10)
            
            while not rospy.is_shutdown():
                global bizhang_end_flag #若正在避障，暂停巡线逻辑
                
                if self.detector.trigger_avoidance :#and not (flag!="end" and time.time()-start_time<=1.9):
                    global bizhang_start_flag
                    self.detector.execute_avoidance_sequence()
                    rate.sleep()
                    bizhang_start_flag=1
                    continue
                if bizhang_start_flag==1 and bizhang_end_flag==0:
                    bizhang_end_flag=1
                    start_time=time.time()-1.5
                # 正常巡线逻辑
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
                # time.time(),start_time,
                print(time.time()-start_time,line_left,line_right,line_mid,flag)
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
                    if self.entry:  #################路口1
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
                        if time.time()-circle_time<=11 or time.time()-circle_time>=22:
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
                                self.cmd_vel.angular.z = -0.48
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
                
                
                global bizhang_flag
                if flag=="end" and time.time()-start_time>=1.5:
                    # stop_time = time.time()
                    while flag=="end":# time.time()- stop_time < 0.2:
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
                        self.cmd_vel.linear.x = 0.2
                        self.cmd_vel_pub.publish(self.cmd_vel)
                        print(time.time()-start_time,line_left,line_right,line_mid,flag)
                    
                    stop_time = time.time()
                    while time.time()- stop_time < 0.6:
                        
                        self.cmd_vel.linear.x = 0.2
                        self.cmd_vel_pub.publish(self.cmd_vel)
                    
                    print("结束")
                    break
                elif bizhang_flag==0 and bizhang_end_flag==1 and flag=="end":
                    bizhang_flag=1
                    start_time=time.time()-1.1
                    # bizhang_time=time.time()
                elif flag!="end" and bizhang_flag==0:
                    start_time=time.time()

                # elif time.time()-bizhang_time<0.27 and flag=="end":
                #     bizhang_time=time.time()
        except rospy.ROSInterruptException:
            pass

def run(entry):
    line = line_finder(entry)
    line.line_main()


if __name__ == "__main__":
    line = line_finder(False)
    line.line_main()
