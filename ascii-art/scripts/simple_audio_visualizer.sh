#!/bin/bash

# Simple Audio Visualizer Script
# This is a simplified version that creates basic audio visualizations

if [ $# -lt 2 ]; then
    echo "Usage: $0 input_audio output_video [mode]"
    echo "Modes: waves, spectrum, cqt, bars"
    echo "Example: $0 input.flac output.mp4 waves"
    exit 1
fi

INPUT="$1"
OUTPUT="$2"
MODE="${3:-waves}"

# Validate input file
if [ ! -f "$INPUT" ]; then
    echo "Error: Input file '$INPUT' not found"
    exit 1
fi

# Basic validation to ensure FFmpeg can read the file
duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$INPUT")
if [ $? -ne 0 ]; then
    echo "Error: FFmpeg cannot read the input file. Is it a valid audio file?"
    exit 1
fi

echo "Input: $INPUT (Duration: $duration seconds)"
echo "Output: $OUTPUT"
echo "Visualization mode: $MODE"

# Set visualization filter based on mode
case "$MODE" in
    "waves")
        FILTER="[0:a]showwaves=s=1280x720:mode=cline:colors=white,format=yuv420p[v]"
        ;;
    "spectrum")
        FILTER="[0:a]showspectrum=s=1280x720:mode=combined:slide=scroll:color=rainbow,format=yuv420p[v]"
        ;;
    "cqt")
        FILTER="[0:a]showcqt=s=1280x720:count=6:gamma=5,format=yuv420p[v]"
        ;;
    "bars")
        FILTER="[0:a]avectorscope=s=1280x720:zoom=2:draw=line,format=yuv420p[v]"
        ;;
    *)
        echo "Unknown mode '$MODE', using 'waves'"
        FILTER="[0:a]showwaves=s=1280x720:mode=cline:colors=white,format=yuv420p[v]"
        ;;
esac

# Create the visualization
echo "Creating visualization..."
# Use -map to select only the audio stream (avoid the cover art image)
ffmpeg -y -i "$INPUT" -filter_complex "$FILTER" -map "[v]" -map 0:a -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 192k "$OUTPUT"

if [ $? -eq 0 ]; then
    echo "Visualization created successfully: $OUTPUT"
else
    echo "Error: Failed to create visualization"
    exit 1
fi
