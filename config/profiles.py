#!/usr/bin/env python3
"""
Profile management for screen and audio configurations.
"""
import os
import json
from typing import Dict, List, Optional, Any
from utils.logger import logger
from config.settings import CONFIG_DIR, load_config, save_config, update_config

# Profiles directory
PROFILES_DIR = os.path.join(CONFIG_DIR, "profiles")
os.makedirs(PROFILES_DIR, exist_ok=True)

def get_profile_path(profile_name: str) -> str:
    """
    Get the file path for a profile.
    
    Args:
        profile_name: Name of the profile
        
    Returns:
        Path to the profile file
    """
    return os.path.join(PROFILES_DIR, f"{profile_name.lower().replace(' ', '_')}.json")

def list_profiles() -> List[Dict[str, Any]]:
    """
    List all available profiles.
    
    Returns:
        List of profile info dictionaries with name and description
    """
    profiles = []
    
    if not os.path.exists(PROFILES_DIR):
        return profiles
    
    for filename in os.listdir(PROFILES_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(PROFILES_DIR, filename)
            try:
                with open(file_path, 'r') as f:
                    profile_data = json.load(f)
                    
                profile_name = filename.replace(".json", "").replace("_", " ")
                profile_info = {
                    "name": profile_name,
                    "display_name": profile_data.get("name", profile_name),
                    "description": profile_data.get("description", ""),
                    "path": file_path
                }
                profiles.append(profile_info)
            except Exception as e:
                logger.error(f"Error reading profile {filename}: {e}")
    
    return profiles

def get_profile(profile_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a profile by name.
    
    Args:
        profile_name: Name of the profile
        
    Returns:
        Profile data dictionary or None if not found
    """
    profile_path = get_profile_path(profile_name)
    
    if not os.path.exists(profile_path):
        logger.error(f"Profile {profile_name} not found")
        return None
    
    try:
        with open(profile_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading profile {profile_name}: {e}")
        return None

def create_profile(profile_name: str, config: Dict[str, Any]) -> bool:
    """
    Create a new profile or update an existing one.
    
    Args:
        profile_name: Name for the profile
        config: Configuration dictionary with display and audio settings
        
    Returns:
        True if successful, False otherwise
    """
    profile_path = get_profile_path(profile_name)
    
    # Include the original name in the profile data
    profile_data = config.copy()
    profile_data["name"] = profile_name
    
    try:
        with open(profile_path, 'w') as f:
            json.dump(profile_data, f, indent=2)
        logger.info(f"Profile {profile_name} saved to {profile_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving profile {profile_name}: {e}")
        return False

def delete_profile(profile_name: str) -> bool:
    """
    Delete a profile.
    
    Args:
        profile_name: Name of the profile to delete
        
    Returns:
        True if successful, False otherwise
    """
    profile_path = get_profile_path(profile_name)
    
    if not os.path.exists(profile_path):
        logger.error(f"Profile {profile_name} not found")
        return False
    
    try:
        os.remove(profile_path)
        logger.info(f"Profile {profile_name} deleted")
        return True
    except Exception as e:
        logger.error(f"Error deleting profile {profile_name}: {e}")
        return False

def build_profile_from_detected_devices(profile_name: str, description: str = "") -> Dict[str, Any]:
    """
    Build a profile configuration from currently detected devices.
    
    Args:
        profile_name: Name for the profile
        description: Optional description for the profile
        
    Returns:
        Profile configuration dictionary
    """
    from core.detection import get_device_info
    
    devices = get_device_info()
    
    # Build a basic profile structure
    profile = {
        "name": profile_name,
        "description": description,
        "displays": {},
        "audio": {
            "output": None,
            "input": None,
            "volume": 50  # Default volume level
        }
    }
    
    # Find default/primary display
    primary_display = None
    for display in devices.get("displays", []):
        if display.get("primary", False):
            primary_display = display
            break
    
    # If no primary, use first available
    if not primary_display and devices.get("displays"):
        primary_display = devices.get("displays")[0]
    
    # Add primary display configuration
    if primary_display:
        profile["displays"]["primary"] = {
            "name": primary_display["name"],
            "enabled": True,
            "primary": True
        }
    
    # Add other displays
    for display in devices.get("displays", []):
        if display != primary_display:
            profile["displays"][display["name"]] = {
                "name": display["name"],
                "enabled": False  # Default to disabled for non-primary displays
            }
    
    # Find default audio output
    for output in devices.get("audio", {}).get("outputs", []):
        if output.get("default", False):
            profile["audio"]["output"] = output["name"]
            break
    
    # Find default audio input
    for input_device in devices.get("audio", {}).get("inputs", []):
        if input_device.get("default", False):
            profile["audio"]["input"] = input_device["name"]
            break
    
    return profile

def apply_profile(profile_name: str) -> bool:
    """
    Apply a profile configuration.
    
    Args:
        profile_name: Name of the profile to apply
        
    Returns:
        True if successful, False otherwise
    """
    profile = get_profile(profile_name)
    if not profile:
        return False
    
    from core.display import DisplayManager
    from core.audio import AudioManager
    
    # Configure displays
    display_mgr = DisplayManager()
    if "displays" in profile:
        # Create a copy of the display configuration, replacing any logical names with actual display names
        display_config = {}
        
        # Process each display in the profile
        for key, settings in profile["displays"].items():
            if "name" in settings:
                # Use the actual display name from the settings
                display_config[settings["name"]] = settings.copy()
            else:
                # Use the key as the display name (for backward compatibility)
                display_config[key] = settings.copy()
                
        # Apply the display configuration
        result = display_mgr.configure_displays(display_config)
        if not result:
            logger.error("Failed to configure displays")
            return False
    
    # Configure audio
    audio_mgr = AudioManager()
    if "audio" in profile:
        # Set default output if specified
        if profile["audio"].get("output"):
            if not audio_mgr.set_default_sink(profile["audio"]["output"]):
                logger.error(f"Failed to set default audio output to {profile['audio']['output']}")
                return False
        
        # Set default input if specified
        if profile["audio"].get("input"):
            if not audio_mgr.set_default_source(profile["audio"]["input"]):
                logger.error(f"Failed to set default audio input to {profile['audio']['input']}")
                return False
        
        # Set volume if specified
        if "volume" in profile["audio"] and profile["audio"].get("output"):
            audio_mgr.set_volume(profile["audio"]["output"], profile["audio"]["volume"])
    
    logger.info(f"Profile {profile_name} applied successfully")
    return True
