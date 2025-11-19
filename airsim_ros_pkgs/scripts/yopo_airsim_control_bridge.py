#!/usr/bin/env python3
"""
YOPO to AirSim Control Bridge Node
Converts YOPO PositionCommand to AirSim control commands

Control Modes:
1. Position mode: Send position + velocity + yaw commands
2. Velocity mode: Send velocity commands only (faster response)
"""

import rospy
import numpy as np
from geometry_msgs.msg import PoseStamped, TwistStamped, Vector3
from airsim_ros_pkgs.msg import VelCmd, PosCmd
from scipy.spatial.transform import Rotation as R
import sys
import os

# Add YOPO path to import PositionCommand
sys.path.append(os.path.join(os.path.dirname(__file__), '../../YOPO/control_msg'))
try:
    from _PositionCommand import PositionCommand
except ImportError:
    rospy.logerr("Cannot import PositionCommand. Make sure YOPO/control_msg is built.")
    # Fallback: use quadrotor_msgs
    from quadrotor_msgs.msg import PositionCommand


class YopoAirSimControlBridge:
    def __init__(self):
        rospy.init_node('yopo_airsim_control_bridge', anonymous=False)

        # Parameters
        self.yopo_ctrl_topic = rospy.get_param('~yopo_ctrl_topic', '/so3_control/pos_cmd')
        self.airsim_ctrl_topic = rospy.get_param('~airsim_ctrl_topic', '/airsim_node/Drone1/vel_cmd_body_frame')
        self.airsim_pose_topic = rospy.get_param('~airsim_pose_topic', '/airsim_node/Drone1/pose_cmd_body_frame')
        self.control_mode = rospy.get_param('~control_mode', 'position')  # 'velocity' or 'position'

        # Publishers (depends on control mode)
        if self.control_mode == 'velocity':
            self.vel_pub = rospy.Publisher(self.airsim_ctrl_topic, TwistStamped, queue_size=10)
            rospy.loginfo(f"Control Mode: VELOCITY")
        else:  # position mode
            self.pose_pub = rospy.Publisher(self.airsim_pose_topic, PoseStamped, queue_size=10)
            rospy.loginfo(f"Control Mode: POSITION")

        # Subscriber
        self.ctrl_sub = rospy.Subscriber(self.yopo_ctrl_topic, PositionCommand,
                                         self.control_callback, queue_size=10, tcp_nodelay=True)

        # State variables
        self.last_cmd_time = None
        self.cmd_timeout = 0.5  # seconds

        rospy.loginfo("YOPO-AirSim Control Bridge Node Started!")
        rospy.loginfo(f"  YOPO Control: {self.yopo_ctrl_topic}")
        rospy.loginfo(f"  AirSim Control: {self.airsim_ctrl_topic if self.control_mode == 'velocity' else self.airsim_pose_topic}")

    def enu_to_ned_position(self, enu_pos):
        """Convert ENU position to NED position"""
        # ENU: x=East, y=North, z=Up
        # NED: x=North, y=East, z=Down
        return np.array([enu_pos[1], enu_pos[0], -enu_pos[2]])

    def enu_to_ned_velocity(self, enu_vel):
        """Convert ENU velocity to NED velocity"""
        return np.array([enu_vel[1], enu_vel[0], -enu_vel[2]])

    def enu_yaw_to_ned_yaw(self, enu_yaw):
        """
        Convert ENU yaw to NED yaw

        ENU: 0 = East, +90 = North, +180/-180 = West, -90 = South
        NED: 0 = North, +90 = East, +180/-180 = South, -90 = West

        Conversion: yaw_ned = -(yaw_enu - pi/2)
        """
        ned_yaw = -(enu_yaw - np.pi / 2)
        # Normalize to [-pi, pi]
        while ned_yaw > np.pi:
            ned_yaw -= 2 * np.pi
        while ned_yaw < -np.pi:
            ned_yaw += 2 * np.pi
        return ned_yaw

    def control_callback(self, msg):
        """
        Convert YOPO PositionCommand to AirSim control command

        YOPO PositionCommand (ENU):
        - position: target position (x, y, z)
        - velocity: target velocity (vx, vy, vz)
        - acceleration: feedforward acceleration
        - yaw: target yaw angle
        - yaw_dot: yaw rate
        """
        # Check trajectory flag
        if msg.trajectory_flag == msg.TRAJECTORY_STATUS_EMPTY:
            rospy.loginfo_throttle(5.0, "Received EMPTY trajectory flag, holding position")
            return

        self.last_cmd_time = rospy.Time.now()

        if self.control_mode == 'velocity':
            self.send_velocity_command(msg)
        else:  # position mode
            self.send_position_command(msg)

    def send_velocity_command(self, msg):
        """Send velocity command to AirSim"""
        # Convert ENU velocity to NED
        vel_enu = np.array([msg.velocity.x, msg.velocity.y, msg.velocity.z])
        vel_ned = self.enu_to_ned_velocity(vel_enu)

        # Create TwistStamped message
        twist_msg = TwistStamped()
        twist_msg.header.stamp = rospy.Time.now()
        twist_msg.header.frame_id = "world"

        # Linear velocity (NED)
        twist_msg.twist.linear.x = vel_ned[0]
        twist_msg.twist.linear.y = vel_ned[1]
        twist_msg.twist.linear.z = vel_ned[2]

        # Angular velocity (yaw rate)
        # Convert ENU yaw_dot to NED yaw_dot
        yaw_dot_ned = -msg.yaw_dot
        twist_msg.twist.angular.x = 0.0
        twist_msg.twist.angular.y = 0.0
        twist_msg.twist.angular.z = yaw_dot_ned

        self.vel_pub.publish(twist_msg)

    def send_position_command(self, msg):
        """Send position command to AirSim"""
        # Convert ENU position to NED
        pos_enu = np.array([msg.position.x, msg.position.y, msg.position.z])
        pos_ned = self.enu_to_ned_position(pos_enu)

        # Convert ENU yaw to NED yaw
        yaw_ned = self.enu_yaw_to_ned_yaw(msg.yaw)

        # Create quaternion from yaw (NED frame)
        # In NED, yaw rotation is around z-axis (down)
        quat_ned = R.from_euler('z', yaw_ned).as_quat()  # [x, y, z, w]

        # Create PoseStamped message
        pose_msg = PoseStamped()
        pose_msg.header.stamp = rospy.Time.now()
        pose_msg.header.frame_id = "world"

        # Position (NED)
        pose_msg.pose.position.x = pos_ned[0]
        pose_msg.pose.position.y = pos_ned[1]
        pose_msg.pose.position.z = pos_ned[2]

        # Orientation (quaternion in NED)
        pose_msg.pose.orientation.x = quat_ned[0]
        pose_msg.pose.orientation.y = quat_ned[1]
        pose_msg.pose.orientation.z = quat_ned[2]
        pose_msg.pose.orientation.w = quat_ned[3]

        self.pose_pub.publish(pose_msg)

    def spin(self):
        rospy.spin()


if __name__ == '__main__':
    try:
        bridge = YopoAirSimControlBridge()
        bridge.spin()
    except rospy.ROSInterruptException:
        pass
