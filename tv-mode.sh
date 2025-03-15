#!/bin/bash

# Script to apply TV mode settings directly

echo "Setting up TV Mode..."

# Completely reconfigure displays
echo "1. Disabling all displays"
xrandr --output DP-1 --off
xrandr --output HDMI-A-1 --off

echo "2. Enabling HDMI as primary"
xrandr --output HDMI-A-1 --auto --primary

echo "3. Enabling DP-1 as secondary"
xrandr --output DP-1 --auto --right-of HDMI-A-1

# Set audio device and volume
echo "4. Setting HDMI audio"
pactl set-default-sink alsa_output.pci-0000_08_00.1.hdmi-stereo-extra1
pactl set-sink-volume alsa_output.pci-0000_08_00.1.hdmi-stereo-extra1 100%

echo "TV Mode applied."
echo "Primary display should now be HDMI-A-1."
echo "Audio output should now be HDMI audio at 100% volume."

# Check the result
echo "Display status:"
xrandr | grep " connected"
