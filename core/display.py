#!/usr/bin/env python3
"""
Display management module for controlling monitors.
"""
from typing import Dict, List, Optional
from utils.shell import run_command
from utils.logger import logger
from core.detection import get_displays, find_display_by_keyword

class DisplayManager:
    """
    Manages display settings using xrandr.
    """
    
    def __init__(self):
        """Initialize the display manager."""
        self.refresh()
    
    def refresh(self) -> None:
        """Refresh the display information."""
        self.displays = get_displays()
    
    def get_display(self, name: str) -> Optional[Dict]:
        """
        Get a display by name.
        
        Args:
            name: Display name or keyword
            
        Returns:
            Display dictionary or None if not found
        """
        # First try exact match
        for display in self.displays:
            if display['name'] == name:
                return display
        
        # Then try keyword search
        return find_display_by_keyword(name, self.displays)
    
    def enable_display(self, display_name: str, resolution: Optional[str] = None, 
                      position: str = '--right-of', relative_to: Optional[str] = None) -> bool:
        """
        Enable a display with optional resolution and position.
        
        Args:
            display_name: Name of the display to enable
            resolution: Optional resolution (e.g., '1920x1080')
            position: Position option (--right-of, --left-of, --above, --below, --same-as)
            relative_to: Reference display for position (if None, uses first connected display)
            
        Returns:
            True if successful, False otherwise
        """
        display = self.get_display(display_name)
        if not display:
            logger.error(f"Display {display_name} not found")
            return False
        
        # Build command
        cmd = ['xrandr', '--output', display['name'], '--auto']
        
        # Add resolution if specified
        if resolution:
            cmd.extend(['--mode', resolution])
        
        # Add position if specified and we have more than one display
        if len(self.displays) > 1 and position and position not in ['--same-as']:
            if relative_to:
                ref_display = self.get_display(relative_to)
                if ref_display:
                    cmd.extend([position, ref_display['name']])
            else:
                # Use first connected display other than current one
                for disp in self.displays:
                    if disp['status'] == 'connected' and disp['name'] != display['name']:
                        cmd.extend([position, disp['name']])
                        break
        
        # Execute command
        result = run_command(' '.join(cmd))
        if result.returncode != 0:
            logger.error(f"Failed to enable display: {result.stderr}")
            return False
        
        self.refresh()
        return True
    
    def disable_display(self, display_name: str) -> bool:
        """
        Disable a display.
        
        Args:
            display_name: Name of the display to disable
            
        Returns:
            True if successful, False otherwise
        """
        display = self.get_display(display_name)
        if not display:
            logger.error(f"Display {display_name} not found")
            return False
        
        cmd = f"xrandr --output {display['name']} --off"
        result = run_command(cmd)
        
        if result.returncode != 0:
            logger.error(f"Failed to disable display: {result.stderr}")
            return False
        
        self.refresh()
        return True
    
    def set_primary(self, display_name: str) -> bool:
        """
        Set a display as primary.
        
        Args:
            display_name: Name of the display to set as primary
            
        Returns:
            True if successful, False otherwise
        """
        display = self.get_display(display_name)
        if not display:
            logger.error(f"Display {display_name} not found")
            return False
        
        cmd = f"xrandr --output {display['name']} --primary"
        result = run_command(cmd)
        
        if result.returncode != 0:
            logger.error(f"Failed to set primary display: {result.stderr}")
            return False
        
        self.refresh()
        return True
    
    def configure_displays(self, config: Dict) -> bool:
        """
        Configure displays according to a configuration dict.
        
        Args:
            config: Dictionary with display configurations
            
        Returns:
            True if successful, False otherwise
        """
        success = True
        
        # First disable any displays marked for disabling
        for display_name, settings in config.items():
            if settings.get('enabled') is False:
                if not self.disable_display(display_name):
                    success = False
        
        # Then enable displays
        for display_name, settings in config.items():
            if settings.get('enabled') is True:
                resolution = settings.get('resolution')
                position = settings.get('position', '--right-of')
                relative_to = settings.get('relative_to')
                
                if not self.enable_display(display_name, resolution, position, relative_to):
                    success = False
        
        # Finally set primary
        for display_name, settings in config.items():
            if settings.get('primary') is True:
                if not self.set_primary(display_name):
                    success = False
        
        return success
    
    def get_display_info(self) -> Dict:
        """
        Get information about all displays.
        
        Returns:
            Dictionary with display information
        """
        self.refresh()
        return {"displays": self.displays}
