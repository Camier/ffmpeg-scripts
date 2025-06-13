#!/bin/bash
set -e

mkdir -p frames_raw frames_ascii frames_ascii_glitched frames_png

echo "🔊 Preparing the incantation..."
ffmpeg -y -i Bees.flac -filter_complex "[0:a]showwaves=s=640x480:mode=cline:colors=0x440088@0.9" \
-frames:v 444 frames_raw/frame_%04d.png

echo "🎨 Carving waveforms into ASCII scripts..."
for f in frames_raw/*.png; do
  base=$(basename "$f" .png)
  ~/.local/bin/img2txt -W 120 -f utf8 "$f" > frames_ascii/"$base".txt
done

echo "💉 Injecting entropy into glyphs..."
for f in frames_ascii/*.txt; do
  base=$(basename "$f")
  perl -pe 's/[A-Z]/#/g; s/[o0]/@/g; s/[|\\\/]/╱/g; s/ +/ /g' "$f" \
  | shuf > frames_ascii_glitched/"$base"
done

echo "🕯️ Summoning raster spirits..."
for f in frames_ascii_glitched/*.txt; do
  base=$(basename "$f" .txt)
  ascii="$(cat "$f" | sed 's/%/%%/g')"
  convert -size 1280x720 xc:black -font Courier -pointsize 12 -fill white \
    -gravity northwest -annotate +10+10 "$ascii" frames_png/"$base".png
done

echo "🔁 Channeling hue madness..."
mkdir -p frames_final
for f in frames_png/*.png; do
  base=$(basename "$f")
  hue=$((RANDOM % 360))
  ffmpeg -y -i "$f" -vf "hue=h=$hue:b=1.25" frames_final/"${base}"
done

echo "📼 Binding glyphs to sound ritual..."
ffmpeg -y -framerate 30 -i frames_final/frame_%04d.png -i Bees.flac \
-c:v libx264 -crf 17 -preset veryslow -pix_fmt yuv420p \
-c:a aac -b:a 192k -shortest \
-metadata title="ASCII Glitch Ritual" \
ascii_darkarts.mp4

echo "✅ Your VHS of the ritual lives: ascii_darkarts.mp4"