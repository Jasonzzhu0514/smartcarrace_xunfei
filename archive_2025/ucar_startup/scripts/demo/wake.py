#!/usr/bin/env python3
# coding=utf-8

import rospy
from std_srvs.srv import Trigger, TriggerRequest, TriggerResponse

def get_test_client():
    rospy.wait_for_service('/speech_command_node/get_test_server')
    try:
        get_test = rospy.ServiceProxy('/speech_command_node/get_test_server', Trigger)
        response = get_test()
        return response.success, response.message
    except rospy.ServiceException as e:
        print("Service call failed: %s" % e)

if __name__ == "__main__":
    rospy.init_node('get_test_client')
    # Call get_test service
    print("Calling get_test service...")
    success, message = get_test_client()
    print("Response from get_test service: success=%s, message=%s" % (success, message))
