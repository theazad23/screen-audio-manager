#!/bin/bash
# Installation script for Screen and Audio Manager

# Parse arguments
DEV_MODE=0
for arg in "$@"; do
  case $arg in
    --dev)
      DEV_MODE=1
      shift
      ;;
  esac
done

set -e

echo "=== Screen and Audio Manager Installation ==="
if [ $DEV_MODE -eq 1 ]; then
  echo "Installing in DEVELOPMENT MODE"
  echo "Changes to source files will be immediately available"
fi
echo

# Define paths
SRC_DIR="$(pwd)"
INSTALL_DIR="${HOME}/.local/bin/screen-audio-manager"
CONFIG_DIR="${HOME}/.config/screen-audio-manager"
DATA_DIR="${HOME}/.local/share/screen-audio-manager"
BIN_DIR="${HOME}/.local/bin"

# Create directories
echo "Creating directories..."
mkdir -p "${INSTALL_DIR}"
mkdir -p "${CONFIG_DIR}"
mkdir -p "${DATA_DIR}/logs"
mkdir -p "${BIN_DIR}"

# Copy or link files based on mode
echo "Installing files..."

if [ $DEV_MODE -eq 1 ]; then
  # Development mode: use symbolic links
  ln -sf "${SRC_DIR}/config" "${INSTALL_DIR}/"
  ln -sf "${SRC_DIR}/core" "${INSTALL_DIR}/"
  ln -sf "${SRC_DIR}/macros" "${INSTALL_DIR}/"
  ln -sf "${SRC_DIR}/utils" "${INSTALL_DIR}/"
  ln -sf "${SRC_DIR}/__init__.py" "${INSTALL_DIR}/"
  ln -sf "${SRC_DIR}/main.py" "${INSTALL_DIR}/"
  
  echo "Using symbolic links in development mode"
else
  # Production mode: copy files
  rm -rf "${INSTALL_DIR}/config" "${INSTALL_DIR}/core" "${INSTALL_DIR}/macros" "${INSTALL_DIR}/utils"
  cp -r ./config "${INSTALL_DIR}/"
  cp -r ./core "${INSTALL_DIR}/"
  cp -r ./macros "${INSTALL_DIR}/"
  cp -r ./utils "${INSTALL_DIR}/"
  cp ./__init__.py "${INSTALL_DIR}/"
  cp ./main.py "${INSTALL_DIR}/"
fi

# Create wrapper script
echo "Creating wrapper script..."
cat > "${BIN_DIR}/sam" << EOL
#!/bin/bash
# Wrapper script for Screen and Audio Manager

cd "${INSTALL_DIR}"
python3 main.py "\$@"
EOL

chmod +x "${BIN_DIR}/sam"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    echo
    echo "WARNING: ${BIN_DIR} is not in your PATH."
    echo "You should add it to your shell configuration file (.bashrc, .zshrc, etc.):"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo
fi

# Create desktop shortcuts for common macros
echo "Creating desktop shortcuts..."
DESKTOP_DIR="${HOME}/.local/share/applications"
mkdir -p "${DESKTOP_DIR}"

cat > "${DESKTOP_DIR}/sam-tv-mode.desktop" << EOL
[Desktop Entry]
Type=Application
Name=TV Mode
Comment=Switch to TV mode
Exec=${BIN_DIR}/sam apply tv
Icon=video-display
Terminal=false
Categories=Utility;
EOL

cat > "${DESKTOP_DIR}/sam-desk-mode.desktop" << EOL
[Desktop Entry]
Type=Application
Name=Desk Mode
Comment=Switch to desk mode
Exec=${BIN_DIR}/sam apply desk
Icon=video-display
Terminal=false
Categories=Utility;
EOL

cat > "${DESKTOP_DIR}/sam-dual-mode.desktop" << EOL
[Desktop Entry]
Type=Application
Name=Dual Mode
Comment=Enable both displays
Exec=${BIN_DIR}/sam apply dual
Icon=video-display
Terminal=false
Categories=Utility;
EOL

# Set permissions
chmod +x "${DESKTOP_DIR}/sam-tv-mode.desktop"
chmod +x "${DESKTOP_DIR}/sam-desk-mode.desktop"
chmod +x "${DESKTOP_DIR}/sam-dual-mode.desktop"

# Add keyboard shortcuts
echo
echo "To add keyboard shortcuts, use your desktop environment's settings:"
echo "  - For TV mode: ${BIN_DIR}/sam apply tv"
echo "  - For desk mode: ${BIN_DIR}/sam apply desk"
echo "  - For dual mode: ${BIN_DIR}/sam apply dual"
echo

# Run initial detection
echo "Running initial device detection..."
"${BIN_DIR}/sam" detect -s "${CONFIG_DIR}/initial_detection.json"

echo
echo "Installation complete!"
if [ $DEV_MODE -eq 1 ]; then
  echo "DEVELOPMENT MODE: Any changes to files in ${SRC_DIR} will be immediately available"
fi
echo "Run 'sam --help' for usage information."
echo
