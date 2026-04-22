#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
from std_msgs.msg import String

def publish_tts_message(text):
    # 初始化ROS节点（匿名=True表示可以运行多个实例）
    rospy.init_node('tts_publisher', anonymous=True)
    
    # 创建一个发布者，发布到/tts_input话题，消息类型为std_msgs/String
    pub = rospy.Publisher('/tts_input', String, queue_size=10)
    
    # 等待连接建立
    rospy.sleep(0.1)
    
    # 创建消息内容
    message = text
    msg = String()
    msg.data = message
    
    # 发布消息
    pub.publish(msg)
    rospy.loginfo("已发布消息: %s", message)

def publish_qrcode_result():
    # 初始化 ROS 节点
    rospy.init_node('qrcode_publisher', anonymous=True)
    
    # 创建发布者，发布到名为 /qrcode_result 的话题，消息类型为 String
    pub = rospy.Publisher('/qrcode_result', String, queue_size=10)

    rate = rospy.Rate(10)  # 发布频率为 10Hz

    # 假设这个变量是你的识别结果
    qrcode_result = "Dessert"  

    while not rospy.is_shutdown():
        # 将结果转换为字符串发送
        result_str = qrcode_result if qrcode_result is not None else "None"
        pub.publish(result_str)
        rospy.loginfo(f"📤 发布二维码识别结果: {result_str}")
        rate.sleep()

# if __name__ == '__main__':
#     try:
#         publish_qrcode_result()
#     except rospy.ROSInterruptException:
#         pass

if __name__ == '__main__':
    txt = "路口"
    try:
        publish_tts_message(txt)
    except rospy.ROSInterruptException:
        pass