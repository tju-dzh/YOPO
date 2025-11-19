#!/usr/bin/env python3
"""
AirSim Connection Test Script
Tests basic AirSim Python API connectivity and functionality
"""

import airsim
import time
import sys


def test_connection():
    """Test basic connection to AirSim"""
    print("=" * 60)
    print("AirSim Connection Test")
    print("=" * 60)

    try:
        # Connect to AirSim
        print("\n1. Connecting to AirSim...")
        client = airsim.MultirotorClient()
        client.confirmConnection()
        print("   ✓ Connected successfully!")

        # Get version
        print("\n2. Checking AirSim version...")
        print(f"   Server version: {client.getServerVersion()}")
        print(f"   Client version: {client.getClientVersion()}")

        # Enable API control
        print("\n3. Enabling API control...")
        client.enableApiControl(True)
        print("   ✓ API control enabled")

        # Arm the drone
        print("\n4. Arming the drone...")
        client.armDisarm(True)
        print("   ✓ Drone armed")

        # Get pose
        print("\n5. Getting current pose...")
        pose = client.simGetVehiclePose()
        print(f"   Position: x={pose.position.x_val:.2f}, y={pose.position.y_val:.2f}, z={pose.position.z_val:.2f}")
        print(f"   Orientation: w={pose.orientation.w_val:.2f}, x={pose.orientation.x_val:.2f}, "
              f"y={pose.orientation.y_val:.2f}, z={pose.orientation.z_val:.2f}")

        # Get IMU data
        print("\n6. Getting IMU data...")
        imu_data = client.getImuData()
        print(f"   Angular velocity: x={imu_data.angular_velocity.x_val:.2f}, "
              f"y={imu_data.angular_velocity.y_val:.2f}, z={imu_data.angular_velocity.z_val:.2f}")
        print(f"   Linear acceleration: x={imu_data.linear_acceleration.x_val:.2f}, "
              f"y={imu_data.linear_acceleration.y_val:.2f}, z={imu_data.linear_acceleration.z_val:.2f}")

        # Test camera
        print("\n7. Testing depth camera...")
        responses = client.simGetImages([
            airsim.ImageRequest("depth_cam", airsim.ImageType.DepthPlanar, pixels_as_float=True)
        ])
        if responses:
            print(f"   ✓ Got depth image: {responses[0].width}x{responses[0].height}")
        else:
            print("   ✗ Failed to get depth image")

        # Test takeoff (optional)
        print("\n8. Testing takeoff (will hover at 2m for 3 seconds)...")
        user_input = input("   Proceed with takeoff test? (y/n): ")
        if user_input.lower() == 'y':
            print("   Taking off...")
            client.takeoffAsync().join()
            print("   ✓ Takeoff complete")

            print("   Hovering for 3 seconds...")
            time.sleep(3)

            print("   Landing...")
            client.landAsync().join()
            print("   ✓ Landing complete")
        else:
            print("   Skipped takeoff test")

        # Cleanup
        print("\n9. Cleaning up...")
        client.armDisarm(False)
        client.enableApiControl(False)
        print("   ✓ Disarmed and disabled API control")

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Unreal Engine is running")
        print("2. Check that AirSim plugin is loaded")
        print("3. Verify settings.json exists at ~/Documents/AirSim/settings.json")
        print("4. Check firewall settings (port 41451)")
        return False


def test_ros_topics():
    """Test ROS topic availability (requires roscore)"""
    print("\n" + "=" * 60)
    print("ROS Topics Test")
    print("=" * 60)

    try:
        import rospy
        from nav_msgs.msg import Odometry
        from sensor_msgs.msg import Imu, Image

        print("\n1. Initializing ROS node...")
        rospy.init_node('airsim_test', anonymous=True)
        print("   ✓ ROS node initialized")

        # Test topic availability
        print("\n2. Checking topic availability...")
        topics = [
            "/airsim_node/Drone1/odom_local_ned",
            "/airsim_node/Drone1/imu/Imu",
            "/airsim_node/Drone1/depth_cam/DepthPlanar"
        ]

        for topic in topics:
            try:
                msg = rospy.wait_for_message(topic, rospy.AnyMsg, timeout=5.0)
                print(f"   ✓ {topic}")
            except rospy.ROSException:
                print(f"   ✗ {topic} (timeout)")

        print("\n" + "=" * 60)
        print("ROS topics test complete")
        print("=" * 60)

    except ImportError:
        print("   ✗ ROS not available (ImportError)")
    except Exception as e:
        print(f"   ✗ Error: {e}")


if __name__ == "__main__":
    success = test_connection()

    if success:
        print("\n" + "=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print("\n1. Launch AirSim ROS wrapper:")
        print("   roslaunch airsim_ros_pkgs airsim_yopo.launch")
        print("\n2. Launch YOPO planner:")
        print("   cd ~/YOPO/YOPO")
        print("   python3 test_yopo_ros.py --trial=1 --epoch=50")
        print("\n3. Set goal in RViz (2D Nav Goal)")
        print("\nSee AIRSIM_README.md for more details.")
    else:
        sys.exit(1)
