#!/usr/bin/env python3
"""
Dual mode macro - enables both screens with desk as primary.
"""
from core.display import DisplayManager
from core.audio import AudioManager
from config.devices import DeviceMapper
from config.settings import load_config
from utils.logger import logger

def apply_dual_mode() -> bool:
    """
    Apply dual mode configuration:
    - Enable both monitors
    - Make desk monitor primary
    - Position TV relative to desk
    - Switch audio to specified output
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("Applying dual mode")
    success = True
    
    try:
        # Load configuration and mappings
        config = load_config()
        mapper = DeviceMapper(config)
        
        # Get macro configuration
        macro_config = config.get("macros", {}).get("dual_mode", {})
        if not macro_config:
            logger.error("Dual mode configuration not found")
            return False
        
        # Set up display manager
        display_manager = DisplayManager()
        
        # First, enable all displays
        display_configs = macro_config.get("displays", {})
        for logical_name, settings in display_configs.items():
            if settings.get("enabled") is True:
                physical_name = mapper.get_display(logical_name)
                if not physical_name:
                    logger.warning(f"Display '{logical_name}' not found in mappings")
                    continue
                
                if not display_manager.enable_display(physical_name):
                    success = False
        
        # Then, position displays relative to each other
        for logical_name, settings in display_configs.items():
            physical_name = mapper.get_display(logical_name)
            if not physical_name:
                continue
            
            position = settings.get("position")
            relative_to = settings.get("relative_to")
            
            if position and relative_to:
                relative_physical = mapper.get_display(relative_to)
                if relative_physical:
                    cmd = [
                        "xrandr", "--output", physical_name, 
                        position, relative_physical
                    ]
                    from utils.shell import run_command
                    result = run_command(" ".join(cmd))
                    if result.returncode != 0:
                        logger.error(f"Failed to position display: {result.stderr}")
                        success = False
        
        # Finally, set primary display
        for logical_name, settings in display_configs.items():
            if settings.get("primary") is True:
                physical_name = mapper.get_display(logical_name)
                if physical_name and not display_manager.set_primary(physical_name):
                    success = False
        
        # Set up audio manager
        audio_manager = AudioManager()
        
        # Set audio output
        audio_config = macro_config.get("audio", {})
        output_name = audio_config.get("output")
        if output_name:
            physical_output = mapper.get_audio_output(output_name)
            if physical_output:
                if not audio_manager.set_default_sink(physical_output):
                    success = False
            else:
                logger.warning(f"Audio output '{output_name}' not found in mappings")
        
        # Set volume if specified
        volume = audio_config.get("volume")
        if volume is not None and physical_output:
            if not audio_manager.set_volume(physical_output, volume):
                success = False
        
        if success:
            logger.info("Dual mode applied successfully")
        else:
            logger.warning("Some operations failed when applying dual mode")
        
        return success
    
    except Exception as e:
        logger.exception(f"Error applying dual mode: {e}")
        return False

if __name__ == "__main__":
    # When run directly, apply the dual mode
    apply_dual_mode()
