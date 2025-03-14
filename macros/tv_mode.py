#!/usr/bin/env python3
"""
TV mode macro - enables living room TV and audio.
"""
from core.display import DisplayManager
from core.audio import AudioManager
from config.devices import DeviceMapper
from config.settings import load_config
from utils.logger import logger

def apply_tv_mode() -> bool:
    """
    Apply TV mode configuration:
    - Enable living room TV
    - Make living room TV primary
    - Switch audio to living room TV
    - Disable desk monitor
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("Applying TV mode")
    success = True
    
    try:
        # Load configuration and mappings
        config = load_config()
        mapper = DeviceMapper(config)
        
        # Get macro configuration
        macro_config = config.get("macros", {}).get("tv_mode", {})
        if not macro_config:
            logger.error("TV mode configuration not found")
            return False
        
        # Set up display manager
        display_manager = DisplayManager()
        
        # Process displays
        display_configs = macro_config.get("displays", {})
        for logical_name, settings in display_configs.items():
            physical_name = mapper.get_display(logical_name)
            if not physical_name:
                logger.warning(f"Display '{logical_name}' not found in mappings")
                continue
            
            if settings.get("enabled") is False:
                if not display_manager.disable_display(physical_name):
                    success = False
            elif settings.get("enabled") is True:
                if not display_manager.enable_display(physical_name):
                    success = False
                if settings.get("primary") is True:
                    if not display_manager.set_primary(physical_name):
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
            logger.info("TV mode applied successfully")
        else:
            logger.warning("Some operations failed when applying TV mode")
        
        return success
    
    except Exception as e:
        logger.exception(f"Error applying TV mode: {e}")
        return False

if __name__ == "__main__":
    # When run directly, apply the TV mode
    apply_tv_mode()
