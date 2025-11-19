#!/usr/bin/env python3
"""
AirSim to YOPO Interface Bridge Node
Converts AirSim ROS topics to YOPO-compatible topics

Topic Mapping:
- AirSim Odometry (NED) -> YOPO Odometry (ENU)
- AirSim IMU -> YOPO IMU
- AirSim DepthPlanar -> YOPO Depth Image (32FC1)
"""

import rospy
import numpy as np
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu, Image
from geometry_msgs.msg import Quaternion
from scipy.spatial.transform import Rotation as R
import cv2
from cv_bridge import CvBridge


class AirSimYopoBridge:
    def __init__(self):
        rospy.init_node('airsim_yopo_bridge', anonymous=False)

        # Parameters
        self.airsim_odom_topic = rospy.get_param('~airsim_odom_topic', '/airsim_node/Drone1/odom_local_ned')
        self.airsim_imu_topic = rospy.get_param('~airsim_imu_topic', '/airsim_node/Drone1/imu/Imu')
        self.airsim_depth_topic = rospy.get_param('~airsim_depth_topic', '/airsim_node/Drone1/depth_cam/DepthPlanar')

        self.yopo_odom_topic = rospy.get_param('~yopo_odom_topic', '/sim/odom')
        self.yopo_imu_topic = rospy.get_param('~yopo_imu_topic', '/sim/imu')
        self.yopo_depth_topic = rospy.get_param('~yopo_depth_topic', '/depth_image')

        # CvBridge for image conversion
        self.bridge = CvBridge()

        # Publishers
        self.odom_pub = rospy.Publisher(self.yopo_odom_topic, Odometry, queue_size=10)
        self.imu_pub = rospy.Publisher(self.yopo_imu_topic, Imu, queue_size=10)
        self.depth_pub = rospy.Publisher(self.yopo_depth_topic, Image, queue_size=10)

        # Subscribers
        self.odom_sub = rospy.Subscriber(self.airsim_odom_topic, Odometry,
                                         self.odom_callback, queue_size=10, tcp_nodelay=True)
        self.imu_sub = rospy.Subscriber(self.airsim_imu_topic, Imu,
                                        self.imu_callback, queue_size=10, tcp_nodelay=True)
        self.depth_sub = rospy.Subscriber(self.airsim_depth_topic, Image,
                                          self.depth_callback, queue_size=10, tcp_nodelay=True)

        rospy.loginfo("AirSim-YOPO Bridge Node Started!")
        rospy.loginfo(f"  Odom: {self.airsim_odom_topic} -> {self.yopo_odom_topic}")
        rospy.loginfo(f"  IMU:  {self.airsim_imu_topic} -> {self.yopo_imu_topic}")
        rospy.loginfo(f"  Depth: {self.airsim_depth_topic} -> {self.yopo_depth_topic}")

    def ned_to_enu_position(self, ned_pos):
        """Convert NED position to ENU position"""
        # NED: x=North, y=East, z=Down
        # ENU: x=East, y=North, z=Up
        return np.array([ned_pos.y, ned_pos.x, -ned_pos.z])

    def ned_to_enu_quaternion(self, ned_quat):
        """Convert NED quaternion to ENU quaternion"""
        # AirSim uses NED frame, YOPO uses ENU frame
        # Rotation: [q_x, q_y, q_z, q_w]
        q_ned = np.array([ned_quat.x, ned_quat.y, ned_quat.z, ned_quat.w])

        # NED to ENU rotation matrix
        # R_enu = R_z(pi/2) * R_x(pi) * R_ned
        R_ned_obj = R.from_quat(q_ned)
        R_ned_to_enu = R.from_euler('zx', [90, 180], degrees=True)
        R_enu = R_ned_to_enu * R_ned_obj

        q_enu = R_enu.as_quat()  # [x, y, z, w]
        return Quaternion(x=q_enu[0], y=q_enu[1], z=q_enu[2], w=q_enu[3])

    def ned_to_enu_velocity(self, ned_vel):
        """Convert NED velocity to ENU velocity"""
        return np.array([ned_vel.y, ned_vel.x, -ned_vel.z])

    def ned_to_enu_angular_velocity(self, ned_omega):
        """Convert NED angular velocity to ENU angular velocity"""
        return np.array([ned_omega.y, ned_omega.x, -ned_omega.z])

    def odom_callback(self, msg):
        """Convert AirSim Odometry (NED) to YOPO Odometry (ENU)"""
        odom_enu = Odometry()
        odom_enu.header = msg.header
        odom_enu.header.frame_id = "world"
        odom_enu.child_frame_id = "base_link"

        # Position: NED -> ENU
        pos_enu = self.ned_to_enu_position(msg.pose.pose.position)
        odom_enu.pose.pose.position.x = pos_enu[0]
        odom_enu.pose.pose.position.y = pos_enu[1]
        odom_enu.pose.pose.position.z = pos_enu[2]

        # Orientation: NED -> ENU
        odom_enu.pose.pose.orientation = self.ned_to_enu_quaternion(msg.pose.pose.orientation)

        # Linear velocity: NED -> ENU
        vel_enu = self.ned_to_enu_velocity(msg.twist.twist.linear)
        odom_enu.twist.twist.linear.x = vel_enu[0]
        odom_enu.twist.twist.linear.y = vel_enu[1]
        odom_enu.twist.twist.linear.z = vel_enu[2]

        # Angular velocity: NED -> ENU
        omega_enu = self.ned_to_enu_angular_velocity(msg.twist.twist.angular)
        odom_enu.twist.twist.angular.x = omega_enu[0]
        odom_enu.twist.twist.angular.y = omega_enu[1]
        odom_enu.twist.twist.angular.z = omega_enu[2]

        # Covariance (copy as-is, assuming small values)
        odom_enu.pose.covariance = msg.pose.covariance
        odom_enu.twist.covariance = msg.twist.covariance

        self.odom_pub.publish(odom_enu)

    def imu_callback(self, msg):
        """Convert AirSim IMU (NED) to YOPO IMU (ENU)"""
        imu_enu = Imu()
        imu_enu.header = msg.header
        imu_enu.header.frame_id = "base_link"

        # Orientation: NED -> ENU
        imu_enu.orientation = self.ned_to_enu_quaternion(msg.orientation)

        # Angular velocity: NED -> ENU
        omega_enu = self.ned_to_enu_angular_velocity(msg.angular_velocity)
        imu_enu.angular_velocity.x = omega_enu[0]
        imu_enu.angular_velocity.y = omega_enu[1]
        imu_enu.angular_velocity.z = omega_enu[2]

        # Linear acceleration: NED -> ENU
        acc_enu = self.ned_to_enu_velocity(msg.linear_acceleration)
        imu_enu.linear_acceleration.x = acc_enu[0]
        imu_enu.linear_acceleration.y = acc_enu[1]
        imu_enu.linear_acceleration.z = acc_enu[2]

        # Covariance
        imu_enu.orientation_covariance = msg.orientation_covariance
        imu_enu.angular_velocity_covariance = msg.angular_velocity_covariance
        imu_enu.linear_acceleration_covariance = msg.linear_acceleration_covariance

        self.imu_pub.publish(imu_enu)

    def depth_callback(self, msg):
        """
        Convert AirSim DepthPlanar to YOPO Depth Image (32FC1)

        AirSim DepthPlanar: Distance along camera's principal axis (meters)
        YOPO expects: 32FC1 format depth image
        """
        try:
            # Convert from ROS Image to OpenCV format
            # AirSim publishes DepthPlanar as 32FC1 (float32, 1 channel)
            depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="32FC1")

            # AirSim depth is in meters, which matches YOPO's expectation
            # No conversion needed for units

            # Handle invalid depth values (inf, nan)
            depth_image = np.nan_to_num(depth_image, nan=0.0, posinf=20.0, neginf=0.0)

            # Clip to reasonable range (0.04m to 20m as per YOPO config)
            depth_image = np.clip(depth_image, 0.04, 20.0)

            # Convert back to ROS Image message (32FC1)
            depth_msg = self.bridge.cv2_to_imgmsg(depth_image, encoding="32FC1")
            depth_msg.header = msg.header
            depth_msg.header.frame_id = "depth_cam"

            self.depth_pub.publish(depth_msg)

        except Exception as e:
            rospy.logerr(f"Error processing depth image: {e}")

    def spin(self):
        rospy.spin()


if __name__ == '__main__':
    try:
        bridge = AirSimYopoBridge()
        bridge.spin()
    except rospy.ROSInterruptException:
        pass
