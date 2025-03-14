#!/usr/bin/env python3
"""
General settings for the screen and audio manager.
"""
import os
import json
from typing import Dict, Any, Optional
from utils.logger import logger

# Default configuration paths
CONFIG_DIR = os.path.expanduser("~/.config/screen-audio-manager")
DEFAULT_CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DEVICE_CACHE_FILE = os.path.join(CONFIG_DIR, "devices_cache.json")

# Ensure config directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)

# Default configuration
DEFAULT_CONFIG = {
    "displays": {
        "keywords": {
            "desk": ["DP", "HDMI-0", "primary"],
            "tv": ["HDMI-1", "HDMI-2", "living", "TV"]
        }
    },
    "audio": {
        "keywords": {
            "desk": ["built-in", "headphone", "analog", "desk"],
            "tv": ["hdmi", "digital", "tv", "living"]
        }
    },
    "macros": {
        "tv_mode": {
            "description": "TV mode (disable desk, enable TV)",
            "displays": {
                "desk": {"enabled": False},
                "tv": {"enabled": True, "primary": True}
            },
            "audio": {
                "output": "tv",
                "volume": 70
            }
        },
        "desk_mode": {
            "description": "Desk mode (disable TV, enable desk)",
            "displays": {
                "desk": {"enabled": True, "primary": True},
                "tv": {"enabled": False}
            },
            "audio": {
                "output": "desk",
                "volume": 50
            }
        },
        "dual_mode": {
            "description": "Dual mode (enable both, desk primary)",
            "displays": {
                "desk": {"enabled": True, "primary": True},
                "tv": {"enabled": True, "position": "--right-of", "relative_to": "desk"}
            },
            "audio": {
                "output": "desk",
                "volume": 50
            }
        }
    }
}

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file or create default if it doesn't exist.
    
    Args:
        config_path: Path to config file. If None, uses default path.
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_FILE
    
    # If config file doesn't exist, create it with defaults
    if not os.path.exists(config_path):
        logger.info(f"Creating default configuration at {config_path}")
        save_config(DEFAULT_CONFIG, config_path)
        return DEFAULT_CONFIG
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            logger.debug(f"Loaded configuration from {config_path}")
            return config
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        logger.info("Using default configuration")
        return DEFAULT_CONFIG

def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary to save
        config_path: Path to save to. If None, uses default path.
        
    Returns:
        True if successful, False otherwise
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_FILE
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.debug(f"Saved configuration to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving config to {config_path}: {e}")
        return False

def update_config(updates: Dict[str, Any], config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Update specific parts of the configuration.
    
    Args:
        updates: Dictionary with configuration updates
        config_path: Path to config file. If None, uses default path.
        
    Returns:
        Updated configuration dictionary
    """
    config = load_config(config_path)
    
    def recursive_update(target, source):
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                recursive_update(target[key], value)
            else:
                target[key] = value
    
    recursive_update(config, updates)
    save_config(config, config_path)
    return config

def get_cache_dir() -> str:
    """
    Get the cache directory and ensure it exists.
    
    Returns:
        Path to cache directory
    """
    cache_dir = os.path.join(CONFIG_DIR, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def save_device_cache(devices: Dict[str, Any]) -> bool:
    """
    Save device information to cache.
    
    Args:
        devices: Device information dictionary
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(DEVICE_CACHE_FILE, 'w') as f:
            json.dump(devices, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving device cache: {e}")
        return False

def load_device_cache() -> Optional[Dict[str, Any]]:
    """
    Load device information from cache.
    
    Returns:
        Device information dictionary or None if not found/invalid
    """
    if not os.path.exists(DEVICE_CACHE_FILE):
        return None
    
    try:
        with open(DEVICE_CACHE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading device cache: {e}")
        return None
