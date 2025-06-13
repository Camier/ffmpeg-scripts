import os
import json

# Read key motion vector scripts
files = []

# Motion vector scripts
mv_files = [
    "motion-vectors/basic/ffmpeg_motion_vectors_simple.py",
    "motion-vectors/basic/motion_vector_extractor.py", 
    "motion-vectors/basic/batch_motion_vectors.py",
    "motion-vectors/artistic/ffmpeg_motion_artist.py",
    "motion-vectors/artistic/motion_vector_figure_art.py"
]

for filepath in mv_files:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Save each file separately for manual processing
            output_file = f"/tmp/{filepath.replace('/', '_')}"
            with open(output_file, 'w', encoding='utf-8') as out:
                out.write(content)
            print(f"Saved {filepath} to {output_file} ({len(content)} bytes)")

# Save key ASCII scripts
ascii_files = [
    "ascii-art/scripts/asciiwave.sh",
    "ascii-art/scripts/ffmpegascii.sh",
    "ascii-art/scripts/modularscii.sh",
    "ascii-art/scripts/responsive-visualizer.sh",
    "ascii-art/visualizers/ascii_symphony_fixed.py"
]

for filepath in ascii_files:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            output_file = f"/tmp/{filepath.replace('/', '_')}"
            with open(output_file, 'w', encoding='utf-8') as out:
                out.write(content)
            print(f"Saved {filepath} to {output_file} ({len(content)} bytes)")
