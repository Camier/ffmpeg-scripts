#!/usr/bin/env python3
"""
FFmpeg Motion Vector Artistic Visualizer
Creates artistic motion vector visualizations using FFmpeg codecview and advanced processing.
Based on existing project techniques and FFmpeg motion vector extraction.
"""

import subprocess
import os
from pathlib import Path
import sys
import cv2
import numpy as np

class FFmpegMotionArtist:
    """Generate artistic motion vector visualizations using FFmpeg techniques."""
    
    def __init__(self):
        self.output_base = Path("/home/mik/VECTOR/motion_vector_art")
        self.output_base.mkdir(exist_ok=True)
        
    def create_motion_vector_art(self, video_path: str, video_name: str):
        """Create artistic motion vector visualizations for a video."""
        
        # Create output directory for this video
        output_dir = self.output_base / f"{video_name}_art"
        output_dir.mkdir(exist_ok=True)
        
        print(f"\n=== Creating Motion Vector Art for {video_name} ===")
        
        # 1. Basic Motion Vector Visualization (FFmpeg style)
        print("1. Basic motion vector visualization...")
        basic_output = output_dir / f"{video_name}_basic_mv.mp4"
        cmd_basic = [
            'ffmpeg', '-y', '-t', '10',  # First 10 seconds
            '-flags2', '+export_mvs',
            '-i', video_path,
            '-vf', 'codecview=mv=pf+bf+bb',
            '-c:v', 'libx264', '-crf', '18',
            str(basic_output)
        ]
        
        try:
            subprocess.run(cmd_basic, check=True, capture_output=True, text=True)
            print(f"   ✓ Created: {basic_output}")
        except subprocess.CalledProcessError as e:
            print(f"   ✗ Basic visualization failed: {e}")
        
        # 2. Isolated Motion Vectors (Artistic Enhancement)
        print("2. Isolated motion vectors with artistic enhancement...")
        isolated_output = output_dir / f"{video_name}_isolated_artistic.mp4"
        cmd_isolated = [
            'ffmpeg', '-y', '-t', '10',
            '-flags2', '+export_mvs',
            '-i', video_path,
            '-vf', (
                'split[original][vectors],'
                '[vectors]codecview=mv=pf+bf+bb[vectors],'
                '[vectors][original]blend=all_mode=difference128,'
                'eq=contrast=8:brightness=-0.4:saturation=1.5,'
                'scale=720:-2'
            ),
            '-c:v', 'libx264', '-crf', '15',
            str(isolated_output)
        ]
        
        try:
            subprocess.run(cmd_isolated, check=True, capture_output=True, text=True)
            print(f"   ✓ Created: {isolated_output}")
        except subprocess.CalledProcessError as e:
            print(f"   ✗ Isolated artistic failed: {e}")
        
        # 3. Color-Enhanced Motion Animation
        print("3. Color-enhanced motion animation...")
        color_output = output_dir / f"{video_name}_color_motion.mp4"
        cmd_color = [
            'ffmpeg', '-y', '-t', '10',
            '-flags2', '+export_mvs',
            '-i', video_path,
            '-vf', (
                'split[original][motion],'
                '[motion]codecview=mv=pf+bf+bb[motion],'
                '[motion]hue=h=sin(2*PI*t):s=1.2[colored_motion],'
                '[colored_motion][original]blend=all_mode=screen:opacity=0.7,'
                'eq=contrast=1.8:brightness=0.1:gamma=1.2'
            ),
            '-c:v', 'libx264', '-crf', '15',
            str(color_output)
        ]
        
        try:
            subprocess.run(cmd_color, check=True, capture_output=True, text=True)
            print(f"   ✓ Created: {color_output}")
        except subprocess.CalledProcessError as e:
            print(f"   ✗ Color motion failed: {e}")
        
        # 4. Frame Extraction for Analysis
        print("4. Extracting key frames with motion vectors...")
        frames_dir = output_dir / "frames"
        frames_dir.mkdir(exist_ok=True)
        
        cmd_frames = [
            'ffmpeg', '-y', '-t', '8',
            '-flags2', '+export_mvs',
            '-i', video_path,
            '-vf', 'codecview=mv=pf+bf+bb,fps=2',
            str(frames_dir / f"{video_name}_frame_%03d.png")
        ]
        
        try:
            subprocess.run(cmd_frames, check=True, capture_output=True, text=True)
            print(f"   ✓ Extracted frames to: {frames_dir}")
        except subprocess.CalledProcessError as e:
            print(f"   ✗ Frame extraction failed: {e}")
        
        # 5. High-Quality Motion Vector Overlay
        print("5. High-quality motion vector overlay...")
        hq_output = output_dir / f"{video_name}_hq_overlay.mp4"
        cmd_hq = [
            'ffmpeg', '-y', '-t', '10',
            '-flags2', '+export_mvs',
            '-i', video_path,
            '-vf', (
                'split[bg][motion],'
                '[motion]codecview=mv=pf+bf+bb[vectors],'
                '[bg]scale=720:-2[bg_scaled],'
                '[vectors]scale=720:-2[vectors_scaled],'
                '[bg_scaled][vectors_scaled]blend=all_mode=overlay:opacity=0.8'
            ),
            '-c:v', 'libx264', '-crf', '12', '-preset', 'slow',
            str(hq_output)
        ]
        
        try:
            subprocess.run(cmd_hq, check=True, capture_output=True, text=True)
            print(f"   ✓ Created: {hq_output}")
        except subprocess.CalledProcessError as e:
            print(f"   ✗ HQ overlay failed: {e}")
        
        # 6. Ballet-Specific: Enhanced Motion Tracking
        if 'ba' in video_name.lower() or 'ballet' in video_name.lower():
            print("6. Ballet-specific enhanced motion tracking...")
            ballet_output = output_dir / f"{video_name}_ballet_enhanced.mp4"
            cmd_ballet = [
                'ffmpeg', '-y', '-t', '10',
                '-flags2', '+export_mvs',
                '-i', video_path,
                '-vf', (
                    'split[orig][mv],'
                    '[mv]codecview=mv=pf+bf+bb[vectors],'
                    '[vectors]eq=contrast=10:brightness=-0.5[enhanced_vectors],'
                    '[enhanced_vectors]hue=h=240:s=2[blue_vectors],'
                    '[orig][blue_vectors]blend=all_mode=lighten:opacity=0.9,'
                    'unsharp=5:5:1.0'
                ),
                '-c:v', 'libx264', '-crf', '15',
                str(ballet_output)
            ]
            
            try:
                subprocess.run(cmd_ballet, check=True, capture_output=True, text=True)
                print(f"   ✓ Created: {ballet_output}")
            except subprocess.CalledProcessError as e:
                print(f"   ✗ Ballet enhancement failed: {e}")
        
        return output_dir
    
    def process_all_videos(self):
        """Process all available MP4 videos in the directory."""
        
        # Find all MP4 files
        video_files = [
            ("/home/mik/VECTOR/ba.mp4", "ba"),
            ("/home/mik/VECTOR/ballerina_archive.mp4", "ballerina_archive"),
            ("/home/mik/VECTOR/istockphoto-1190157881-640_adpp_is.mp4", "istock_ballet_1"),
            ("/home/mik/VECTOR/istockphoto-1190161149-640_adpp_is.mp4", "istock_ballet_2"),
            ("/home/mik/VECTOR/istockphoto-2030237020-640_adpp_is.mp4", "istock_ballet_3")
        ]
        
        results = []
        
        for video_path, video_name in video_files:
            if os.path.exists(video_path) and os.path.getsize(video_path) > 1000:
                try:
                    output_dir = self.create_motion_vector_art(video_path, video_name)
                    results.append((video_name, output_dir, "Success"))
                except Exception as e:
                    print(f"   ✗ Failed to process {video_name}: {e}")
                    results.append((video_name, None, f"Error: {e}"))
            else:
                print(f"   ⚠ Skipping {video_name}: file not found or too small")
                results.append((video_name, None, "Skipped"))
        
        # Summary
        print("\n" + "="*60)
        print("MOTION VECTOR ART GENERATION SUMMARY")
        print("="*60)
        
        for video_name, output_dir, status in results:
            print(f"{video_name:25} | {status}")
            if output_dir:
                print(f"{'':25} | Output: {output_dir}")
        
        print(f"\nAll artistic visualizations saved in: {self.output_base}")
        
        return results


def main():
    """Main function to generate motion vector artistic visualizations."""
    
    print("FFmpeg Motion Vector Artistic Visualizer")
    print("=" * 50)
    
    # Check if FFmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✓ FFmpeg is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ FFmpeg not found. Please install FFmpeg.")
        return
    
    # Create artist and process videos
    artist = FFmpegMotionArtist()
    results = artist.process_all_videos()
    
    print("\n🎨 Motion vector artistic visualization complete!")
    print("Check the generated files for artistic motion vector renderings.")


if __name__ == "__main__":
    main()