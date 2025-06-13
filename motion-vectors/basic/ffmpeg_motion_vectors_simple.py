#!/usr/bin/env python3
"""
FFmpeg Motion Vector Extractor - Simple Version
Extracts motion vectors from ballet videos using only FFmpeg
No OpenCV dependencies
"""

import subprocess
import os
from pathlib import Path
import json
from typing import List, Dict, Tuple

class FFmpegMotionVectorExtractor:
    """Extract motion vectors using pure FFmpeg commands"""
    
    def __init__(self, output_base: str = "motion_vector_output"):
        self.output_base = Path(output_base)
        self.output_base.mkdir(exist_ok=True)
        
        # Motion vector styles using FFmpeg filters
        self.styles = [
            {
                "name": "dense_white_arrows",
                "filter": "codecview=mv=pf+bf+bb",
                "description": "Dense white arrows on black background"
            },
            {
                "name": "isolated_vectors",
                "filter": (
                    "split[original][vectors],"
                    "[vectors]codecview=mv=pf+bf+bb[vectors],"
                    "[vectors][original]blend=all_mode=difference128,"
                    "eq=contrast=10:brightness=-0.5"
                ),
                "description": "Isolated motion vectors only"
            },
            {
                "name": "glowing_arrows",
                "filter": (
                    "codecview=mv=pf+bf+bb,"
                    "split[v1][v2][v3],"
                    "[v1]gblur=sigma=1[b1],"
                    "[v2]gblur=sigma=3[b2],"
                    "[v3]gblur=sigma=5[b3],"
                    "[b1][b2]blend=all_mode=screen[b12],"
                    "[b12][b3]blend=all_mode=screen"
                ),
                "description": "Glowing motion arrows"
            },
            {
                "name": "high_contrast",
                "filter": (
                    "codecview=mv=pf+bf+bb,"
                    "eq=contrast=15:brightness=-0.6:gamma=0.5,"
                    "unsharp=5:5:2"
                ),
                "description": "Ultra high contrast vectors"
            },
            {
                "name": "color_time",
                "filter": (
                    "codecview=mv=pf+bf+bb,"
                    "hue=h=2*PI*t/10:s=2,"
                    "eq=contrast=3"
                ),
                "description": "Color changes over time"
            },
            {
                "name": "silhouette_reveal",
                "filter": (
                    "codecview=mv=pf+bf+bb,"
                    "negate,"
                    "erosion,erosion,"
                    "eq=contrast=5:brightness=-0.2"
                ),
                "description": "Reveals dancer silhouette"
            },
            {
                "name": "artistic_blend",
                "filter": (
                    "split[orig][mv],"
                    "[mv]codecview=mv=pf+bf+bb[vectors],"
                    "[vectors]colorkey=0x000000:0.3:0.2[vectors],"
                    "[orig][vectors]overlay,"
                    "eq=contrast=2:brightness=0.1"
                ),
                "description": "Artistic overlay blend"
            },
            {
                "name": "macroblock_detail",
                "filter": "codecview=mv=pf+bf+bb:mv_type=fp+bp",
                "description": "Detailed macroblock visualization"
            }
        ]
    
    def process_video_segment(self, video_path: str, output_path: str, 
                            filter_complex: str, start_time: float = 0, 
                            duration: float = 10) -> bool:
        """Process a video segment with specified filter"""
        
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_time),
            '-t', str(duration),
            '-flags2', '+export_mvs',
            '-i', str(video_path),
            '-vf', filter_complex,
            '-c:v', 'libx264', 
            '-crf', '18',
            '-preset', 'medium',
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ⚠ Error: {e.stderr[:200]}...")
            return False
    
    def extract_frames(self, video_path: str, output_pattern: str, 
                      start_time: float = 0, duration: float = 10, 
                      fps: float = 2) -> int:
        """Extract frames from video"""
        
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_time),
            '-t', str(duration),
            '-i', str(video_path),
            '-vf', f'fps={fps}',
            '-q:v', '2',
            str(output_pattern)
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            # Count extracted frames
            pattern_dir = Path(output_pattern).parent
            pattern_name = Path(output_pattern).name.replace('%04d', '*')
            frames = list(pattern_dir.glob(pattern_name))
            return len(frames)
        except:
            return 0
    
    def get_video_duration(self, video_path: str) -> float:
        """Get video duration using ffprobe"""
        
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json', str(video_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            return float(info['format']['duration'])
        except:
            return 0.0
    
    def process_video(self, video_path: str, segments: int = 3):
        """Process a video with all style variations"""
        
        video_path = Path(video_path)
        if not video_path.exists():
            print(f"✗ Video not found: {video_path}")
            return
        
        video_name = video_path.stem
        print(f"\n{'='*60}")
        print(f"Processing: {video_name}")
        print(f"{'='*60}")
        
        # Get video duration
        duration = self.get_video_duration(str(video_path))
        if duration == 0:
            print("✗ Could not determine video duration")
            return
        
        print(f"Video duration: {duration:.1f} seconds")
        
        # Create output directory
        output_dir = self.output_base / video_name
        output_dir.mkdir(exist_ok=True)
        
        # Calculate segment times (focus on dynamic parts)
        segment_duration = min(10, duration / segments)
        segment_times = []
        
        # Add beginning
        segment_times.append((0, min(10, duration)))
        
        # Add middle segments
        if duration > 30:
            # Add a segment around 30% (often contains establishing moves)
            segment_times.append((duration * 0.3, min(duration * 0.3 + 10, duration)))
            
            # Add a segment around 70% (often contains climactic moves)
            segment_times.append((duration * 0.7, min(duration * 0.7 + 10, duration)))
        
        # Process each segment with each style
        results = []
        
        for seg_idx, (start_time, end_time) in enumerate(segment_times):
            seg_duration = end_time - start_time
            seg_name = f"segment_{seg_idx+1}_t{int(start_time)}"
            seg_dir = output_dir / seg_name
            seg_dir.mkdir(exist_ok=True)
            
            print(f"\nSegment {seg_idx+1}: {start_time:.1f}s - {end_time:.1f}s ({seg_duration:.1f}s)")
            
            for style in self.styles:
                output_video = seg_dir / f"{style['name']}.mp4"
                print(f"  • {style['name']}: {style['description']}")
                
                success = self.process_video_segment(
                    str(video_path),
                    str(output_video),
                    style['filter'],
                    start_time,
                    seg_duration
                )
                
                if success:
                    # Extract sample frames
                    frames_dir = seg_dir / f"{style['name']}_frames"
                    frames_dir.mkdir(exist_ok=True)
                    frame_count = self.extract_frames(
                        str(output_video),
                        str(frames_dir / "frame_%04d.jpg"),
                        fps=2
                    )
                    
                    results.append({
                        'segment': seg_name,
                        'style': style['name'],
                        'output': str(output_video),
                        'frames': frame_count,
                        'success': True
                    })
                    print(f"    ✓ Success ({frame_count} frames extracted)")
                else:
                    results.append({
                        'segment': seg_name,
                        'style': style['name'],
                        'success': False
                    })
                    print(f"    ✗ Failed")
        
        # Create summary
        self.create_summary(output_dir, video_name, results)
        
        return output_dir
    
    def create_summary(self, output_dir: Path, video_name: str, results: List[Dict]):
        """Create processing summary"""
        
        successful = sum(1 for r in results if r.get('success', False))
        
        summary_text = f"""# Motion Vector Extraction Results

## Video: {video_name}

### Statistics
- Total Variations: {len(results)}
- Successful: {successful}
- Failed: {len(results) - successful}

### Styles Used
"""
        
        for style in self.styles:
            summary_text += f"- **{style['name']}**: {style['description']}\n"
        
        summary_text += "\n### Results by Segment\n"
        
        current_segment = None
        for result in results:
            if result['segment'] != current_segment:
                current_segment = result['segment']
                summary_text += f"\n#### {current_segment}\n"
            
            status = "✓" if result.get('success') else "✗"
            summary_text += f"- {status} {result.get('style', 'unknown')}"
            
            if result.get('frames'):
                summary_text += f" ({result['frames']} frames)"
            summary_text += "\n"
        
        # Save summary
        with open(output_dir / 'README.md', 'w') as f:
            f.write(summary_text)
        
        # Save JSON results
        with open(output_dir / 'results.json', 'w') as f:
            json.dump({
                'video': video_name,
                'output_dir': str(output_dir),
                'results': results,
                'styles': [s['name'] for s in self.styles]
            }, f, indent=2)
        
        print(f"\n✓ Summary saved to: {output_dir}/README.md")


def main():
    """Main function"""
    
    # Check FFmpeg availability
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✓ FFmpeg is available")
    except:
        print("✗ FFmpeg not found. Please install FFmpeg:")
        print("  sudo apt-get install ffmpeg")
        return
    
    # Video list
    videos = [
        "/home/mik/VECTOR/File:Pirouette_en_dedans.webm",
        "/home/mik/VECTOR/ballerina_archive.mp4",
        "/home/mik/VECTOR/Czech National Ballet (2160p_25fps_VP9 LQ-160kbit_Opus).webm",
        "/home/mik/VECTOR/pirouette_ballet.webm"
    ]
    
    # Process videos
    extractor = FFmpegMotionVectorExtractor()
    
    print("FFmpeg Motion Vector Extractor")
    print("=" * 60)
    print(f"Will process {len(videos)} videos with {len(extractor.styles)} styles each")
    
    for video_path in videos:
        if os.path.exists(video_path):
            extractor.process_video(video_path)
        else:
            print(f"\n⚠ Skipping {video_path}: File not found")
    
    print(f"\n✓ All outputs saved in: {extractor.output_base}")


if __name__ == "__main__":
    main()