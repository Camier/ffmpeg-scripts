#!/usr/bin/env python3
import os

# Key scripts to showcase
showcase_scripts = [
    {
        "path": "motion-vectors/basic/batch_motion_vectors.py",
        "desc": "Batch process multiple videos with motion vectors"
    },
    {
        "path": "ascii-art/scripts/ffmpegascii.sh", 
        "desc": "Simple FFmpeg to ASCII converter"
    },
    {
        "path": "ascii-art/scripts/modularscii.sh",
        "desc": "Modular ASCII generation system"
    }
]

for script in showcase_scripts:
    if os.path.exists(script["path"]):
        output_file = f"/mnt/c/Users/micka/Documents/{os.path.basename(script['path'])}"
        with open(script["path"], 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Copied {script['path']} to Windows ({len(content)} bytes)")
        print(f"  Description: {script['desc']}")
    else:
        print(f"✗ Not found: {script['path']}")
