#!/bin/bash
# Advanced Responsive ASCII Audio Visualizer
# Dynamically adapts to audio characteristics

INPUT_FILE="$1"
WIDTH="${2:-80}"   # Default width: 80 columns
HEIGHT="${3:-40}"  # Default height: 40 rows
DURATION="$4"      # Optional duration limit

DURATION_PARAM=""
if [ ! -z "$DURATION" ]; then
  DURATION_PARAM="-t $DURATION"
fi

if [ -z "$INPUT_FILE" ]; then
  echo "Error: Please provide an input audio file"
  echo "Usage: $0 audio_file.mp3 [width] [height] [duration_seconds]"
  exit 1
fi

echo "Advanced Responsive ASCII Audio Visualizer"
echo "Terminal size: ${WIDTH}x${HEIGHT}"
echo "Press Ctrl+C to stop"
sleep 1

# Create dynamic audio visualization pipeline
ffmpeg $DURATION_PARAM -i "$INPUT_FILE" -filter_complex "
# Extract audio volume for dynamic control
[0:a]volumedetect[vol];
[0:a]astats=metadata=1:reset=1,ametadata=mode=print:key=lavfi.astats.Overall.RMS_level:file=-[stats];

# Apply different visualizations based on detected characteristics
[0:a]asplit=3[a1][a2][a3];

# Base spectrum visualization
[a1]showspectrum=s=${WIDTH}x${HEIGHT}:slide=scroll:mode=combined:scale=log[spec];

# Frequency analysis with CQT
[a2]showcqt=s=${WIDTH}x${HEIGHT}:count=6:gamma=5:bar_g=2[cqt];

# Dynamic waveform visualization
[a3]showwaves=s=${WIDTH}x${HEIGHT}:mode=cline:n=80[waves];

# Apply color effects based on audio intensity
[spec]hue=h=t*20+if(gt(VOLUME,-20),VOLUME+20,0):s=if(gt(VOLUME,-30),1.5,1)[color_spec];
[cqt]edgedetect=low=0.1:high=0.4[edges];
[waves]negate[inv_waves];

# Combine all visualizations with blending
[color_spec][edges]blend=all_mode=screen:shortest=1[blend1];
[blend1][inv_waves]blend=all_mode=multiply:shortest=1,format=rgb24[final]
" \
-map "[final]" \
-f caca \
-charset blocks \
-algorithm fstein \
-color full16 \
-window_size "${WIDTH}x${HEIGHT}" -