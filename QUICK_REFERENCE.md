# FFmpeg Scripts Quick Reference 🚀

## Most Popular Scripts

### 🎬 Motion Vector Extraction
```bash
# Basic extraction
python motion-vectors/basic/ffmpeg_motion_vectors_simple.py video.mp4

# Batch processing
python motion-vectors/basic/batch_motion_vectors.py /path/to/videos/

# Artistic motion flow
python motion-vectors/artistic/ffmpeg_motion_artist.py video.mp4
```

### 🎨 ASCII Art Generation

#### Top Shell Scripts
```bash
# Audio-reactive ASCII waves
./ascii-art/scripts/asciiwave.sh video.mp4

# Simple FFmpeg ASCII converter
./ascii-art/scripts/ffmpegascii.sh input.mp4

# Modular ASCII system
./ascii-art/scripts/modularscii.sh video.mp4
```

## 🛠️ Common Options

- `--width`: Set ASCII width (default: 80)
- `--height`: Set ASCII height (default: 24)
- `--chars`: Custom character set
- `--output-dir`: Specify output directory