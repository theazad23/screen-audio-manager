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
from config.profiles import list_profiles, create_profile, get_profile, delete_profile, apply_profile, build_profile_from_detected_devices
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
    if args.profile:
        # Apply a saved profile
        result = apply_profile(args.profile)
        if not result:
            logger.error(f"Failed to apply profile: {args.profile}")
            sys.exit(1)
    elif args.macro == "desk":
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

def profile_command(args) -> None:
    """Handle the 'profile' command."""
    if args.list:
        # List available profiles
        profiles = list_profiles()
        if not profiles:
            print("No profiles found.")
            return
        
        print("Available profiles:")
        for profile in profiles:
            print(f"  {profile['display_name']}: {profile['description']}")
    
    elif args.create:
        # Create a profile based on current device state
        description = args.description or f"Profile created on {os.popen('date').read().strip()}"
        profile_config = build_profile_from_detected_devices(args.create, description)
        
        # Allow the user to specify primary display
        if args.primary_display:
            for display_name, display in profile_config["displays"].items():
                display["primary"] = display_name == args.primary_display
                if display_name == args.primary_display:
                    display["enabled"] = True
        
        # Allow the user to specify additional displays to enable
        if args.enable_displays:
            for display_name in args.enable_displays.split(','):
                display_name = display_name.strip()
                if display_name in profile_config["displays"]:
                    profile_config["displays"][display_name]["enabled"] = True
        
        # Allow the user to specify audio output
        if args.audio_output:
            profile_config["audio"]["output"] = args.audio_output
        
        # Allow the user to specify audio input
        if args.audio_input:
            profile_config["audio"]["input"] = args.audio_input
        
        # Allow the user to specify volume
        if args.volume is not None:
            profile_config["audio"]["volume"] = args.volume
        
        result = create_profile(args.create, profile_config)
        if not result:
            logger.error(f"Failed to create profile: {args.create}")
            sys.exit(1)
        
        logger.info(f"Profile '{args.create}' created successfully")
    
    elif args.delete:
        # Delete a profile
        result = delete_profile(args.delete)
        if not result:
            logger.error(f"Failed to delete profile: {args.delete}")
            sys.exit(1)
        
        logger.info(f"Profile '{args.delete}' deleted successfully")
    
    elif args.show:
        # Show profile configuration
        profile = get_profile(args.show)
        if not profile:
            logger.error(f"Profile not found: {args.show}")
            sys.exit(1)
        
        print(json.dumps(profile, indent=2))

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Screen and Audio Manager")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose logging")
    
    subparsers = parser.add_subparsers(dest='command', help="Command to execute")
    
    # Detect command
    detect_parser = subparsers.add_parser('detect', help="Detect devices")
    detect_parser.add_argument('-s', '--save', help="Save detection results to file")
    
    # Apply command
    apply_parser = subparsers.add_parser('apply', help="Apply a macro or profile")
    apply_group = apply_parser.add_mutually_exclusive_group(required=True)
    apply_group.add_argument('macro', nargs='?', choices=['desk', 'tv', 'dual'], 
                             help="Macro to apply")
    apply_group.add_argument('-p', '--profile', help="Profile to apply")
    
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
    
    # Profile command
    profile_parser = subparsers.add_parser('profile', help="Manage profiles")
    profile_group = profile_parser.add_mutually_exclusive_group(required=True)
    profile_group.add_argument('-l', '--list', action='store_true', help="List available profiles")
    profile_group.add_argument('-c', '--create', help="Create a new profile with the given name")
    profile_group.add_argument('-d', '--delete', help="Delete a profile")
    profile_group.add_argument('-s', '--show', help="Show profile configuration")
    
    # Profile creation options
    profile_parser.add_argument('--description', help="Description for the new profile")
    profile_parser.add_argument('--primary-display', help="Set primary display for the profile")
    profile_parser.add_argument('--enable-displays', help="Comma-separated list of displays to enable")
    profile_parser.add_argument('--audio-output', help="Set default audio output for the profile")
    profile_parser.add_argument('--audio-input', help="Set default audio input for the profile")
    profile_parser.add_argument('--volume', type=int, help="Set volume level for the profile (0-100)")
    
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
        elif args.command == 'profile':
            profile_command(args)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
