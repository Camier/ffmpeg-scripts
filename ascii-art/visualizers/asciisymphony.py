#!/usr/bin/env python3
"""
AsciiSymphony - Creative audio visualization using libcaca and FFmpeg

This script converts audio files into ASCII art visualizations by:
1. Extracting audio features using FFmpeg
2. Generating real-time ASCII art using libcaca
3. Rendering the results as a video or animation

Requires:
- FFmpeg
- libcaca (with img2txt utility)
- Python 3.6+
"""

import argparse
import os
import sys
import subprocess
import tempfile
import shutil
import json
import time
import threading
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Union

@dataclass
class VisualizationOptions:
    """Configuration options for ASCII visualization"""
    width: int = 80
    height: int = 40
    format: str = "ansi"
    dither: str = "fstein"
    brightness: float = 1.0
    contrast: float = 1.2
    fps: int = 25
    color: bool = True
    invert: bool = False
    output_file: str = "output.mp4"
    temp_dir: Optional[str] = None
    visualization_type: str = "spectrum"  # spectrum, waveform, spectrogram
    reactive_colors: bool = True
    font_size: int = 12
    background_color: str = "black"

class AudioFeatures:
    """Extracts and manages audio features for visualization"""
    
    def __init__(self, audio_file: str):
        self.audio_file = audio_file
        self.duration = self._get_duration()
        self.sample_rate = self._get_sample_rate()
        self.temp_dir = None
    
    def _get_duration(self) -> float:
        """Get audio duration in seconds"""
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", self.audio_file
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    
    def _get_sample_rate(self) -> int:
        """Get audio sample rate"""
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "a:0", 
            "-show_entries", "stream=sample_rate", "-of", "json", self.audio_file
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return int(data["streams"][0]["sample_rate"])
    
    def extract_frames(self, temp_dir: str, fps: int = 25) -> str:
        """Extract audio visualization frames to temporary directory"""
        self.temp_dir = temp_dir
        frames_dir = os.path.join(temp_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        
        total_frames = int(self.duration * fps)
        print(f"⏳ Extracting {total_frames} audio visualization frames...")
        
        # Create a progress bar
        progress_thread = threading.Thread(
            target=self._show_progress,
            args=(total_frames,)
        )
        progress_thread.daemon = True
        progress_thread.start()
        
        # Generate visualization frames based on audio
        filter_complex = self._get_filter_complex(fps)
        
        cmd = [
            "ffmpeg", "-y", "-i", self.audio_file, "-filter_complex", filter_complex,
            "-fps_mode", "vfr", "-frame_size", "64", "-f", "rawvideo",
            "-pix_fmt", "rgb24", os.path.join(frames_dir, "frame%05d.raw")
        ]
        
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("\n✅ Frame extraction complete!")
        return frames_dir
    
    def _get_filter_complex(self, fps: int) -> str:
        """Get FFmpeg filter complex string for audio visualization"""
        return (
            f"showspectrum=s=640x480:mode=combined:color=rainbow:scale=lin:slide=replace:fps={fps},"
            "format=rgb24"
        )
    
    def _show_progress(self, total_frames: int):
        """Display a progress bar during frame extraction"""
        while not os.path.exists(self.temp_dir):
            time.sleep(0.1)
        
        frames_dir = os.path.join(self.temp_dir, "frames")
        prev_count = 0
        
        while True:
            if not os.path.exists(frames_dir):
                time.sleep(0.5)
                continue
                
            files = os.listdir(frames_dir)
            count = len([f for f in files if f.startswith("frame") and f.endswith(".raw")])
            
            if count != prev_count:
                progress = min(count / total_frames, 1.0)
                bar_length = 40
                filled = int(bar_length * progress)
                bar = "█" * filled + "░" * (bar_length - filled)
                percent = int(progress * 100)
                sys.stdout.write(f"\r|{bar}| {percent}% ({count}/{total_frames} frames)")
                sys.stdout.flush()
                prev_count = count
            
            if count >= total_frames:
                break
                
            time.sleep(0.5)

class AsciiRenderer:
    """Converts raw frames to ASCII art using libcaca"""
    
    def __init__(self, options: VisualizationOptions):
        self.options = options
    
    def convert_frames(self, frames_dir: str, ascii_dir: str):
        """Convert raw frames to ASCII art"""
        os.makedirs(ascii_dir, exist_ok=True)
        
        frames = sorted([f for f in os.listdir(frames_dir) if f.endswith(".raw")])
        total_frames = len(frames)
        
        print(f"🎨 Converting {total_frames} frames to ASCII art...")
        
        frame_width = 640
        frame_height = 480
        
        for i, frame in enumerate(frames):
            progress = (i + 1) / total_frames
            bar_length = 40
            filled = int(bar_length * progress)
            bar = "█" * filled + "░" * (bar_length - filled)
            percent = int(progress * 100)
            sys.stdout.write(f"\r|{bar}| {percent}% ({i+1}/{total_frames} frames)")
            sys.stdout.flush()
            
            # Use img2txt to convert raw frame to ASCII
            input_path = os.path.join(frames_dir, frame)
            output_path = os.path.join(ascii_dir, frame.replace(".raw", f".{self.options.format}"))
            
            # Convert raw to PNG first
            temp_png = input_path.replace(".raw", ".png")
            raw_to_png_cmd = [
                "ffmpeg", "-y", "-f", "rawvideo", "-pixel_format", "rgb24",
                "-video_size", f"{frame_width}x{frame_height}",
                "-i", input_path, "-frames:v", "1", temp_png
            ]
            subprocess.run(raw_to_png_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Now convert to ASCII with img2txt
            cmd = [
                "img2txt", "-W", str(self.options.width), "-H", str(self.options.height),
                "-f", self.options.format, "-d", self.options.dither,
                "-b", str(self.options.brightness), "-c", str(self.options.contrast)
            ]
            
            if self.options.invert:
                cmd.append("--invert")
            
            cmd.append(temp_png)
            
            with open(output_path, "w") as f:
                subprocess.run(cmd, stdout=f, stderr=subprocess.DEVNULL)
            
            # Clean up temporary PNG
            os.remove(temp_png)
        
        print("\n✅ ASCII conversion complete!")
        return ascii_dir

class VideoGenerator:
    """Compiles ASCII frames into a video"""
    
    def __init__(self, options: VisualizationOptions):
        self.options = options
    
    def create_video(self, ascii_dir: str, output_file: str):
        """Create video from ASCII frames"""
        print("🎬 Generating final video...")
        
        frames = sorted([f for f in os.listdir(ascii_dir) 
                        if f.endswith(f".{self.options.format}")])
        
        if self.options.format == "ansi":
            self._compile_ansi_to_video(ascii_dir, frames, output_file)
        elif self.options.format == "html":
            self._compile_html_to_video(ascii_dir, frames, output_file)
        elif self.options.format == "svg":
            self._compile_svg_to_video(ascii_dir, frames, output_file)
        else:
            print(f"❌ Unsupported output format: {self.options.format}")
            return
        
        print(f"✅ Video created successfully: {output_file}")
    
    def _compile_ansi_to_video(self, ascii_dir: str, frames: List[str], output_file: str):
        """Compile ANSI frames to video"""
        # First convert ANSI frames to PNGs using a terminal emulator
        png_dir = os.path.join(os.path.dirname(ascii_dir), "png_frames")
        os.makedirs(png_dir, exist_ok=True)
        
        terminal_width = self.options.width + 5  # Add some margin
        terminal_height = self.options.height + 5
        
        for i, frame in enumerate(frames):
            progress = (i + 1) / len(frames)
            bar_length = 40
            filled = int(bar_length * progress)
            bar = "█" * filled + "░" * (bar_length - filled)
            percent = int(progress * 100)
            sys.stdout.write(f"\r|{bar}| {percent}% ({i+1}/{len(frames)} frames)")
            sys.stdout.flush()
            
            frame_path = os.path.join(ascii_dir, frame)
            png_path = os.path.join(png_dir, frame.replace(f".{self.options.format}", ".png"))
            
            # Use xterm or similar to render ANSI to image
            term_cmd = [
                "terminal-to-image", 
                "--cols", str(terminal_width),
                "--rows", str(terminal_height),
                "--font-size", str(self.options.font_size),
                "--background", self.options.background_color,
                frame_path, png_path
            ]
            
            try:
                subprocess.run(term_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                # Fall back to xterm if terminal-to-image is not available
                xterm_cmd = [
                    "xterm", "-geometry", f"{terminal_width}x{terminal_height}",
                    "-e", f"cat {frame_path}; sleep 0.5"
                ]
                subprocess.run(xterm_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Take a screenshot of xterm (not ideal but works as fallback)
                shot_cmd = [
                    "import", "-window", "xterm", png_path
                ]
                subprocess.run(shot_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("\n🔄 Converting frames to video...")
        
        # Now create video from PNGs
        video_cmd = [
            "ffmpeg", "-y", "-framerate", str(self.options.fps),
            "-pattern_type", "glob", "-i", f"{png_dir}/*.png",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            output_file
        ]
        subprocess.run(video_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def _compile_html_to_video(self, ascii_dir: str, frames: List[str], output_file: str):
        """Compile HTML frames to video using a headless browser"""
        # Convert HTML to PNGs using a headless browser
        png_dir = os.path.join(os.path.dirname(ascii_dir), "png_frames")
        os.makedirs(png_dir, exist_ok=True)
        
        for i, frame in enumerate(frames):
            progress = (i + 1) / len(frames)
            bar_length = 40
            filled = int(bar_length * progress)
            bar = "█" * filled + "░" * (bar_length - filled)
            percent = int(progress * 100)
            sys.stdout.write(f"\r|{bar}| {percent}% ({i+1}/{len(frames)} frames)")
            sys.stdout.flush()
            
            frame_path = os.path.join(ascii_dir, frame)
            png_path = os.path.join(png_dir, frame.replace(f".{self.options.format}", ".png"))
            
            # Use wkhtmltopng or similar to render HTML to image
            html_cmd = [
                "wkhtmltoimage", "--width", str(self.options.width * 10),
                "--height", str(self.options.height * 20),
                frame_path, png_path
            ]
            
            try:
                subprocess.run(html_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                print("\n❌ wkhtmltoimage not found. Please install it to convert HTML frames.")
                return
        
        print("\n🔄 Converting frames to video...")
        
        # Now create video from PNGs
        video_cmd = [
            "ffmpeg", "-y", "-framerate", str(self.options.fps),
            "-pattern_type", "glob", "-i", f"{png_dir}/*.png",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            output_file
        ]
        subprocess.run(video_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def _compile_svg_to_video(self, ascii_dir: str, frames: List[str], output_file: str):
        """Compile SVG frames to video"""
        # Convert SVGs to PNGs using rsvg-convert or similar
        png_dir = os.path.join(os.path.dirname(ascii_dir), "png_frames")
        os.makedirs(png_dir, exist_ok=True)
        
        for i, frame in enumerate(frames):
            progress = (i + 1) / len(frames)
            bar_length = 40
            filled = int(bar_length * progress)
            bar = "█" * filled + "░" * (bar_length - filled)
            percent = int(progress * 100)
            sys.stdout.write(f"\r|{bar}| {percent}% ({i+1}/{len(frames)} frames)")
            sys.stdout.flush()
            
            frame_path = os.path.join(ascii_dir, frame)
            png_path = os.path.join(png_dir, frame.replace(f".{self.options.format}", ".png"))
            
            # Use rsvg-convert to render SVG to image
            svg_cmd = [
                "rsvg-convert", "-w", str(self.options.width * 10),
                "-h", str(self.options.height * 20),
                "-o", png_path, frame_path
            ]
            
            try:
                subprocess.run(svg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                print("\n❌ rsvg-convert not found. Please install it to convert SVG frames.")
                return
        
        print("\n🔄 Converting frames to video...")
        
        # Now create video from PNGs
        video_cmd = [
            "ffmpeg", "-y", "-framerate", str(self.options.fps),
            "-pattern_type", "glob", "-i", f"{png_dir}/*.png",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            output_file
        ]
        subprocess.run(video_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def check_dependencies():
    """Check if required dependencies are installed"""
    dependencies = {
        "ffmpeg": "FFmpeg is required for audio processing",
        "ffprobe": "FFprobe (part of FFmpeg) is required for audio analysis",
        "img2txt": "img2txt (part of libcaca) is required for ASCII conversion"
    }
    
    missing = []
    
    for dep, message in dependencies.items():
        if shutil.which(dep) is None:
            missing.append(f"❌ {dep}: {message}")
    
    if missing:
        print("Missing dependencies:")
        for msg in missing:
            print(msg)
        print("\nPlease install the required dependencies before running this script.")
        sys.exit(1)
    
    print("✅ All dependencies found!")

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(
        description="AsciiSymphony - Create ASCII art visualizations from audio files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("input_file", help="Input audio file")
    parser.add_argument("-o", "--output", default="output.mp4", help="Output video file")
    parser.add_argument("-w", "--width", type=int, default=80, help="ASCII art width")
    # Changed from -h to -H to avoid conflict with help
    parser.add_argument("-H", "--height", type=int, default=40, help="ASCII art height")
    parser.add_argument("-f", "--format", choices=["ansi", "html", "svg"], default="ansi",
                        help="Output format for ASCII frames")
    parser.add_argument("-d", "--dither", choices=["none", "ordered2", "ordered4", 
                                                 "ordered8", "random", "fstein"],
                        default="fstein", help="Dithering algorithm")
    parser.add_argument("-b", "--brightness", type=float, default=1.0, help="Brightness adjustment")
    parser.add_argument("-c", "--contrast", type=float, default=1.2, help="Contrast adjustment")
    parser.add_argument("--fps", type=int, default=25, help="Frames per second")
    parser.add_argument("--invert", action="store_true", help="Invert colors")
    parser.add_argument("--font-size", type=int, default=12, help="Font size for rendering")
    parser.add_argument("--background", default="black", help="Background color")
    parser.add_argument("-v", "--visualization", choices=["spectrum", "waveform", "spectrogram"],
                        default="spectrum", help="Visualization type")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary files")
    
    args = parser.parse_args()
    
    # Check dependencies
    check_dependencies()
    
    options = VisualizationOptions(
        width=args.width,
        height=args.height,  # This now correctly uses args.height
        format=args.format,
        dither=args.dither,
        brightness=args.brightness,
        contrast=args.contrast,
        fps=args.fps,
        invert=args.invert,
        output_file=args.output,
        visualization_type=args.visualization,
        font_size=args.font_size,
        background_color=args.background
    )
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        options.temp_dir = temp_dir
        
        print(f"🎵 Processing audio file: {args.input_file}")
        
        # Extract audio features and create visualization frames
        audio = AudioFeatures(args.input_file)
        frames_dir = audio.extract_frames(temp_dir, options.fps)
        
        # Convert frames to ASCII art
        ascii_renderer = AsciiRenderer(options)
        ascii_dir = os.path.join(temp_dir, "ascii_frames")
        ascii_renderer.convert_frames(frames_dir, ascii_dir)
        
        # Generate the final video
        video_generator = VideoGenerator(options)
        video_generator.create_video(ascii_dir, options.output_file)
        
        if args.keep_temp:
            # Copy temporary files to a permanent location if requested
            keep_dir = f"asciisymphony_temp_{int(time.time())}"
            shutil.copytree(temp_dir, keep_dir)
            print(f"✅ Temporary files saved to: {keep_dir}")
    
    print(f"🎉 Success! ASCII art visualization saved to: {options.output_file}")

if __name__ == "__main__":
    main()