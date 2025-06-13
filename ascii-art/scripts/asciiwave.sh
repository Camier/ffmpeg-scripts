#!/bin/bash

# Spectrum Waves: An advanced ASCII art audio visualization
# Usage: ./spectrum_waves.sh input.flac output.mp4

INPUT="$1"
OUTPUT="$2"

# Validate input parameters
if [ -z "$INPUT" ] || [ -z "$OUTPUT" ]; then
    echo "Usage: $0 input.flac output.mp4"
    exit 1
fi

# Create a temporary ASCII art output
TMP_DIR=$(mktemp -d)
TMP_ASCII="$TMP_DIR/ascii_art.txt"
TMP_VIDEO="$TMP_DIR/temp_video.mp4"

# Step 1: Create the complex visualization pipeline
ffmpeg -i "$INPUT" -filter_complex "
# Split audio for different visualizations
[0:a]asplit=3[a1][a2][a3];

# Create a spectrum visualization with color gradient
[a1]showspectrum=s=640x240:mode=combined:slide=scroll:scale=log:color=rainbow[spectrum];

# Create waveform with edge detection
[a2]showwaves=s=640x240:mode=p2p:n=30:draw=full:colors=0x00FFFF[waves];
[waves]edgedetect=low=0.1:high=0.4[edges];

# Create reactive beats visualization
[a3]showvolume=f=60:b=4:w=640:h=120:c=0xFFFFFF:t=0[volume];

# Stack and merge the visualizations
[spectrum][edges]vstack[upper];
[upper][volume]vstack[combined];

# Enhance color dynamics with audio reactivity
[combined]hue=h=t*10+if(gt(random(1),0.8),t%360,t):s=1+min(1,t/100)*sin(2*PI*t/30)[colored];

# Format for caca
[colored]format=rgb24[rgb]
" -map "[rgb]" -f caca -charset blocks -color full16 -algorithm fstein "$TMP_ASCII"

# Step 2: Convert ASCII art to video with ffmpeg
ffmpeg -f lavfi -i "color=c=black:s=1280x720:r=30" -vf "
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf:
fontsize=14:fontcolor=white:x=10:y=10:
textfile=$TMP_ASCII
" -c:v libx264 -crf 18 -preset veryslow -pix_fmt yuv420p "$TMP_VIDEO"

# Step 3: Add the original audio back to the video
ffmpeg -i "$TMP_VIDEO" -i "$INPUT" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k "$OUTPUT"

# Clean up temporary files
rm -rf "$TMP_DIR"

echo "Visualization complete: $OUTPUT"