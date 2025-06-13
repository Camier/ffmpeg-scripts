```bash
#!/bin/bash

# ASCII Video Converter Launcher Script
# This script ensures all dependencies are installed and launches the interactive terminal

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}         ASCII Video Converter - Interactive Terminal               ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check for required system tools
echo "Checking system dependencies..."

check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗ $1 not found${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $1 found${NC}"
        return 0
    fi
}

# Check for required tools
MISSING_TOOLS=0
check_tool ffmpeg || MISSING_TOOLS=1
check_tool ffprobe || MISSING_TOOLS=1
check_tool img2txt || MISSING_TOOLS=1

if [ $MISSING_TOOLS -eq 1 ]; then
    echo
    echo -e "${YELLOW}Missing required tools. Please install:${NC}"
    echo
    echo "On Ubuntu/Debian:"
    echo "  sudo apt-get install ffmpeg libcaca-utils"
    echo
    echo "On macOS with Homebrew:"
    echo "  brew install ffmpeg libcaca"
    echo
    echo "On Fedora/RHEL:"
    echo "  sudo dnf install ffmpeg libcaca"
    echo
    exit 1
fi

# Install Python dependencies
echo
echo "Installing Python dependencies..."
pip3 install --quiet rich numpy pillow opencv-python-headless pyyaml

# Optional: Install python-caca bindings if available
# pip3 install --quiet python-caca 2>/dev/null || true

echo
echo -e "${GREEN}All dependencies satisfied!${NC}"
echo
echo "Launching interactive terminal..."
echo

# Launch the converter
python3 video_to_ascii_interactive.py --interactive
```