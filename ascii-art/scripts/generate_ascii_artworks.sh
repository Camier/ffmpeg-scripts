#!/bin/bash

# Super ASCII Art Visualizer - Batch Generator
# This script generates multiple ASCII art visualizations with different settings

# Set default audio file
DEFAULT_AUDIO="Heith.flac"
AUDIO_FILE=${1:-$DEFAULT_AUDIO}

# Ensure audio file exists
if [ ! -f "$AUDIO_FILE" ]; then
    echo "Error: Audio file '$AUDIO_FILE' not found"
    echo "Usage: $0 [audio_file]"
    exit 1
fi

# Get base name without extension
BASE_NAME=$(basename "$AUDIO_FILE" | sed 's/\.[^.]*$//')
echo "Using audio file: $AUDIO_FILE (Base name: $BASE_NAME)"

# Create output directory
OUTPUT_DIR="${BASE_NAME}_visualizations"
mkdir -p "$OUTPUT_DIR"
echo "Created output directory: $OUTPUT_DIR"

# Function to generate a visualization
generate_visualization() {
    local name="$1"
    local pattern="$2"
    local charset="$3"
    local colorscheme="$4"
    local duration="$5"
    local width="$6"
    local height="$7"
    local additional_params="$8"
    
    local output_file="${OUTPUT_DIR}/${BASE_NAME}_${name}.mp4"
    
    echo "Generating visualization: $name"
    echo "  Pattern: $pattern, Charset: $charset, Colors: $colorscheme"
    echo "  Dimensions: ${width}x${height}, Duration: ${duration}s"
    echo "  Output: $output_file"
    
    # Build command
    cmd="python3 ./super_ascii_visualizer.py"
    cmd+=" \"$AUDIO_FILE\" \"$output_file\""
    cmd+=" --pattern $pattern --charset $charset --color-scheme $colorscheme"
    cmd+=" --duration $duration --width $width --height $height"
    cmd+=" --quality high --no-timestamp --no-credits"
    
    # Add additional parameters if provided
    if [ -n "$additional_params" ]; then
        cmd+=" $additional_params"
    fi
    
    # Execute command
    echo "Executing: $cmd"
    eval "$cmd"
    
    echo "Completed: $name"
    echo "-------------------------------------------"
}

# Generate a variety of visualizations
echo "Starting batch generation of ASCII art visualizations..."

# Matrix-like visualization
generate_visualization "matrix" "matrix" "matrix" "hacker" "15" "80" "40" "--audio-reactive"

# Cyberpunk style
generate_visualization "cyberpunk" "vortex" "blocks" "cyberpunk" "15" "120" "60" "--pulse --audio-reactive"

# Psychedelic visualization
generate_visualization "psychedelic" "kaleidoscope" "braille" "rainbow" "15" "100" "50" "--randomize-chars 0.2 --audio-reactive"

# Retro visualization
generate_visualization "retro" "waveform" "symbols" "retrowave" "15" "80" "40" "--audio-reactive"

# Minimalist visualization
generate_visualization "minimal" "spectrum" "minimal" "mono" "15" "100" "50" "--audio-reactive"

# Abstract visualization
generate_visualization "abstract" "fractal" "stars" "neon" "15" "100" "50" "--audio-reactive --randomize-colors 0.5"

# Random visualization
generate_visualization "random" "random" "random" "random" "15" "100" "50" "--randomize-chars 0.3 --randomize-colors 0.5 --audio-reactive"

# Elegant visualization
generate_visualization "elegant" "ripple" "waves" "pastel" "15" "120" "60" "--audio-reactive"

echo "All visualizations completed!"
echo "Output files are in: $OUTPUT_DIR"