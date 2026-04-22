#!/usr/bin/env python3
import os
import rospy
from std_msgs.msg import String
import last

def stop_camera():
    rospy.init_node('camera_controller', anonymous=True)
    
    rospy.loginfo("初始化成功")
    pub = rospy.Publisher('/camera_control', String, queue_size=1)

    # 等待 publisher 注册完成
    rospy.sleep(0.5)

    rospy.loginfo("📷 正在发布摄像头停止指令...")
    pub.publish("stop")

    # 再次等待确保消息发送成功
    rospy.sleep(0.5)

    rospy.loginfo("✅ 摄像头停止指令已发布，程序退出")

# stop_camera()


last.run()
# rospy.init_node('rknn')
# rospy.loginfo('init successful!!')
# os.system('python /home/iflytek/ucar_ws/src/ucar_startup/scripts/rk.py')
# os.system('python --version')

# def open_terminal(commands):
#     cmd_list = []
#     for cmd in commands:
#         cmd_list.append(""" gnome-terminal --tab -e "bash -c '%s;exec bash'" >/dev/null  2>&1 """ %cmd)

# if __name__ == "__main__":
#     command_list = [
#         "roscore",
#         "python /home/iflytek/ucar_ws/src/ucar_startup/scripts/rk.py"
#     ]
#     open_terminal(command_list)