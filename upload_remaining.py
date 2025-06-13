#!/usr/bin/env python3
import os
import json

# Scripts already on GitHub
uploaded = {
    "motion-vectors/basic/ffmpeg_motion_vectors_simple.py",
    "motion-vectors/basic/batch_motion_vectors.py", 
    "motion-vectors/basic/simple_example.py",
    "ascii-art/scripts/asciiwave.sh",
    "ascii-art/scripts/ffmpegascii.sh",
    "ascii-art/scripts/modularscii.sh",
    "ascii-art/scripts/simple_ascii.sh"
}

# Scripts to upload
to_upload = []

# Motion vector scripts
mv_scripts = [
    "motion-vectors/artistic/ffmpeg_motion_artist.py",
    "motion-vectors/artistic/motion_vector_figure_art.py",
    "motion-vectors/basic/motion_vector_extractor.py"
]

# ASCII shell scripts (excluding already uploaded)
ascii_shell = [
    "ascii-art/scripts/ASCIIrave.sh",
    "ascii-art/scripts/advanced_caca_effects.sh",
    "ascii-art/scripts/ascii_darkarts.sh",
    "ascii-art/scripts/responsive-visualizer.sh",
    "ascii-art/scripts/create_bee_datamosh.sh",
    "ascii-art/scripts/enhanced-ascii-symphony.sh",
    "ascii-art/scripts/motion_vector_animation.sh"
]

# ASCII Python visualizers (sample)
ascii_python = [
    "ascii-art/visualizers/ascii_symphony_fixed.py",
    "ascii-art/visualizers/ascii_audio_visualizer.py",
    "ascii-art/visualizers/ascii_symphony_gui.py",
    "ascii-art/visualizers/asciisymphony_ultra_fixed.py"
]

# Prepare files for upload
all_files = mv_scripts + ascii_shell + ascii_python

for filepath in all_files:
    if os.path.exists(filepath) and filepath not in uploaded:
        output_file = f"/mnt/c/Users/micka/Documents/push_{filepath.replace('/', '_')}"
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Prepared {filepath} ({len(content)} bytes)")
        except Exception as e:
            print(f"✗ Error with {filepath}: {e}")

print(f"\nTotal files prepared: {len(all_files)}")
