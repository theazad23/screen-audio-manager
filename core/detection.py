#!/usr/bin/env python3
"""
Device detection module for automatically finding displays and audio devices.
"""
import re
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from utils.shell import run_command
from utils.logger import logger
from config.settings import CONFIG_DIR, save_device_cache

def get_displays() -> List[Dict]:
    """
    Detect connected displays using xrandr.
    
    Returns:
        List of dictionaries with display information.
    """
    displays = []
    
    # Get output from xrandr
    result = run_command("xrandr --query")
    if result.returncode != 0:
        logger.error(f"Failed to get display info: {result.stderr}")
        return displays
    
    # Parse displays
    current_display = None
    for line in result.stdout.split('\n'):
        # Match display names like "HDMI-1 connected" or "DP-1 disconnected"
        display_match = re.match(r'^([a-zA-Z0-9-]+) (connected|disconnected)', line)
        if display_match:
            name = display_match.group(1)
            status = display_match.group(2)
            
            if status == 'connected':
                current_display = {
                    'name': name,
                    'status': status,
                    'resolutions': [],
                    'current_resolution': None,
                    'primary': '+primary' in line
                }
                displays.append(current_display)
        
        # Parse resolution info
        elif current_display and '*' in line:
            res_match = re.search(r'(\d+x\d+).*\*', line)
            if res_match:
                current_display['current_resolution'] = res_match.group(1)
    
    return displays

def get_audio_devices() -> Dict[str, List[Dict]]:
    """
    Detect audio devices using PulseAudio or Pipewire.
    
    Returns:
        Dictionary with 'inputs' and 'outputs' lists.
    """
    devices = {
        'inputs': [],
        'outputs': []
    }
    
    # Try PulseAudio first
    result = run_command("pactl list short sinks")
    
    if result.returncode != 0:
        # Fall back to pipewire
        result = run_command("wpctl status")
        if result.returncode != 0:
            logger.error("Failed to detect audio devices")
            return devices
        
        # Parse Pipewire output
        return _parse_pipewire_devices(result.stdout)
    
    # Parse PulseAudio output
    return _parse_pulse_devices()

def _parse_pulse_devices() -> Dict[str, List[Dict]]:
    """Parse PulseAudio devices."""
    devices = {
        'inputs': [],
        'outputs': []
    }
    
    # Get sinks (outputs)
    sinks_result = run_command("pactl list sinks")
    if sinks_result.returncode == 0:
        current_device = None
        for line in sinks_result.stdout.split('\n'):
            if line.startswith('Sink #'):
                if current_device:
                    devices['outputs'].append(current_device)
                sink_id = line.split('#')[1].strip()
                current_device = {'id': sink_id, 'name': '', 'description': '', 'default': False}
            elif 'Name:' in line and current_device:
                current_device['name'] = line.split('Name:')[1].strip()
            elif 'Description:' in line and current_device:
                current_device['description'] = line.split('Description:')[1].strip()
        
        if current_device:
            devices['outputs'].append(current_device)
    
    # Get default sink
    default_result = run_command("pactl info | grep 'Default Sink'")
    if default_result.returncode == 0 and default_result.stdout:
        default_sink = default_result.stdout.split(':')[1].strip()
        for device in devices['outputs']:
            if device['name'] == default_sink:
                device['default'] = True
    
    # Similar for sources (inputs)
    sources_result = run_command("pactl list sources")
    if sources_result.returncode == 0:
        current_device = None
        for line in sources_result.stdout.split('\n'):
            if line.startswith('Source #'):
                if current_device:
                    devices['inputs'].append(current_device)
                source_id = line.split('#')[1].strip()
                current_device = {'id': source_id, 'name': '', 'description': '', 'default': False}
            elif 'Name:' in line and current_device:
                current_device['name'] = line.split('Name:')[1].strip()
            elif 'Description:' in line and current_device:
                current_device['description'] = line.split('Description:')[1].strip()
        
        if current_device:
            devices['inputs'].append(current_device)
    
    return devices

def _parse_pipewire_devices(stdout: str) -> Dict[str, List[Dict]]:
    """Parse Pipewire devices from wpctl output."""
    devices = {
        'inputs': [],
        'outputs': []
    }
    
    current_section = None
    current_id = None
    
    for line in stdout.split('\n'):
        if "Sinks:" in line:
            current_section = 'outputs'
        elif "Sources:" in line:
            current_section = 'inputs'
        elif current_section and line.strip() and '│' in line:
            parts = line.split('│')
            if len(parts) >= 2:
                id_part = parts[0].strip()
                name_part = parts[1].strip()
                
                if id_part and name_part:
                    is_default = '*' in id_part
                    id_clean = re.sub(r'[\s*]', '', id_part)
                    
                    device = {
                        'id': id_clean,
                        'name': name_part,
                        'description': name_part,
                        'default': is_default
                    }
                    
                    devices[current_section].append(device)
    
    return devices

def get_device_info() -> Dict[str, Any]:
    """
    Get comprehensive information about all detected devices.
    
    Returns:
        Dictionary with display and audio device information.
    """
    return {
        'displays': get_displays(),
        'audio': get_audio_devices()
    }

def find_display_by_keyword(keyword: str, displays: Optional[List[Dict]] = None) -> Optional[Dict]:
    """
    Find a display that matches the given keyword in its name or description.
    
    Args:
        keyword: String to search for in display names.
        displays: Optional list of displays to search in. If None, will detect displays.
        
    Returns:
        Matching display dict or None if not found.
    """
    if displays is None:
        displays = get_displays()
    
    keyword = keyword.lower()
    for display in displays:
        if keyword in display['name'].lower():
            return display
    
    return None

def find_audio_by_keyword(keyword: str, device_type: str = 'outputs', 
                          devices: Optional[Dict] = None) -> Optional[Dict]:
    """
    Find an audio device that matches the given keyword.
    
    Args:
        keyword: String to search for in device names/descriptions.
        device_type: 'outputs' or 'inputs'
        devices: Optional dict of devices to search in. If None, will detect devices.
        
    Returns:
        Matching device dict or None if not found.
    """
    if devices is None:
        devices = get_audio_devices()
    
    if device_type not in devices:
        return None
    
    keyword = keyword.lower()
    for device in devices[device_type]:
        if (keyword in device['name'].lower() or 
            (device.get('description') and keyword in device['description'].lower())):
            return device
    
    return None

def save_detected_devices(filename: str = 'detected_devices.json') -> bool:
    """
    Detect all devices and save to a JSON file.
    
    Args:
        filename: Path to save the JSON data.
        
    Returns:
        True if successful, False otherwise
    """
    devices = get_device_info()
    
    # If not an absolute path, save to config directory
    if not os.path.isabs(filename):
        filename = os.path.join(CONFIG_DIR, filename)
    
    try:
        with open(filename, 'w') as f:
            json.dump(devices, f, indent=2)
        logger.info(f"Device information saved to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving device information: {e}")
        return False

def get_available_displays() -> List[Dict[str, str]]:
    """
    Get a simplified list of available displays.
    
    Returns:
        List of dictionaries with display information in a simple format.
    """
    displays = get_displays()
    return [{"name": d["name"], "description": f"{d['name']} - {'Primary' if d.get('primary') else 'Secondary'}"} 
            for d in displays if d["status"] == "connected"]

def get_available_audio_devices() -> Dict[str, List[Dict[str, str]]]:
    """
    Get a simplified list of available audio devices.
    
    Returns:
        Dictionary with 'inputs' and 'outputs' lists in a simple format.
    """
    audio_devices = get_audio_devices()
    
    simplified = {
        "outputs": [],
        "inputs": []
    }
    
    for device_type in ["outputs", "inputs"]:
        for device in audio_devices.get(device_type, []):
            simplified[device_type].append({
                "name": device["name"],
                "description": device.get("description", device["name"]),
                "default": device.get("default", False)
            })
    
    return simplified

if __name__ == "__main__":
    # When run directly, print detected devices
    devices = get_device_info()
    print(json.dumps(devices, indent=2))

    # Also print a formatted version for easier reading
    print("\nDisplays:")
    for display in get_available_displays():
        print(f"  {display['name']}: {display['description']}")
    
    print("\nAudio outputs:")
    for device in get_available_audio_devices()["outputs"]:
        print(f"  {device['name']}: {device['description']} {'(default)' if device['default'] else ''}")
    
    print("\nAudio inputs:")
    for device in get_available_audio_devices()["inputs"]:
        print(f"  {device['name']}: {device['description']} {'(default)' if device['default'] else ''}")
