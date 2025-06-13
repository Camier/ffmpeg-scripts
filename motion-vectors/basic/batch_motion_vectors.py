#!/usr/bin/env python3
"""
Batch FFmpeg Motion Vector Processor
Processes multiple videos in parallel with various motion vector styles
"""

import subprocess
import os
from pathlib import Path
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Tuple
import time

class BatchMotionVectorProcessor:
    """Batch process videos with FFmpeg motion vectors"""
    
    def __init__(self, output_base: str = "batch_motion_vectors"):
        self.output_base = Path(output_base)
        self.output_base.mkdir(exist_ok=True)
        
        # Simplified, fast-rendering styles for batch processing
        self.batch_styles = [
            {
                "name": "arrows_dense",
                "filter": "codecview=mv=pf+bf+bb",
                "suffix": "_dense"
            },
            {
                "name": "arrows_isolated",
                "filter": (
                    "split[a][b],"
                    "[b]codecview=mv=pf+bf+bb[v],"
                    "[v][a]blend=all_mode=difference128,"
                    "eq=contrast=8:brightness=-0.4"
                ),
                "suffix": "_isolated"
            },
            {
                "name": "arrows_high_contrast",
                "filter": (
                    "codecview=mv=pf+bf+bb,"
                    "eq=contrast=12:brightness=-0.5:gamma=0.6"
                ),
                "suffix": "_contrast"
            },
            {
                "name": "arrows_glow",
                "filter": (
                    "codecview=mv=pf+bf+bb,"
                    "gblur=sigma=2,"
                    "eq=contrast=3"
                ),
                "suffix": "_glow"
            }
        ]
    
    def find_all_videos(self) -> List[Path]:
        """Find all video files in VECTOR directory"""
        video_extensions = ['*.mp4', '*.webm', '*.avi', '*.mov']
        videos = []
        
        for ext in video_extensions:
            videos.extend(Path("/home/mik/VECTOR").glob(ext))
            videos.extend(Path("/home/mik/VECTOR").rglob(ext))
        
        # Remove duplicates and filter
        videos = list(set(videos))
        # Filter out already processed videos
        videos = [v for v in videos if 'motion_vector' not in str(v) and 'batch_motion' not in str(v)]
        
        return sorted(videos)[:20]  # Limit to 20 videos for batch
    
    def process_single_style(self, video_path: Path, style: Dict, 
                           start_time: float, duration: float) -> Dict:
        """Process a single video with one style"""
        
        video_name = video_path.stem
        output_dir = self.output_base / video_name
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"{video_name}{style['suffix']}.mp4"
        
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_time),
            '-t', str(duration),
            '-flags2', '+export_mvs',
            '-i', str(video_path),
            '-vf', style['filter'],
            '-c:v', 'libx264',
            '-crf', '23',  # Higher CRF for faster encoding
            '-preset', 'faster',  # Faster preset
            '-s', '1280x720',  # Limit resolution
            str(output_file)
        ]
        
        start = time.time()
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
            
            # Extract a few sample frames
            frames_dir = output_dir / f"{style['name']}_frames"
            frames_dir.mkdir(exist_ok=True)
            
            frame_cmd = [
                'ffmpeg', '-y',
                '-i', str(output_file),
                '-vf', 'fps=0.5',  # 1 frame every 2 seconds
                '-frames:v', '5',  # Max 5 frames
                str(frames_dir / 'frame_%02d.jpg')
            ]
            
            subprocess.run(frame_cmd, capture_output=True, check=True, timeout=30)
            
            return {
                'video': video_name,
                'style': style['name'],
                'output': str(output_file),
                'duration': time.time() - start,
                'success': True
            }
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            return {
                'video': video_name,
                'style': style['name'],
                'error': str(e)[:100],
                'duration': time.time() - start,
                'success': False
            }
    
    def get_key_moments(self, video_path: Path) -> List[Tuple[float, float]]:
        """Get key moments from video for processing"""
        
        # Get video duration
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json', str(video_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            duration = float(info['format']['duration'])
            
            # Extract 3 key moments
            moments = []
            
            # Beginning (first 5 seconds)
            moments.append((0, min(5, duration)))
            
            # Middle (if video is long enough)
            if duration > 20:
                mid_point = duration / 2
                moments.append((mid_point - 2.5, min(mid_point + 2.5, duration)))
            
            # Climax (around 70% if long enough)
            if duration > 30:
                climax = duration * 0.7
                moments.append((climax, min(climax + 5, duration)))
            
            return moments
            
        except:
            # Default to first 5 seconds
            return [(0, 5)]
    
    def process_video_batch(self, video_paths: List[Path], max_workers: int = 4):
        """Process multiple videos in parallel"""
        
        print(f"Processing {len(video_paths)} videos with {len(self.batch_styles)} styles each")
        print(f"Using {max_workers} parallel workers")
        print("="*60)
        
        all_tasks = []
        
        # Create tasks for each video and style combination
        for video_path in video_paths:
            moments = self.get_key_moments(video_path)
            
            for start, end in moments[:1]:  # Just use first moment for batch
                duration = end - start
                
                for style in self.batch_styles:
                    all_tasks.append((video_path, style, start, duration))
        
        print(f"Total tasks: {len(all_tasks)}")
        
        # Process in parallel
        results = []
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self.process_single_style, *task): task 
                for task in all_tasks
            }
            
            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                video_name = task[0].stem
                style_name = task[1]['name']
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        print(f"✓ {video_name} - {style_name} ({result['duration']:.1f}s)")
                    else:
                        print(f"✗ {video_name} - {style_name} (failed)")
                    
                except Exception as e:
                    print(f"✗ {video_name} - {style_name} (exception: {str(e)[:50]})")
                    results.append({
                        'video': video_name,
                        'style': style_name,
                        'error': str(e),
                        'success': False
                    })
                
                completed += 1
                if completed % 10 == 0:
                    print(f"Progress: {completed}/{len(all_tasks)} tasks")
        
        return results
    
    def create_batch_summary(self, results: List[Dict]):
        """Create summary of batch processing"""
        
        # Group results by video
        video_results = {}
        for result in results:
            video = result['video']
            if video not in video_results:
                video_results[video] = []
            video_results[video].append(result)
        
        # Create summary
        summary = {
            'total_videos': len(video_results),
            'total_tasks': len(results),
            'successful': sum(1 for r in results if r.get('success', False)),
            'failed': sum(1 for r in results if not r.get('success', False)),
            'styles': [s['name'] for s in self.batch_styles],
            'video_summaries': {}
        }
        
        for video, video_res in video_results.items():
            summary['video_summaries'][video] = {
                'total': len(video_res),
                'successful': sum(1 for r in video_res if r.get('success', False)),
                'outputs': [r.get('output') for r in video_res if r.get('output')]
            }
        
        # Save JSON summary
        with open(self.output_base / 'batch_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Create markdown summary
        md_summary = f"""# Batch Motion Vector Processing Summary

## Statistics
- Total Videos: {summary['total_videos']}
- Total Tasks: {summary['total_tasks']}
- Successful: {summary['successful']}
- Failed: {summary['failed']}
- Success Rate: {summary['successful']/summary['total_tasks']*100:.1f}%

## Styles Applied
"""
        
        for style in self.batch_styles:
            md_summary += f"- **{style['name']}**: {style['suffix']}\n"
        
        md_summary += "\n## Results by Video\n\n"
        
        for video, stats in sorted(summary['video_summaries'].items()):
            success_rate = stats['successful'] / stats['total'] * 100 if stats['total'] > 0 else 0
            md_summary += f"### {video}\n"
            md_summary += f"- Success: {stats['successful']}/{stats['total']} ({success_rate:.0f}%)\n"
            if stats['outputs']:
                md_summary += f"- Output Directory: `{Path(stats['outputs'][0]).parent}`\n"
            md_summary += "\n"
        
        with open(self.output_base / 'README.md', 'w') as f:
            f.write(md_summary)
        
        print(f"\n✓ Batch summary saved to: {self.output_base}/README.md")
        
        return summary


def main():
    """Main batch processing function"""
    
    print("FFmpeg Motion Vector Batch Processor")
    print("="*60)
    
    # Check FFmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
        print("✓ FFmpeg is available")
    except:
        print("✗ FFmpeg not found")
        return
    
    # Create processor
    processor = BatchMotionVectorProcessor()
    
    # Find videos
    print("\nSearching for videos...")
    videos = processor.find_all_videos()
    
    if not videos:
        print("No videos found")
        return
    
    print(f"Found {len(videos)} videos to process:")
    for i, video in enumerate(videos[:10]):  # Show first 10
        print(f"  {i+1}. {video.name}")
    
    if len(videos) > 10:
        print(f"  ... and {len(videos)-10} more")
    
    # Start processing
    print("\nStarting batch processing...")
    start_time = time.time()
    
    # Process with limited workers to avoid overload
    results = processor.process_video_batch(videos, max_workers=3)
    
    # Create summary
    summary = processor.create_batch_summary(results)
    
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"Batch processing complete!")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Average time per task: {total_time/len(results):.1f} seconds")
    print(f"Success rate: {summary['successful']/summary['total_tasks']*100:.1f}%")
    print(f"Output directory: {processor.output_base}")


if __name__ == "__main__":
    main()