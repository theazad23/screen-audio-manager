#!/usr/bin/env python3
"""
Device configuration and mapping module.
"""
from typing import Dict, List, Optional, Any
from core.detection import get_displays, get_audio_devices, find_display_by_keyword, find_audio_by_keyword
from utils.logger import logger
from config.settings import load_config

class DeviceMapper:
    """
    Maps logical device names (like 'desk' or 'tv') to actual devices 
    found on the system using keywords and auto-detection.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize with configuration.
        
        Args:
            config: Optional configuration dictionary. If None, loads from default location.
        """
        self.config = config or load_config()
        self.displays = get_displays()
        self.audio_devices = get_audio_devices()
        self.mappings = self._create_mappings()
    
    def refresh(self) -> None:
        """Refresh device information and mappings."""
        self.displays = get_displays()
        self.audio_devices = get_audio_devices()
        self.mappings = self._create_mappings()
    
    def _create_mappings(self) -> Dict[str, Dict[str, str]]:
        """
        Create mappings from logical names to actual device names.
        
        Returns:
            Dictionary with mappings for displays and audio devices
        """
        mappings = {
            "displays": {},
            "audio": {
                "outputs": {},
                "inputs": {}
            }
        }
        
        # Map displays
        display_keywords = self.config.get("displays", {}).get("keywords", {})
        for logical_name, keywords in display_keywords.items():
            for keyword in keywords:
                display = find_display_by_keyword(keyword, self.displays)
                if display:
                    mappings["displays"][logical_name] = display["name"]
                    break
        
        # Map audio devices
        audio_keywords = self.config.get("audio", {}).get("keywords", {})
        for logical_name, keywords in audio_keywords.items():
            # Try to find output devices first
            for keyword in keywords:
                device = find_audio_by_keyword(keyword, "outputs", self.audio_devices)
                if device:
                    mappings["audio"]["outputs"][logical_name] = device["name"]
                    break
            
            # Then try input devices
            for keyword in keywords:
                device = find_audio_by_keyword(keyword, "inputs", self.audio_devices)
                if device:
                    mappings["audio"]["inputs"][logical_name] = device["name"]
                    break
        
        return mappings
    
    def get_display(self, logical_name: str) -> Optional[str]:
        """
        Get actual display name from logical name.
        
        Args:
            logical_name: Logical name (e.g., 'desk', 'tv')
            
        Returns:
            Actual display name or None if not found
        """
        return self.mappings["displays"].get(logical_name)
    
    def get_audio_output(self, logical_name: str) -> Optional[str]:
        """
        Get actual audio output device name from logical name.
        
        Args:
            logical_name: Logical name (e.g., 'desk', 'tv')
            
        Returns:
            Actual audio output device name or None if not found
        """
        return self.mappings["audio"]["outputs"].get(logical_name)
    
    def get_audio_input(self, logical_name: str) -> Optional[str]:
        """
        Get actual audio input device name from logical name.
        
        Args:
            logical_name: Logical name (e.g., 'desk', 'tv')
            
        Returns:
            Actual audio input device name or None if not found
        """
        return self.mappings["audio"]["inputs"].get(logical_name)
    
    def update_mappings(self, mappings: Dict[str, Any]) -> None:
        """
        Update device mappings manually.
        
        Args:
            mappings: New mappings to set
        """
        if "displays" in mappings:
            self.mappings["displays"].update(mappings["displays"])
        
        if "audio" in mappings:
            if "outputs" in mappings["audio"]:
                self.mappings["audio"]["outputs"].update(mappings["audio"]["outputs"])
            if "inputs" in mappings["audio"]:
                self.mappings["audio"]["inputs"].update(mappings["audio"]["inputs"])
    
    def get_mappings(self) -> Dict[str, Any]:
        """
        Get all current device mappings.
        
        Returns:
            Dictionary with all mappings
        """
        return self.mappings
    
    def get_all_devices(self) -> Dict[str, Any]:
        """
        Get information about all detected devices.
        
        Returns:
            Dictionary with all device information
        """
        return {
            "displays": self.displays,
            "audio": self.audio_devices,
            "mappings": self.mappings
        }
