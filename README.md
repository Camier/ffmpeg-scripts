# FFmpeg Scripts Collection 🎬

A comprehensive collection of 50+ FFmpeg-based scripts for video processing, motion vector extraction, and ASCII art generation.

## 🚀 Overview

This repository contains specialized FFmpeg scripts organized into categories:

### 📊 Motion Vectors (5 scripts)
Extract and visualize motion data from videos for artistic and analytical purposes.

### 🎨 ASCII Art (47 scripts)
Convert videos to ASCII art with various styles and effects:
- **Visualizers** (15 Python scripts): Real-time ASCII video players
- **Scripts** (32 Shell scripts): Ready-to-use ASCII generators

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/ffmpeg-scripts.git
cd ffmpeg-scripts
```

2. **Install dependencies:**
```bash
# System dependencies
sudo apt-get install ffmpeg python3-pip

# Python dependencies
pip install numpy opencv-python pillow matplotlib tqdm colorama rich
```

## 💡 Quick Start

### Extract Motion Vectors
```bash
python motion-vectors/basic/ffmpeg_motion_vectors_simple.py input.mp4
```

### Generate ASCII Art
```bash
# Using shell script
./ascii-art/scripts/asciiwave.sh video.mp4

# Using Python visualizer
python ascii-art/visualizers/ascii_symphony_fixed.py video.mp4
```

## 📝 License

MIT License

## ⭐ Star this repository if you find it useful!