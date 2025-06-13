#!/bin/bash

# audio_visual.sh - Audio visualization with FFmpeg and libcaca

# Default parameters
INPUT_FILE="/home/mik/CLOCOD/Bees.flac"
TEMP_DIR="/tmp/audio_visuals"
OUTFILE="audio_vis"
VIS_TYPE="avectorscope"  # Options: avectorscope, showwaves, showspectrum
DURATION=5
OFFSET=0
WIDTH=640
HEIGHT=480
FPS=25
OUTPUT_FORMAT="mp4"      # Options: mp4, ascii

# Parse command line arguments
while getopts "i:t:d:o:w:h:f:r:a" opt; do
  case $opt in
    i) INPUT_FILE="$OPTARG" ;;
    t) VIS_TYPE="$OPTARG" ;;
    d) DURATION="$OPTARG" ;;
    o) OFFSET="$OPTARG" ;;
    w) WIDTH="$OPTARG" ;;
    h) HEIGHT="$OPTARG" ;;
    f) OUTFILE="$OPTARG" ;;
    r) FPS="$OPTARG" ;;
    a) OUTPUT_FORMAT="ascii" ;;
    \?) echo "Invalid option -$OPTARG" >&2; exit 1 ;;
  esac
done

# Ensure output directory exists
mkdir -p "${TEMP_DIR}"
TEMP_FILE="${TEMP_DIR}/temp_vis.png"

# Size parameter for visualization
SIZE="${WIDTH}x${HEIGHT}"

echo "Generating audio visualization with FFmpeg..."

# Generate visualization based on selected type
case $VIS_TYPE in
  avectorscope)
    if [ "$OUTPUT_FORMAT" = "ascii" ]; then
      # For ASCII output, create a single frame
      ffmpeg -y -ss $OFFSET -t $DURATION -i "${INPUT_FILE}" \
        -filter_complex "[0:a]aformat=channel_layouts=stereo,avectorscope=s=${SIZE}:mode=lissajous:zoom=1.5[v]" \
        -map "[v]" -frames:v 1 -update 1 "${TEMP_FILE}"
    else
      # For MP4 output, create video
      ffmpeg -y -ss $OFFSET -t $DURATION -i "${INPUT_FILE}" \
        -filter_complex "[0:a]aformat=channel_layouts=stereo,avectorscope=s=${SIZE}:mode=lissajous:rate=${FPS}:zoom=1.5:draw=line:scale=sqrt[v]" \
        -map "[v]" -c:v libx264 -pix_fmt yuv420p -r ${FPS} "${OUTFILE}.mp4"
    fi
    ;;
  showwaves)
    if [ "$OUTPUT_FORMAT" = "ascii" ]; then
      # For ASCII output, create a single frame
      ffmpeg -y -ss $OFFSET -t $DURATION -i "${INPUT_FILE}" \
        -filter_complex "[0:a]aformat=channel_layouts=stereo,showwaves=s=${SIZE}:mode=cline:colors=0x00ffff|0xff00ff[v]" \
        -map "[v]" -frames:v 1 -update 1 "${TEMP_FILE}"
    else
      # For MP4 output, create video
      ffmpeg -y -ss $OFFSET -t $DURATION -i "${INPUT_FILE}" \
        -filter_complex "[0:a]aformat=channel_layouts=stereo,showwaves=s=${SIZE}:mode=p2p:colors=0x00ffff|0xff00ff:rate=${FPS}:scale=sqrt[v]" \
        -map "[v]" -c:v libx264 -pix_fmt yuv420p -r ${FPS} "${OUTFILE}.mp4"
    fi
    ;;
  showspectrum)
    if [ "$OUTPUT_FORMAT" = "ascii" ]; then
      # For ASCII output, create a single frame
      ffmpeg -y -ss $OFFSET -t $DURATION -i "${INPUT_FILE}" \
        -filter_complex "[0:a]aformat=channel_layouts=stereo,showspectrum=s=${SIZE}:color=rainbow:scale=log[v]" \
        -map "[v]" -frames:v 1 -update 1 "${TEMP_FILE}"
    else
      # For MP4 output, create video
      ffmpeg -y -ss $OFFSET -t $DURATION -i "${INPUT_FILE}" \
        -filter_complex "[0:a]aformat=channel_layouts=stereo,showspectrum=s=${SIZE}:slide=scroll:mode=combined:color=rainbow:scale=log[v0];[v0]fps=${FPS}[v]" \
        -map "[v]" -c:v libx264 -pix_fmt yuv420p "${OUTFILE}.mp4"
    fi
    ;;
  *)
    echo "Unknown visualization type: $VIS_TYPE"
    echo "Valid types: avectorscope, showwaves, showspectrum"
    exit 1
    ;;
esac

RESULT=$?
if [ $RESULT -ne 0 ]; then
  echo "Error generating visualization"
  exit 1
fi

# Handle ASCII output if selected
if [ "$OUTPUT_FORMAT" = "ascii" ]; then
  echo "Converting to ASCII art with libcaca..."
  
  # Use smaller dimensions for ASCII art to maintain proportions
  ASCII_WIDTH=$(($WIDTH / 8))
  ASCII_HEIGHT=$(($HEIGHT / 16))
  
  # Convert the image to ASCII art using libcaca's img2txt
  img2txt -W "${ASCII_WIDTH}" -H "${ASCII_HEIGHT}" -f utf8 "${TEMP_FILE}" > "${OUTFILE}.txt"
  
  if [ $? -ne 0 ]; then
    echo "Error converting to ASCII art"
    exit 1
  fi
  
  # Display the result
  echo "ASCII art saved to ${OUTFILE}.txt"
  cat "${OUTFILE}.txt"
  
  # Clean up
  rm "${TEMP_FILE}"
else
  # Report success for MP4 output
  if [ -f "${OUTFILE}.mp4" ] && [ -s "${OUTFILE}.mp4" ]; then
    echo "Video successfully created: ${OUTFILE}.mp4"
    echo "You can play it with: ffplay ${OUTFILE}.mp4"
  else
    echo "Error: Output file not created or empty"
    exit 1
  fi
fi

echo "Try different parameters for varied results:"
echo "  -i FILE       Input audio file (default: ${INPUT_FILE})"
echo "  -t TYPE       Visualization type (avectorscope, showwaves, showspectrum) (default: ${VIS_TYPE})"
echo "  -d DURATION   Duration in seconds to analyze (default: ${DURATION})"
echo "  -o OFFSET     Starting offset in seconds (default: ${OFFSET})"
echo "  -w WIDTH      Width (default: ${WIDTH})"
echo "  -h HEIGHT     Height (default: ${HEIGHT})"
echo "  -r FPS        Frames per second for video (default: ${FPS})"
echo "  -f OUTFILE    Output file name without extension (default: ${OUTFILE})"
echo "  -a            ASCII art output mode (default is MP4 video if not specified)"