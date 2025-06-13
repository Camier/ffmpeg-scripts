#!/bin/bash
set -e

# ✨ Create workspace
mkdir -p frames_raw frames_ascii frames_ascii_glitched frames_png frames_final

echo "🔊 Extracting spectrogram from the aether..."
ffmpeg -y -i Bees.flac -filter_complex \
"[0:a]showspectrum=s=640x480:mode=combined:color=intensity:scale=log" \
-frames:v 444 frames_raw/frame_%04d.png

echo "🔤 Transmuting visuals into ASCII glyphs..."
for f in frames_raw/*.png; do
  base=$(basename "$f" .png)
  ~/.local/bin/img2txt -W 120 -f utf8 "$f" > "frames_ascii/$base.txt"
done

echo "💉 Injecting corrupted glyph entropy..."
for f in frames_ascii/*.txt; do
  base=$(basename "$f")
  cat "$f" \
    | perl -pe 's/[A-Z]/#/g; s/[oO0]/@/g; s/[|\\\/]/╱/g;' \
    | shuf > "frames_ascii_glitched/$base"
done

echo "🖼️ Painting glyphs into black space..."
for f in frames_ascii_glitched/*.txt; do
  base=$(basename "$f" .txt)
  escaped=$(sed 's/%/%%/g' "$f")

  # Use a pleasant color instead of white
  convert -size 1280x720 xc:black \
    -font Courier -pointsize 12 -fill "#66CCFF" \
    -gravity northwest -annotate +10+10 "$escaped" \
    "frames_png/$base.png"
done

echo "🌈 Infusing chromatic aura over glyphs..."
for f in frames_png/*.png; do
  base=$(basename "$f")
  frame_index=$(echo "$base" | grep -o '[0-9]\+')
  hue=$(( (frame_index % 60) - 30 )) # gentle sweep from -30° to +30°
  
  ffmpeg -y -loglevel error -i "$f" \
    -vf "hue=h=$hue:s=1.1:b=1.05,boxblur=1:1" \
    -frames:v 1 -update 1 "frames_final/$base"
done

echo "📼 Binding images and frequencies..."
ffmpeg -y -framerate 30 -i frames_final/frame_%04d.png -i Bees.flac \
-c:v libx264 -crf 18 -preset veryslow -pix_fmt yuv420p \
-c:a aac -b:a 192k -shortest \
-metadata title="ᴀsᴄɪɪ 🜁 ɢʟɪᴛᴄʜ 🜃 ʀɪᴛᴜᴀʟ" \
ascii_spectrum_ritual.mp4

echo "✅ The ritual is encrypted within:  ascii_spectrum_ritual.mp4"