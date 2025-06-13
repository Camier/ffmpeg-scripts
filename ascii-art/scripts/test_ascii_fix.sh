#!/bin/bash
#
# Test script for ASCII rendering fixes in AsciiSymphony Pro
#

# Set up error handling
set -e
trap 'echo "Error: Command failed with status $?"' ERR

echo "=================================================================="
echo "AsciiSymphony Pro ASCII Rendering Test"
echo "=================================================================="
echo

# Check dependencies
echo "Checking dependencies..."
dependencies=("python3" "ffmpeg")
missing=0

for dep in "${dependencies[@]}"; do
    if ! command -v "$dep" &> /dev/null; then
        echo "Error: $dep is required but not installed."
        missing=1
    fi
done

if [[ $missing -eq 1 ]]; then
    echo "Please install missing dependencies and try again."
    exit 1
fi

# Check for Python libraries
echo "Checking Python libraries..."
python3 -c "import PIL" 2>/dev/null || { echo "Installing Pillow..."; pip install pillow; }
python3 -c "import numpy" 2>/dev/null || { echo "Installing NumPy..."; pip install numpy; }

# Set variables
INPUT_FILE="Bees_nocover.flac"
TEST_DURATION=5

# Check if input file exists
if [[ ! -f "$INPUT_FILE" ]]; then
    echo "Error: Input file $INPUT_FILE not found."
    echo "Please make sure you're running this script from the AsciiSymphonyPro directory."
    exit 1
fi

echo
echo "=================================================================="
echo "Running Direct ASCII Renderer Test (recommended solution)"
echo "=================================================================="
chmod +x direct_ascii_renderer.py
./direct_ascii_renderer.py "$INPUT_FILE" "test_direct_ascii.mp4" "waves" "$TEST_DURATION"

echo
echo "=================================================================="
echo "Testing a different visualization mode (spectrum)"
echo "=================================================================="
./direct_ascii_renderer.py "$INPUT_FILE" "test_spectrum_ascii.mp4" "spectrum" "$TEST_DURATION"

echo
echo "=================================================================="
echo "Testing another visualization mode (cqt)"
echo "=================================================================="
./direct_ascii_renderer.py "$INPUT_FILE" "test_cqt_ascii.mp4" "cqt" "$TEST_DURATION"

echo
echo "=================================================================="
echo "Tests completed successfully!"
echo "=================================================================="
echo
echo "The following test files were created:"
echo "  - test_direct_ascii.mp4 (wave visualization)"
echo "  - test_spectrum_ascii.mp4 (spectrum visualization)"
echo "  - test_cqt_ascii.mp4 (CQT visualization)"
echo
echo "You can play these files to verify that ASCII art is visible in the output."
echo "For example: ffplay test_direct_ascii.mp4"
echo
echo "To integrate this fix into your AsciiSymphony Pro implementation,"
echo "please refer to the ASCII_RENDERING_FIX.md file for details."
echo "=================================================================="