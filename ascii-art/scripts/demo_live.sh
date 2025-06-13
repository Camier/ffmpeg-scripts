#!/bin/bash
# AsciiSymphony Pro Live Demonstration
# This script demonstrates the live audio capabilities

# Check if AsciiSymphony Pro script exists
if [[ ! -f "./asciisymphony_pro.sh" ]]; then
    echo "Error: asciisymphony_pro.sh not found"
    echo "Make sure you are in the AsciiSymphonyPro directory"
    exit 1
fi

# Make sure the script is executable
chmod +x ./asciisymphony_pro.sh

echo "==============================================="
echo "AsciiSymphony Pro Live Demonstration"
echo "==============================================="
echo ""

# List available audio devices
echo "Listing available audio devices..."
./asciisymphony_pro.sh --list-devices
echo ""

# Ask user to select a device or use default
read -p "Enter device number (or press Enter for default): " device_number

# Ask user to select a visualization mode
echo ""
echo "Available visualization modes:"
echo "1) typography - Text-based visualization"
echo "2) neural - Neural network-inspired visualization"
echo "3) particles - Particle system visualization"
echo "4) fractal - Fractal-inspired visualization"
echo ""
read -p "Select visualization mode (1-4, default: 1): " mode_choice

# Set visualization mode based on user choice
case "$mode_choice" in
    2) mode="neural" ;;
    3) mode="particles" ;;
    4) mode="fractal" ;;
    *) mode="typography" ;;
esac

# Ask user for quality setting
echo ""
echo "Quality settings:"
echo "1) low - For slower systems"
echo "2) balanced - Default setting"
echo "3) high - For better systems"
echo "4) ultra - For powerful systems"
echo ""
read -p "Select quality (1-4, default: 2): " quality_choice

# Set quality based on user choice
case "$quality_choice" in
    1) quality="low" ;;
    3) quality="high" ;;
    4) quality="ultra" ;;
    *) quality="balanced" ;;
esac

# Construct command line
if [[ -z "$device_number" ]]; then
    cmd="./asciisymphony_pro.sh --live --mode=$mode --quality=$quality"
else
    cmd="./asciisymphony_pro.sh --live $device_number --mode=$mode --quality=$quality"
fi

# Add latency setting for responsive visualization
cmd="$cmd --latency=low"

echo ""
echo "Running: $cmd"
echo "Press Ctrl+C to exit"
echo ""

# Execute the command
eval "$cmd"
