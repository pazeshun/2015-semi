#! /usr/bin/env python

import rospy
from std_msgs.msg import String
import time
import threading

class GetKeyInput(threading.Thread):
    def __init__(self):
        super(GetKeyInput, self).__init__()
        self.key = '0'
        rospy.Subscriber("input_key", String, self.sub_input_key)

    def run(self):
        rospy.spin()
        self.exit()

    def sub_input_key(self, input_key):
        self.key = input_key.data
        
    def get_key(self):
        return self.key
        
def main():
    #rospy.init_node('hiro_teaching_two_arms', anonymous=True)
    r = rospy.Rate(10)
    
    key_input_th = GetKeyInput()
    key_input_th.start()

    robot.checkEncoders()
    robot.goInitial()

    robot.startImpedance('rarm',force_gain=[2, 2, 2],moment_gain = [300, 300, 300])
    robot.startImpedance('larm',force_gain=[2, 2, 2],moment_gain = [300, 300, 300])
    robot.sc_svc.servoOff()
    time.sleep(1)
    print "Enter s to start teaching"
    while key_input_th.get_key() != 's' and not rospy.is_shutdown():
        r.sleep()
    print "start teaching"
    first_hand_angle = []
    for servo_id in robot.HandGroups['rhand'] + robot.HandGroups['lhand']:
        while not rospy.is_shutdown():
            res = robot.sc_svc.getJointAngle(servo_id)
            if res[0]:
                first_hand_angle.append(res[1])
                break
    print "Enter e to end teaching"
    whole_arm_angle_list = []
    hand_angle_list = []
    sample_num = 0
    while key_input_th.get_key() != 'e' and not rospy.is_shutdown():
        arm_angle = robot.getActualState().angle   
        whole_arm_angle_list.append(arm_angle)
        hand_angle_now = []
        for servo_id in robot.HandGroups['rhand'] + robot.HandGroups['lhand']:
            hand_angle = robot.sc_svc.getJointAngle(servo_id) 
            if hand_angle[0]:
                hand_angle_now.append(hand_angle[1])
            elif sample_num == 0:
                hand_angle_now.append(first_hand_angle[servo_id-2])
            else:
                hand_angle_now.append(hand_angle_list[sample_num-1][servo_id-2])
        hand_angle_list.append(hand_angle_now)
        sample_num += 1
        r.sleep()
    print "end teaching"
    robot.stopImpedance('rarm')
    robot.stopImpedance('larm')
    robot.sc_svc.servoOn()

    time.sleep(1)
    robot.goInitial()
    target_angle_rarm_list = []
    target_angle_larm_list = []
    tm = []
    for i in range(0,sample_num):
        target_angle_rarm_list.append(whole_arm_angle_list[i][3:9])
        target_angle_larm_list.append(whole_arm_angle_list[i][9:15])
        tm.append(0.1)
    print "start playback"
    robot.playPatternOfGroup('rarm',target_angle_rarm_list,tm)
    robot.playPatternOfGroup('larm',target_angle_larm_list,tm)
    er = rospy.Rate(5)
    for i in range(0,sample_num,2):
        for servo_id in robot.HandGroups['rhand'] + robot.HandGroups['lhand']:
            robot.sc_svc.setJointAngle(servo_id,hand_angle_list[i][servo_id-2],tm[i]*2)
        er.sleep()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException: pass
