#!/bin/bash
# Installation script for Screen and Audio Manager

set -e

echo "=== Screen and Audio Manager Installation ==="
echo

# Define paths
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

# Copy files
echo "Copying files..."
cp -r ./config "${INSTALL_DIR}/"
cp -r ./core "${INSTALL_DIR}/"
cp -r ./macros "${INSTALL_DIR}/"
cp -r ./utils "${INSTALL_DIR}/"
cp ./__init__.py "${INSTALL_DIR}/"
cp ./main.py "${INSTALL_DIR}/"

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
echo "Run 'sam --help' for usage information."
echo
