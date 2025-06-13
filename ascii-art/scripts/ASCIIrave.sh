#!/bin/bash

set -e

echo "🔊 Generating waveform frames from audio..."

mkdir -p frames_raw
ffmpeg -y -i Bees.flac -filter_complex \
"[0:a]showwaves=s=640x480:mode=cline:colors=0x00FFAA@0.8,format=gray" \
-frames:v 600 frames_raw/frame_%04d.png

echo "🎨 Converting PNG to ASCII with img2txt..."

mkdir -p frames_ascii

for f in frames_raw/*.png; do
  base=$(basename "$f" .png)
  ~/.local/bin/img2txt -W 120 -f utf8 "$f" > "frames_ascii/${base}.txt"
done

echo "💀 Applying minimal text glitches..."

mkdir -p frames_ascii_glitched

for f in frames_ascii/*.txt; do
  base=$(basename "$f")
  sed 's/[O0]/@/g; s/[l1]/|/g; s/[A-Z]/#/g' "$f" > "frames_ascii_glitched/${base}"
done

echo "🖼️ Rendering ASCII to PNG frames..."

mkdir -p frames_png

for f in frames_ascii_glitched/*.txt; do
  base=$(basename "$f" .txt)
  
  # Escape all '%' characters to avoid ImageMagick warnings
  ascii_text=$(sed 's/%/%%/g' "$f")

  convert -size 1280x720 xc:black \
    -font Courier -pointsize 12 -fill white \
    -gravity northwest -annotate +10+10 "$ascii_text" "frames_png/${base}.png"
done

echo "🎞️ Encoding final video..."

ffmpeg -y -framerate 30 -i frames_png/frame_%04d.png -i Bees.flac \
-c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p \
-c:a aac -b:a 192k -shortest \
-metadata:s:v:0 title="ASCII RAVE VISUALIZER" \
-metadata:s:a:0 title="Damos Room – Bees" \
ASCII_RAVE.mp4

echo "✅ Done! Your video is saved as ASCII_RAVE.mp4"