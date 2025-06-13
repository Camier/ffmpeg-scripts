#!/bin/bash

# Define input and output paths
INPUT_AUDIO="/home/mik/CLOCOD/Damos Room - Bricolage - Bees - 02 Bees.flac"
OUTPUT_VIDEO="/home/mik/CLOCOD/DataMosh_Bees.mp4"
TEMP_DIR="/tmp/bee_datamosh"

# Create temp directory
mkdir -p "$TEMP_DIR"

# Video dimensions
WIDTH=1920
HEIGHT=1080

# FFmpeg command for data-mosh bee visualization
ffmpeg -y \
-i "$INPUT_AUDIO" \
-filter_complex "
color=s=${WIDTH}x${HEIGHT}:c=black:r=30[base];
[0:a]showspectrum=s=${WIDTH}x${HEIGHT}:mode=combined:slide=scroll:scale=cbrt:color=inferno:gain=5:saturation=10[spectrum];
[0:a]showwaves=s=${WIDTH}x${HEIGHT}:r=30:mode=p2p:scale=sqrt:colors=gold:draw=full[wave];
[0:a]avectorscope=s=${WIDTH}x${HEIGHT}:zoom=1.5:rc=0:gc=1:bc=0:rf=0:gf=40:bf=0:draw=line:scale=cbrt[vector];
[base][spectrum]blend=all_mode=overlay:all_opacity=0.4[base1];
[base1][wave]blend=all_mode=screen:all_opacity=0.3[base2];
[base2][vector]blend=all_mode=screen:all_opacity=0.4[base3];
[base3]tmix=frames=8:weights='0.05 0.1 0.15 0.2 0.2 0.15 0.1 0.05'[blurred];
[blurred]split=2[blurry1][blurry2];
[blurry1]boxblur=20:5[blurred1];
[blurry2][blurred1]blend=all_mode=screen:all_opacity=0.5[glowing];
[glowing]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='BUZZ':fontsize=80:fontcolor=yellow@0.4:x=w/2-200+200*sin(t/2):y=h/2+200*cos(t/3):shadowcolor=black@0.7:shadowx=2:shadowy=2[text];
[text]eq=brightness=0.06:saturation=2:gamma=1.1,hue=h=t*2,noise=alls=10:allf=t+10,format=yuv420p[video]
" \
-map "[video]" -map 0:a \
-c:v libx264 -preset medium -crf 18 -tune film \
-c:a aac -b:a 192k \
-pix_fmt yuv420p \
-r 30 -shortest \
"$OUTPUT_VIDEO"

echo "Bee DataMosh visualization created: $OUTPUT_VIDEO"