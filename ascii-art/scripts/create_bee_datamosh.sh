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

# Extract audio waveform image for visualization
ffmpeg -i "$INPUT_AUDIO" -filter_complex \
"showwavespic=s=${WIDTH}x400:colors=ffff00|ffffff:scale=sqrt:filter=peak" \
"$TEMP_DIR/waveform.png"

# Create visualization with multiple layers for the data-mosh effect
ffmpeg -y \
-i "$INPUT_AUDIO" \
-filter_complex "
# Generate base canvas
color=s=${WIDTH}x${HEIGHT}:c=black:r=30[base];

# Create audio reactivity using spectrum analyzer with bee-like yellow color
[0:a]showspectrum=s=${WIDTH}x${HEIGHT}:mode=combined:slide=scroll:scale=cbrt:color=inferno:gain=5:saturation=10[spectrum];

# Create wave visualization that will drive particle movement
[0:a]showwaves=s=${WIDTH}x${HEIGHT}:r=30:mode=p2p:scale=sqrt:colors=gold:draw=full:point=0:n=2[wave];

# Create a time-based movement pattern using vectorscope for swarming effect
[0:a]avectorscope=s=${WIDTH}x${HEIGHT}:zoom=1.5:rc=0:gc=1:bc=0:rf=0:gf=40:bf=0:draw=line:scale=cbrt[vector];

# Create pulsing hexagonal grid for honeycomb effect
nullsrc=s=${WIDTH}x${HEIGHT},format=rgba,
geq='r=128+127*sin((x/16+y/16+t*2)*2):g=128+127*sin((x/12+y/12+t*2)*2):b=0:
    a=255*(mod(((x-${WIDTH}/2)^2+(y-${HEIGHT}/2)^2)^(0.5)/20,2)<1)*
    (mod(atan2(y-${HEIGHT}/2,x-${WIDTH}/2)*3/PI+t/2,1)>0.5)*
    (sin(t*2+x/100+y/100)+1)/2*
    (sin(sqrt((x-${WIDTH}/2)^2+(y-${HEIGHT}/2)^2)/20)+1)',
hue=H=t*10+180[hexgrid];

# Create particle system for bee-like movement
nullsrc=s=${WIDTH}x${HEIGHT},format=rgba,
geq='r=255:g=255:b=0:
    a=255*exp(-((x/2-${WIDTH}/4+100*sin(t/2+random(1)))^2+(y/2-${HEIGHT}/4+100*cos(t/3+random(1)))^2)/1000)*
    (sin(t*10+x/10+y/10+random(3))>0)',
colorchannelmixer=aa=0.7[particles1];

nullsrc=s=${WIDTH}x${HEIGHT},format=rgba,
geq='r=255:g=190:b=0:
    a=255*exp(-((x/2-${WIDTH}/4+120*sin(t/3+0.1+random(1)))^2+(y/2-${HEIGHT}/4+120*cos(t/2+0.2+random(1)))^2)/800)*
    (sin(t*8+x/20+y/15+random(2))>0)',
colorchannelmixer=aa=0.7[particles2];

nullsrc=s=${WIDTH}x${HEIGHT},format=rgba,
geq='r=255:g=220:b=0:
    a=255*exp(-((x/2-${WIDTH}/4+150*sin(t/4+0.3+random(1)))^2+(y/2-${HEIGHT}/4+150*cos(t/5+0.4+random(1)))^2)/600)*
    (sin(t*6+x/30+y/25+random(4))>0)',
colorchannelmixer=aa=0.7[particles3];

# Blend layers with data-mosh techniques
[base][spectrum]blend=all_mode=overlay:all_opacity=0.4[base1];
[base1][wave]blend=all_mode=screen:all_opacity=0.3[base2];
[base2][vector]blend=all_mode=screen:all_opacity=0.4[base3];
[base3][hexgrid]blend=all_mode=overlay:all_opacity=0.5[base4];
[base4][particles1]blend=all_mode=screen:all_opacity=0.6[base5];
[base5][particles2]blend=all_mode=screen:all_opacity=0.7[base6];
[base6][particles3]blend=all_mode=screen:all_opacity=0.8[combined];

# Add motion blur effect for trails
[combined]tmix=frames=8:weights='0.05 0.1 0.15 0.2 0.2 0.15 0.1 0.05'[blurred];

# Apply glow effect
[blurred]split=2[blurry1][blurry2];
[blurry1]boxblur=20:5[blurred1];
[blurry2][blurred1]blend=all_mode=screen:all_opacity=0.5[glowing];

# Add text for bee trails
[glowing]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='BEES':fontsize=60:
fontcolor=yellow@0.3:x=(w-text_w)/2+100*sin(t):y=(h-text_h)/2+100*cos(t/1.5):shadowcolor=black@0.7:shadowx=2:shadowy=2,
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='BUZZ':fontsize=40:
fontcolor=yellow@0.3:x=w/4+50*sin(t*1.2+1):y=h/3+50*cos(t*1.5+2):shadowcolor=black@0.7:shadowx=2:shadowy=2,
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='HONEYCOMB':fontsize=50:
fontcolor=yellow@0.3:x=w*3/4+80*sin(t*0.8+3):y=h*2/3+80*cos(t+4):shadowcolor=black@0.7:shadowx=2:shadowy=2[text];

# Apply final color grading and datamosh effect
[text]eq=brightness=0.02:saturation=1.5:gamma=1.1,
unsharp=5:5:1.5:5:5:0.5,
hue=h=t*2[colored];

# Final touch - add scan lines and noise for glitch aesthetic
[colored]noise=alls=10:allf=t+10,
format=yuv420p[video]
" \
-map "[video]" -map 0:a \
-c:v libx264 -preset slow -crf 18 -tune film \
-c:a aac -b:a 192k \
-pix_fmt yuv420p \
-r 30 -shortest \
"$OUTPUT_VIDEO"

echo "Bee DataMosh visualization created: $OUTPUT_VIDEO"