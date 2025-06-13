#!/bin/bash
# Run script for ASCII Symphony Pro with dynamic ASCII visualization

# Check if input file is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <input_audio_file> [mode] [colors]"
    echo
    echo "Modes: waves, spectrum, cqt, neural (default: waves)"
    echo "Colors: green, amber, blue, red, monochrome, thermal, rainbow, gradient, cyan, magenta (default: green)"
    echo
    echo "Example: $0 Bees.flac spectrum rainbow"
    exit 1
fi

INPUT_FILE="$1"
MODE="${2:-waves}"
COLORS="${3:-green}"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' not found"
    exit 1
fi

# Run the improved ASCII visualizer
echo "Running improved ASCII visualizer with file: $INPUT_FILE, mode: $MODE, colors: $COLORS"
python3 test_improved_ascii.py "$INPUT_FILE" --mode "$MODE" --colors "$COLORS"

# Offer to run the standard ASCII generator for comparison
echo
echo "Would you like to compare with the standard non-dynamic ASCII visualizer? (y/n)"
read -r COMPARE
if [[ "$COMPARE" == "y" || "$COMPARE" == "Y" ]]; then
    python3 test_ascii.py "$INPUT_FILE" "$MODE" "$COLORS"
fi

# Offer to run the full visualization
echo
echo "Would you like to run the full video visualization? (y/n)"
read -r FULL_VIZ
if [[ "$FULL_VIZ" == "y" || "$FULL_VIZ" == "Y" ]]; then
    echo "Running full video visualization..."
    
    # Create config file
    CONFIG_FILE="/tmp/ascii_symphony_config.json"
    cat > "$CONFIG_FILE" << EOF
{
    "input": "$INPUT_FILE",
    "output": "/tmp/output_visualization.mp4",
    "mode": "$MODE",
    "colors": "$COLORS",
    "width": 1280,
    "height": 720,
    "fps": 30,
    "quality": "high"
}
EOF
    
    # Run the visualization
    python3 ascii_symphony_fixed.py --config "$CONFIG_FILE"
    
    # Ask to play the output
    echo
    echo "Would you like to play the output video? (y/n)"
    read -r PLAY_VIDEO
    if [[ "$PLAY_VIDEO" == "y" || "$PLAY_VIDEO" == "Y" ]]; then
        # Check for video players and use the first one available
        if command -v ffplay >/dev/null 2>&1; then
            ffplay -autoexit "/tmp/output_visualization.mp4"
        elif command -v vlc >/dev/null 2>&1; then
            vlc --play-and-exit "/tmp/output_visualization.mp4"
        elif command -v mpv >/dev/null 2>&1; then
            mpv "/tmp/output_visualization.mp4"
        else
            echo "No video player found. Output is at /tmp/output_visualization.mp4"
        fi
    else
        echo "Output video saved to /tmp/output_visualization.mp4"
    fi
fi

echo "Done."