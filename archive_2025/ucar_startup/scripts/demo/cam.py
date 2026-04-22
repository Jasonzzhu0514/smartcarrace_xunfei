#!/usr/bin/env python3
import rospy
import numpy as np
import cv2
from sensor_msgs.msg import Image

class RawImageViewer:
    def __init__(self):
        rospy.init_node('raw_image_viewer', anonymous=True)

        self.image_topic = "/usb_cam/image_raw"
        self.color_sub = rospy.Subscriber(self.image_topic, Image, self.image_callback, queue_size=1, buff_size=52428800)

        rospy.loginfo("Subscribed to topic: %s", self.image_topic)

    def image_callback(self, image):
        try:
            # 将ROS图像数据转为NumPy数组
            color_image = np.frombuffer(image.data, dtype=np.uint8).reshape(image.height, image.width, -1)

            # 检查图像通道数并转为RGB格式（OpenCV使用BGR）
            if color_image.shape[2] == 4:
                color_image = cv2.cvtColor(color_image, cv2.COLOR_RGBA2BGR)
            elif color_image.shape[2] == 3:
                color_image = cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)
            else:
                rospy.logwarn("Unknown image format with shape: %s", str(color_image.shape))
                return

            # 显示图像
            cv2.imshow("Raw Camera View", color_image)
            cv2.waitKey(1)

        except Exception as e:
            rospy.logerr(f"Error in image_callback: {str(e)}")

    def spin(self):
        rospy.spin()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    try:
        viewer = RawImageViewer()
        viewer.spin()
    except rospy.ROSInterruptException:
        pass
