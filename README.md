# Screen and Audio Manager

A modular Python-based tool for managing screen configurations and audio devices on Linux systems. The tool provides easy-to-use keyboard macros for switching between different display and audio configurations.

## Features

- Auto-detection of displays and audio devices
- Easily switch between predefined display/audio configurations (macros)
- Multiple modes supported out of the box:
  - **TV Mode**: Enables living room TV as primary display with TV audio
  - **Desk Mode**: Enables desk monitor as primary display with desk speakers
  - **Dual Mode**: Enables both displays with desk monitor as primary
- Command-line interface for all operations
- Desktop shortcuts integration
- Modular architecture for easy extension
- Dynamic configuration that works across different computers
- Supports both PulseAudio and Pipewire

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/screen-audio-manager.git
   cd screen-audio-manager
   ```

2. Run the installation script:
   ```bash
   ./install.sh
   ```

The script will install the program to `~/.local/bin/screen-audio-manager` and create a command-line wrapper `sam` in `~/.local/bin`.

## Usage

### Command-line Interface

The manager can be controlled using the `sam` command:

```bash
# Show help
sam --help

# Apply a macro
sam apply tv     # TV mode
sam apply desk   # Desk mode
sam apply dual   # Dual mode

# Detect devices
sam detect
sam detect --save mydevices.json

# Manage displays
sam display --list
sam display --enable "HDMI-1"
sam display --disable "DP-1"
sam display --primary "HDMI-1"

# Manage audio
sam audio --list
sam audio --output "alsa_output.pci-0000_00_1f.3.analog-stereo"
sam audio --volume 70 --device "alsa_output.pci-0000_00_1f.3.analog-stereo"

# Configure settings
sam config --show
sam config --update myconfig.json
sam config --reset
```

### Keyboard Shortcuts

To add keyboard shortcuts for the macros, use your desktop environment's settings:

- **TV Mode**: `sam apply tv`
- **Desk Mode**: `sam apply desk`
- **Dual Mode**: `sam apply dual`

## Configuration

The configuration is stored in `~/.config/screen-audio-manager/config.json`. You can modify it directly or use the `sam config` command.

### Default Configuration

The default configuration maps logical device names (`desk`, `tv`) to physical devices using keywords:

```json
{
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
        "desk": {"enabled": false},
        "tv": {"enabled": true, "primary": true}
      },
      "audio": {
        "output": "tv",
        "volume": 70
      }
    },
    "desk_mode": {
      "description": "Desk mode (disable TV, enable desk)",
      "displays": {
        "desk": {"enabled": true, "primary": true},
        "tv": {"enabled": false}
      },
      "audio": {
        "output": "desk",
        "volume": 50
      }
    },
    "dual_mode": {
      "description": "Dual mode (enable both, desk primary)",
      "displays": {
        "desk": {"enabled": true, "primary": true},
        "tv": {"enabled": true, "position": "--right-of", "relative_to": "desk"}
      },
      "audio": {
        "output": "desk",
        "volume": 50
      }
    }
  }
}
```

## Extending

To add a new macro:

1. Create a new file in the `macros` directory (use an existing macro as a template)
2. Add the macro configuration to the `config.json` file
3. Update the `main.py` file to include your new macro

## Requirements

- Python 3.6+
- xrandr (for display management)
- Either PulseAudio (pactl) or Pipewire (wpctl) for audio management

## License

MIT

## Troubleshooting

### Device Detection Issues

If the automatic device mapping doesn't work correctly, you can:

1. Run `sam detect` to see detected devices
2. Update the keywords in your configuration:
   ```bash
   sam config --show > myconfig.json
   # Edit myconfig.json to update keywords
   sam config --update myconfig.json
   ```

### Audio Not Switching

If audio doesn't switch correctly:

1. Check your audio system: `sam audio --list`
2. Update the audio device keywords in your configuration
3. Try setting the output device manually: `sam audio --output "device_name"`
