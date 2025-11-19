#!/bin/bash
###############################################################################
# AirSim + ROS Noetic Setup Script for YOPO Project
# Ubuntu 20.04 + ROS Noetic + AirSim 1.8.1 + Unreal Engine 4.27.2
###############################################################################

set -e  # Exit on error

echo "=========================================="
echo "YOPO AirSim Integration Setup"
echo "=========================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get workspace root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
YOPO_ROOT="${SCRIPT_DIR}"
CATKIN_WS="${YOPO_ROOT}/Controller"

echo -e "${GREEN}YOPO Root: ${YOPO_ROOT}${NC}"
echo -e "${GREEN}Catkin Workspace: ${CATKIN_WS}${NC}"

###############################################################################
# 1. Check System Requirements
###############################################################################
echo ""
echo "=========================================="
echo "1. Checking System Requirements"
echo "=========================================="

# Check Ubuntu version
if ! lsb_release -d | grep -q "20.04"; then
    echo -e "${YELLOW}Warning: This script is designed for Ubuntu 20.04${NC}"
fi

# Check ROS Noetic
if [ -f /opt/ros/noetic/setup.bash ]; then
    echo -e "${GREEN}✓ ROS Noetic found${NC}"
    source /opt/ros/noetic/setup.bash
else
    echo -e "${RED}✗ ROS Noetic not found. Please install ROS Noetic first.${NC}"
    echo "Visit: http://wiki.ros.org/noetic/Installation/Ubuntu"
    exit 1
fi

###############################################################################
# 2. Install System Dependencies
###############################################################################
echo ""
echo "=========================================="
echo "2. Installing System Dependencies"
echo "=========================================="

sudo apt-get update

# ROS packages
echo "Installing ROS packages..."
sudo apt-get install -y \
    ros-noetic-cv-bridge \
    ros-noetic-image-transport \
    ros-noetic-tf2-ros \
    ros-noetic-mavros \
    ros-noetic-mavros-msgs

# Python dependencies
echo "Installing Python dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-opencv \
    python3-numpy \
    python3-scipy

pip3 install --user scipy numpy opencv-python

echo -e "${GREEN}✓ System dependencies installed${NC}"

###############################################################################
# 3. Clone and Build AirSim ROS Wrapper
###############################################################################
echo ""
echo "=========================================="
echo "3. Setting up AirSim ROS Wrapper"
echo "=========================================="

AIRSIM_ROS_DIR="${CATKIN_WS}/src/airsim_ros_pkgs"

# Check if AirSim ROS wrapper exists
if [ ! -d "${AIRSIM_ROS_DIR}" ]; then
    echo "Cloning AirSim ROS wrapper..."
    cd "${CATKIN_WS}/src"
    git clone https://github.com/microsoft/AirSim.git --depth 1 --branch v1.8.1

    # Copy ROS wrapper
    cp -r AirSim/ros/src/airsim_ros_pkgs ./

    # Clean up
    rm -rf AirSim

    echo -e "${GREEN}✓ AirSim ROS wrapper cloned${NC}"
else
    echo -e "${YELLOW}AirSim ROS wrapper already exists, skipping clone${NC}"
fi

# Copy our custom bridge package
echo "Copying custom bridge package..."
if [ -d "${YOPO_ROOT}/airsim_ros_pkgs" ]; then
    # Merge our custom files with AirSim ROS wrapper
    cp -r "${YOPO_ROOT}/airsim_ros_pkgs/"* "${AIRSIM_ROS_DIR}/"
    echo -e "${GREEN}✓ Custom bridge package copied${NC}"
else
    echo -e "${RED}✗ Custom bridge package not found at ${YOPO_ROOT}/airsim_ros_pkgs${NC}"
    exit 1
fi

###############################################################################
# 4. Configure AirSim Settings
###############################################################################
echo ""
echo "=========================================="
echo "4. Configuring AirSim Settings"
echo "=========================================="

AIRSIM_SETTINGS_DIR="$HOME/Documents/AirSim"
mkdir -p "${AIRSIM_SETTINGS_DIR}"

if [ -f "${YOPO_ROOT}/airsim_config/settings.json" ]; then
    cp "${YOPO_ROOT}/airsim_config/settings.json" "${AIRSIM_SETTINGS_DIR}/settings.json"
    echo -e "${GREEN}✓ AirSim settings.json copied to ${AIRSIM_SETTINGS_DIR}${NC}"
else
    echo -e "${RED}✗ settings.json not found at ${YOPO_ROOT}/airsim_config/settings.json${NC}"
    exit 1
fi

###############################################################################
# 5. Build ROS Workspace
###############################################################################
echo ""
echo "=========================================="
echo "5. Building ROS Workspace"
echo "=========================================="

cd "${CATKIN_WS}"

# Source ROS
source /opt/ros/noetic/setup.bash

# Build
echo "Building catkin workspace..."
catkin_make

# Check build status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi

###############################################################################
# 6. Setup Environment
###############################################################################
echo ""
echo "=========================================="
echo "6. Setting up Environment"
echo "=========================================="

# Add to bashrc if not already present
BASHRC="$HOME/.bashrc"
SOURCE_LINE="source ${CATKIN_WS}/devel/setup.bash"

if ! grep -Fxq "${SOURCE_LINE}" "${BASHRC}"; then
    echo "" >> "${BASHRC}"
    echo "# YOPO with AirSim" >> "${BASHRC}"
    echo "${SOURCE_LINE}" >> "${BASHRC}"
    echo -e "${GREEN}✓ Added workspace to .bashrc${NC}"
else
    echo -e "${YELLOW}Workspace already in .bashrc${NC}"
fi

###############################################################################
# 7. Make Scripts Executable
###############################################################################
echo ""
echo "=========================================="
echo "7. Making Scripts Executable"
echo "=========================================="

chmod +x "${AIRSIM_ROS_DIR}/scripts/"*.py
echo -e "${GREEN}✓ Python scripts are now executable${NC}"

###############################################################################
# Done
###############################################################################
echo ""
echo "=========================================="
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Download Unreal Engine environment (or use existing AirSim environment)"
echo "2. Launch Unreal Engine with AirSim"
echo "3. Source your workspace:"
echo "   source ${CATKIN_WS}/devel/setup.bash"
echo "4. Launch YOPO with AirSim:"
echo "   roslaunch airsim_ros_pkgs airsim_yopo.launch"
echo "5. In another terminal, run YOPO planner:"
echo "   cd ${YOPO_ROOT}/YOPO"
echo "   python3 test_yopo_ros.py --trial=1 --epoch=50"
echo ""
echo "See AIRSIM_MIGRATION_GUIDE.md for detailed instructions."
echo ""
