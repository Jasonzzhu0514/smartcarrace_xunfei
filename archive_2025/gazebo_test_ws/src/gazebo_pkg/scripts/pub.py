#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
from std_msgs.msg import String

def publish_qrcode_result():
    # 初始化 ROS 节点
    rospy.init_node('qrcode_publisher', anonymous=True)
    
    # 创建发布者，发布到名为 /qrcode_result 的话题，消息类型为 String
    pub = rospy.Publisher('/room_result', String, queue_size=10)

    rate = rospy.Rate(10)  # 发布频率为 10Hz

    # 假设这个变量是你的识别结果
    Room = "A"  

    while not rospy.is_shutdown():
        # 将结果转换为字符串发送
        result_str = Room if Room is not None else "None"
        pub.publish(result_str)
        rospy.loginfo(f"📤 识别结果: {result_str}")
        rate.sleep()

if __name__ == '__main__':
    try:
        publish_qrcode_result()
    except rospy.ROSInterruptException:
        pass
