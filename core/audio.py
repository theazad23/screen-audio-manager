#!/usr/bin/env python3
"""
Audio device management module using PulseAudio or Pipewire.
"""
import re
import json
from typing import Dict, List, Optional
from utils.shell import run_command
from utils.logger import logger
from core.detection import get_audio_devices, find_audio_by_keyword

class AudioManager:
    """
    Manages audio devices using PulseAudio or Pipewire.
    """
    
    def __init__(self):
        """Initialize the audio manager and detect the audio subsystem."""
        self.system = self._detect_audio_system()
        self.refresh()
    
    def refresh(self) -> None:
        """Refresh audio device information."""
        self.devices = get_audio_devices()
    
    def _detect_audio_system(self) -> str:
        """
        Detect whether the system is using PulseAudio or Pipewire.
        
        Returns:
            'pulse' or 'pipewire'
        """
        # Check for PulseAudio
        result = run_command("pactl info")
        if result.returncode == 0 and "PulseAudio" in result.stdout:
            return 'pulse'
        
        # Check for Pipewire
        result = run_command("wpctl status")
        if result.returncode == 0:
            return 'pipewire'
        
        # Default to PulseAudio as fallback
        logger.warning("Could not determine audio system, defaulting to PulseAudio")
        return 'pulse'
    
    def get_device(self, keyword: str, device_type: str = 'outputs') -> Optional[Dict]:
        """
        Get an audio device by keyword.
        
        Args:
            keyword: Keyword to search for in device names/descriptions
            device_type: 'outputs' or 'inputs'
            
        Returns:
            Device dictionary or None if not found
        """
        return find_audio_by_keyword(keyword, device_type, self.devices)
    
    def set_default_sink(self, sink_name: str) -> bool:
        """
        Set the default audio output device.
        
        Args:
            sink_name: Name or keyword for the sink
            
        Returns:
            True if successful, False otherwise
        """
        sink = self.get_device(sink_name, 'outputs')
        if not sink:
            logger.error(f"Audio output device '{sink_name}' not found")
            return False
        
        if self.system == 'pulse':
            cmd = f"pactl set-default-sink {sink['name']}"
        else:  # pipewire
            cmd = f"wpctl set-default {sink['id']}"
        
        result = run_command(cmd)
        if result.returncode != 0:
            logger.error(f"Failed to set default sink: {result.stderr}")
            return False
        
        # Move all streams to the new sink (PulseAudio only)
        if self.system == 'pulse':
            # Get all input streams (playback streams)
            inputs_result = run_command("pactl list short sink-inputs")
            if inputs_result.returncode == 0:
                for line in inputs_result.stdout.splitlines():
                    if line.strip():
                        input_id = line.split()[0]
                        move_cmd = f"pactl move-sink-input {input_id} {sink['name']}"
                        run_command(move_cmd)
        
        self.refresh()
        return True
    
    def set_default_source(self, source_name: str) -> bool:
        """
        Set the default audio input device.
        
        Args:
            source_name: Name or keyword for the source
            
        Returns:
            True if successful, False otherwise
        """
        source = self.get_device(source_name, 'inputs')
        if not source:
            logger.error(f"Audio input device '{source_name}' not found")
            return False
        
        if self.system == 'pulse':
            cmd = f"pactl set-default-source {source['name']}"
        else:  # pipewire
            cmd = f"wpctl set-default {source['id']}"
        
        result = run_command(cmd)
        if result.returncode != 0:
            logger.error(f"Failed to set default source: {result.stderr}")
            return False
        
        self.refresh()
        return True
    
    def set_volume(self, device_name: str, volume: int, device_type: str = 'outputs') -> bool:
        """
        Set the volume for a device.
        
        Args:
            device_name: Name or keyword for the device
            volume: Volume level (0-100)
            device_type: 'outputs' or 'inputs'
            
        Returns:
            True if successful, False otherwise
        """
        device = self.get_device(device_name, device_type)
        if not device:
            logger.error(f"Audio device '{device_name}' not found")
            return False
        
        # Ensure volume is within range
        volume = max(0, min(100, volume))
        
        if self.system == 'pulse':
            cmd = f"pactl set-{'sink' if device_type == 'outputs' else 'source'}-volume {device['name']} {volume}%"
        else:  # pipewire
            # Convert to 0-1.5 range for wpctl
            wpctl_vol = volume / 100 * 1.5
            cmd = f"wpctl set-volume {device['id']} {wpctl_vol:.2f}"
        
        result = run_command(cmd)
        if result.returncode != 0:
            logger.error(f"Failed to set volume: {result.stderr}")
            return False
        
        return True
    
    def mute(self, device_name: str, mute: bool = True, device_type: str = 'outputs') -> bool:
        """
        Mute or unmute a device.
        
        Args:
            device_name: Name or keyword for the device
            mute: True to mute, False to unmute
            device_type: 'outputs' or 'inputs'
            
        Returns:
            True if successful, False otherwise
        """
        device = self.get_device(device_name, device_type)
        if not device:
            logger.error(f"Audio device '{device_name}' not found")
            return False
        
        if self.system == 'pulse':
            cmd = f"pactl set-{'sink' if device_type == 'outputs' else 'source'}-mute {device['name']} {1 if mute else 0}"
        else:  # pipewire
            cmd = f"wpctl set-mute {device['id']} {1 if mute else 0}"
        
        result = run_command(cmd)
        if result.returncode != 0:
            logger.error(f"Failed to {'mute' if mute else 'unmute'}: {result.stderr}")
            return False
        
        return True
    
    def get_audio_info(self) -> Dict:
        """
        Get information about all audio devices.
        
        Returns:
            Dictionary with audio device information
        """
        self.refresh()
        return {"audio": self.devices, "system": self.system}
