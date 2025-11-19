#!/bin/bash
###############################################################################
# AirSim Plugin Setup Script for ForestDrone UE 4.27.1 Project
###############################################################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "AirSim Plugin Setup for ForestDrone"
echo -e "==========================================${NC}"

# Get directories
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="${SCRIPT_DIR}"
PLUGINS_DIR="${PROJECT_DIR}/Plugins"
AIRSIM_PLUGIN_DIR="${PLUGINS_DIR}/AirSim"

echo -e "\n${GREEN}Project Directory: ${PROJECT_DIR}${NC}"

# Check if AirSim is already installed
AIRSIM_DIR="${HOME}/AirSim"
if [ ! -d "${AIRSIM_DIR}" ]; then
    echo -e "\n${YELLOW}AirSim not found in ${AIRSIM_DIR}${NC}"
    echo "Please install AirSim first:"
    echo "  cd ~"
    echo "  git clone https://github.com/Microsoft/AirSim.git --branch v1.8.1"
    echo "  cd AirSim"
    echo "  ./setup.sh"
    echo "  ./build.sh"
    exit 1
fi

echo -e "\n${GREEN}✓ AirSim found at ${AIRSIM_DIR}${NC}"

# Create Plugins directory
echo -e "\n${BLUE}Creating Plugins directory...${NC}"
mkdir -p "${PLUGINS_DIR}"

# Copy AirSim plugin
echo -e "\n${BLUE}Copying AirSim plugin...${NC}"
if [ -d "${AIRSIM_PLUGIN_DIR}" ]; then
    echo -e "${YELLOW}Removing existing AirSim plugin...${NC}"
    rm -rf "${AIRSIM_PLUGIN_DIR}"
fi

cp -r "${AIRSIM_DIR}/Unreal/Plugins/AirSim" "${PLUGINS_DIR}/"
echo -e "${GREEN}✓ AirSim plugin copied${NC}"

# Update plugin for UE 4.27
echo -e "\n${BLUE}Updating plugin for UE 4.27.1...${NC}"
PLUGIN_FILE="${AIRSIM_PLUGIN_DIR}/AirSim.uplugin"
if [ -f "${PLUGIN_FILE}" ]; then
    # Backup original
    cp "${PLUGIN_FILE}" "${PLUGIN_FILE}.backup"

    # Update engine version
    sed -i 's/"EngineVersion": ".*"/"EngineVersion": "4.27.0"/g' "${PLUGIN_FILE}"
    echo -e "${GREEN}✓ Plugin updated for UE 4.27.1${NC}"
fi

# Create AirSim settings directory
echo -e "\n${BLUE}Creating AirSim settings...${NC}"
SETTINGS_DIR="${HOME}/Documents/AirSim"
mkdir -p "${SETTINGS_DIR}"

# Copy settings.json if exists
if [ -f "${PROJECT_DIR}/../../../airsim_config/settings.json" ]; then
    cp "${PROJECT_DIR}/../../../airsim_config/settings.json" "${SETTINGS_DIR}/settings.json"
    echo -e "${GREEN}✓ AirSim settings.json copied${NC}"
else
    echo -e "${YELLOW}! Default settings.json not found, will use AirSim defaults${NC}"
fi

# Update project file to enable plugin
echo -e "\n${BLUE}Enabling AirSim plugin in project...${NC}"
PROJECT_FILE="${PROJECT_DIR}/ForestDrone.uproject"

if [ -f "${PROJECT_FILE}" ]; then
    echo -e "${GREEN}✓ Project file found${NC}"
    echo -e "${YELLOW}Note: AirSim plugin is already enabled in ForestDrone.uproject${NC}"
else
    echo -e "${RED}✗ Project file not found!${NC}"
    exit 1
fi

# Create symlink to AirSim for easy access
echo -e "\n${BLUE}Creating symlink to AirSim...${NC}"
ln -sf "${AIRSIM_DIR}" "${PROJECT_DIR}/AirSim_Source"
echo -e "${GREEN}✓ Symlink created: ${PROJECT_DIR}/AirSim_Source -> ${AIRSIM_DIR}${NC}"

# Build project (optional)
echo -e "\n${BLUE}=========================================="
echo "Setup Complete!"
echo -e "==========================================${NC}"

echo -e "\n${GREEN}Next steps:${NC}"
echo "1. Open Unreal Engine 4.27:"
echo -e "   ${YELLOW}cd ~/UnrealEngine${NC}"
echo -e "   ${YELLOW}./Engine/Binaries/Linux/UE4Editor ${PROJECT_DIR}/ForestDrone.uproject${NC}"
echo ""
echo "2. When prompted, allow Unreal to rebuild the AirSim plugin"
echo ""
echo "3. Create your forest environment in the editor"
echo ""
echo "4. Press 'Play' to test with AirSim"
echo ""
echo -e "${BLUE}Useful keyboard shortcuts:${NC}"
echo "  Alt+P : Toggle between editor and game mode"
echo "  F8    : Eject from pawn (free camera)"
echo "  ;     : Toggle AirSim subwindows"
echo ""
echo -e "${GREEN}Documentation:${NC}"
echo "  See FOREST_SCENE_GUIDE.md for scene creation"
echo "  See AIRSIM_MIGRATION_GUIDE.md for ROS integration"
echo ""
