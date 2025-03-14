#!/usr/bin/env python3
"""
Main entry point for the screen and audio manager.
Provides command-line interface for applying macros and managing devices.
"""
import os
import sys
import argparse
import json
from typing import Dict, List, Optional, Any

from core.display import DisplayManager
from core.audio import AudioManager
from core.detection import get_device_info, save_detected_devices
from config.devices import DeviceMapper
from config.settings import load_config, save_config, update_config
from utils.logger import logger, set_verbose
from utils.shell import check_dependency

# Import macros
from macros.desk_mode import apply_desk_mode
from macros.tv_mode import apply_tv_mode
from macros.dual_mode import apply_dual_mode

def check_dependencies() -> bool:
    """
    Check if required dependencies are installed.
    
    Returns:
        True if all dependencies are met, False otherwise
    """
    dependencies = [
        ("xrandr", "xorg-xrandr"),
    ]
    
    # At least one of these audio systems must be present
    audio_deps = [
        ("pactl", "pulseaudio-utils"),
        ("wpctl", "wireplumber")
    ]
    
    all_met = True
    
    for cmd, pkg in dependencies:
        if not check_dependency(cmd, pkg):
            all_met = False
    
    # Check if at least one audio system is available
    audio_met = False
    for cmd, pkg in audio_deps:
        if check_dependency(cmd, pkg):
            audio_met = True
            break
    
    if not audio_met:
        logger.error("No supported audio system found.")
        logger.error("Please install either pulseaudio-utils or wireplumber.")
        all_met = False
    
    return all_met

def detect_command(args) -> None:
    """Handle the 'detect' command."""
    if args.save:
        save_detected_devices(args.save)
    else:
        devices = get_device_info()
        print(json.dumps(devices, indent=2))

def apply_command(args) -> None:
    """Handle the 'apply' command."""
    if args.macro == "desk":
        result = apply_desk_mode()
    elif args.macro == "tv":
        result = apply_tv_mode()
    elif args.macro == "dual":
        result = apply_dual_mode()
    else:
        logger.error(f"Unknown macro: {args.macro}")
        sys.exit(1)
    
    if not result:
        sys.exit(1)

def display_command(args) -> None:
    """Handle the 'display' command."""
    display_mgr = DisplayManager()
    
    if args.list:
        displays = display_mgr.get_display_info()
        print(json.dumps(displays, indent=2))
    elif args.enable:
        result = display_mgr.enable_display(args.enable)
        if not result:
            sys.exit(1)
    elif args.disable:
        result = display_mgr.disable_display(args.disable)
        if not result:
            sys.exit(1)
    elif args.primary:
        result = display_mgr.set_primary(args.primary)
        if not result:
            sys.exit(1)

def audio_command(args) -> None:
    """Handle the 'audio' command."""
    audio_mgr = AudioManager()
    
    if args.list:
        audio = audio_mgr.get_audio_info()
        print(json.dumps(audio, indent=2))
    elif args.output:
        result = audio_mgr.set_default_sink(args.output)
        if not result:
            sys.exit(1)
    elif args.input:
        result = audio_mgr.set_default_source(args.input)
        if not result:
            sys.exit(1)
    elif args.volume is not None:
        device = args.device or "default"
        result = audio_mgr.set_volume(device, args.volume)
        if not result:
            sys.exit(1)
    elif args.mute:
        device = args.device or "default"
        result = audio_mgr.mute(device, True)
        if not result:
            sys.exit(1)
    elif args.unmute:
        device = args.device or "default"
        result = audio_mgr.mute(device, False)
        if not result:
            sys.exit(1)

def config_command(args) -> None:
    """Handle the 'config' command."""
    if args.show:
        config = load_config()
        print(json.dumps(config, indent=2))
    elif args.update:
        try:
            with open(args.update, 'r') as f:
                updates = json.load(f)
            update_config(updates)
            logger.info("Configuration updated successfully")
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            sys.exit(1)
    elif args.reset:
        from config.settings import DEFAULT_CONFIG, DEFAULT_CONFIG_FILE
        save_config(DEFAULT_CONFIG, DEFAULT_CONFIG_FILE)
        logger.info("Configuration reset to defaults")

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Screen and Audio Manager")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose logging")
    
    subparsers = parser.add_subparsers(dest='command', help="Command to execute")
    
    # Detect command
    detect_parser = subparsers.add_parser('detect', help="Detect devices")
    detect_parser.add_argument('-s', '--save', help="Save detection results to file")
    
    # Apply command
    apply_parser = subparsers.add_parser('apply', help="Apply a macro")
    apply_parser.add_argument('macro', choices=['desk', 'tv', 'dual'], 
                             help="Macro to apply")
    
    # Display command
    display_parser = subparsers.add_parser('display', help="Manage displays")
    display_group = display_parser.add_mutually_exclusive_group(required=True)
    display_group.add_argument('-l', '--list', action='store_true', help="List displays")
    display_group.add_argument('-e', '--enable', help="Enable display")
    display_group.add_argument('-d', '--disable', help="Disable display")
    display_group.add_argument('-p', '--primary', help="Set primary display")
    
    # Audio command
    audio_parser = subparsers.add_parser('audio', help="Manage audio devices")
    audio_group = audio_parser.add_mutually_exclusive_group(required=True)
    audio_group.add_argument('-l', '--list', action='store_true', help="List audio devices")
    audio_group.add_argument('-o', '--output', help="Set default output device")
    audio_group.add_argument('-i', '--input', help="Set default input device")
    audio_group.add_argument('--volume', type=int, help="Set volume (0-100)")
    audio_group.add_argument('--mute', action='store_true', help="Mute device")
    audio_group.add_argument('--unmute', action='store_true', help="Unmute device")
    audio_parser.add_argument('--device', help="Device to apply volume/mute to")
    
    # Config command
    config_parser = subparsers.add_parser('config', help="Manage configuration")
    config_group = config_parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument('-s', '--show', action='store_true', help="Show current config")
    config_group.add_argument('-u', '--update', help="Update config from JSON file")
    config_group.add_argument('-r', '--reset', action='store_true', help="Reset to default config")
    
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        set_verbose(True)
    
    # Check if no command was provided
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Missing required dependencies")
        sys.exit(1)
    
    # Handle commands
    try:
        if args.command == 'detect':
            detect_command(args)
        elif args.command == 'apply':
            apply_command(args)
        elif args.command == 'display':
            display_command(args)
        elif args.command == 'audio':
            audio_command(args)
        elif args.command == 'config':
            config_command(args)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
