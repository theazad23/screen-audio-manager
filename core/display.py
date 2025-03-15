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
        
        # Make sure we run the primary command on an enabled display
        cmd = f"xrandr --output {display['name']} --primary"
        logger.debug(f"Executing primary display command: {cmd}")
        result = run_command(cmd)
        
        if result.returncode != 0:
            logger.error(f"Failed to set primary display: {result.stderr}")
            return False
        
        logger.debug(f"Set {display_name} as primary display successfully")
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
        
        logger.debug(f"Configuring displays with config: {config}")
        
        # Find which display should be primary and get a list of all enabled displays
        primary_display = None
        enabled_displays = []
        disabled_displays = []
        
        for display_name, settings in config.items():
            if settings.get('enabled') is True:
                enabled_displays.append(display_name)
                if settings.get('primary') is True:
                    primary_display = display_name
            else:
                disabled_displays.append(display_name)
        
        # First turn off all displays
        logger.debug("Disabling all displays first to reset configuration")
        self.refresh() # Make sure we have the latest display info
        for display in self.displays:
            display_name = display['name']
            logger.debug(f"Disabling display: {display_name}")
            self.disable_display(display_name)
        
        # Then enable the primary display first (if set)
        if primary_display:
            display_settings = config[primary_display]
            logger.debug(f"Enabling primary display first: {primary_display}")
            
            resolution = display_settings.get('resolution')
            
            # For primary, don't set position relative to anything since it's first
            cmd = f"xrandr --output {display_settings['name']} --auto --primary"
            if resolution:
                cmd += f" --mode {resolution}"
                
            logger.debug(f"Executing primary display command: {cmd}")
            result = run_command(cmd)
            
            if result.returncode != 0:
                logger.error(f"Failed to enable primary display: {result.stderr}")
                success = False
            else:
                logger.debug(f"Successfully enabled primary display: {primary_display}")
                # Remove primary from the list of displays to enable
                enabled_displays.remove(primary_display)
        
        # Then enable other displays relative to the primary or the first one enabled
        reference_display = primary_display if primary_display else None
        
        for display_name in enabled_displays:
            if not reference_display:
                reference_display = display_name
                
            settings = config[display_name]
            logger.debug(f"Enabling secondary display: {display_name}")
            
            resolution = settings.get('resolution')
            position = settings.get('position', '--right-of')
            relative_to = settings.get('relative_to', reference_display)
            
            # Enable this display
            if not self.enable_display(display_name, resolution, position, relative_to):
                success = False
        
        # Verify that the primary setting was applied
        if primary_display and success:
            self.refresh()  # Refresh display list
            primary_set = False
            
            for display in self.displays:
                if display['name'] == config[primary_display]['name'] and display.get('primary'):
                    primary_set = True
                    break
                    
            if not primary_set:
                # Try one more time to set the primary display
                logger.debug(f"Trying one more time to set {primary_display} as primary")
                if not self.set_primary(primary_display):
                    logger.warning(f"Failed to set {primary_display} as primary display")
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

    def _enable_display_as_primary(self, display_name: str, resolution: str = None, 
                                 position: str = None, relative_to: str = None) -> bool:
        """
        Enable a display and set it as primary in one operation.
        
        Args:
            display_name: Name of the display to enable
            resolution: Optional resolution string (e.g. "1920x1080")
            position: Optional position flag (e.g. "--right-of", "--left-of")
            relative_to: Optional display name to position relative to
            
        Returns:
            True if successful, False otherwise
        """
        display = self.get_display(display_name)
        if not display:
            logger.error(f"Display {display_name} not found")
            return False
            
        # Build xrandr command
        cmd = f"xrandr --output {display['name']} --auto --primary"
        
        if resolution:
            cmd += f" --mode {resolution}"
            
        if position and relative_to:
            # Check if the relative display exists
            relative_display = self.get_display(relative_to)
            if relative_display:
                cmd += f" {position} {relative_display['name']}"
                
        logger.debug(f"Executing enable as primary command: {cmd}")
        result = run_command(cmd)
        
        if result.returncode != 0:
            logger.error(f"Failed to enable display as primary: {result.stderr}")
            return False
            
        logger.debug(f"Enabled {display_name} as primary display successfully")
        self.refresh()
        return True
