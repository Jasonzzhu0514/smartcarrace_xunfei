#!/usr/bin/env python
import rospy
from geometry_msgs.msg import Twist
from ucar_startup.msg import DetectResult

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
        self.target_center = 40.0
        self.center_threshold = 8.0

        rospy.loginfo("Start rotating to align with category: %s", target_category)
        self.rotate()

    def rotate(self):
        rate = rospy.Rate(10)
        twist = Twist()
        twist.angular.z = 0.8

        while not rospy.is_shutdown() and not self.target_found:
            self.cmd_pub.publish(twist)
            rate.sleep()

        self.stop()

    def stop(self):
        twist = Twist()
        self.cmd_pub.publish(twist)
        rospy.loginfo("Target aligned. Rotation stopped.")

    def detect_callback(self, msg):
        class_id = msg.detect_class
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

if __name__ == '__main__':
    try:
        # 你可以修改下面的参数为 "Fruit"、"Vegetable" 或 "Dessert"
        AlignToCategory(target_category="Dessert")
    except rospy.ROSInterruptException:
        pass

''' #没有对比的，单单旋转
#!/usr/bin/env python
import rospy
from geometry_msgs.msg import Twist
from ucar_startup.msg import DetectResult

class AlignToCenter:
    def __init__(self):
        rospy.init_node('align_to_center_node')
        
        self.cmd_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        rospy.Subscriber('/rknn_detect_result', DetectResult, self.detect_callback)

        self.target_center = 325.0
        self.center_threshold = 8.0   # 允许小范围偏差
        self.aligned = False

        rospy.loginfo("Node initialized, start rotating...")
        self.rotate()

    def rotate(self):
        rate = rospy.Rate(20)
        twist = Twist()
        twist.angular.z = 0.5  # 正方向旋转，调整角速度大小

        while not rospy.is_shutdown() and not self.aligned:
            self.cmd_pub.publish(twist)
            rate.sleep()

        # 停止转动
        self.stop()

    def stop(self):
        twist = Twist()
        self.cmd_pub.publish(twist)
        rospy.loginfo("Box centered. Rotation stopped.")

    def detect_callback(self, msg):
        box_center = msg.box_center
        rospy.loginfo("Detect box_center: %.2f" % box_center)

        if abs(box_center - self.target_center) <= self.center_threshold:
            self.aligned = True

if __name__ == '__main__':
    try:
        AlignToCenter()
    except rospy.ROSInterruptException:
        pass
'''
