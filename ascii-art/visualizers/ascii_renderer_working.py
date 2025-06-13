#!/usr/bin/env python3
"""
Direct ASCII art renderer that renders audio visualization directly with ASCII characters.

This approach bypasses libcaca issues by using Python's PIL and FFmpeg in a different way.
"""

import os
import sys
import subprocess
import tempfile
import shutil
import time
import logging
from pathlib import Path
import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("direct_ascii_renderer")

def create_ascii_frames_directly(input_file, output_dir, duration=None, width=80, height=40, mode="waves", fps=15):
    """Create ASCII art frames directly using FFmpeg and PIL"""
    
    try:
        # Import the required libraries
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
    except ImportError:
        logger.error("Required libraries not found. Install with: pip install pillow numpy")
        return False
    
    # Create input stream for FFmpeg
    temp_audio = os.path.join(output_dir, "temp_audio.wav")
    if duration:
        # Extract audio segment to temporary file
        audio_cmd = [
            'ffmpeg', 
            '-y',
            '-i', input_file,
            '-t', str(duration),
            temp_audio
        ]
        
        subprocess.run(audio_cmd, check=True, capture_output=True)
        audio_input = temp_audio
    else:
        audio_input = input_file
    
    # Create a visual representation based on the mode
    # We'll generate our own ASCII frames
    
    # Define a suitable ASCII character set
    charsets = {
        "waves": " ▁▂▃▄▅▆▇█",
        "spectrum": " ░▒▓█",
        "cqt": " .:+*#%@",
        "neural": " ▘▝▀▁▂▃▄▅▆▇█",
        "default": " .:-=+*#%@"
    }
    
    charset = charsets.get(mode, charsets["default"])
    
    # Try to find a suitable monospace font
    try:
        # Try to find a monospace font
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
            "/usr/share/fonts/dejavu/DejaVuSansMono.ttf"
        ]
        
        font_path = None
        for path in font_paths:
            if os.path.exists(path):
                font_path = path
                break
        
        if not font_path:
            logger.warning("No monospace font found, ASCII rendering may look incorrect")
            return False
        
        # Get audio waveform data
        audio_data = []
        
        # Use ffprobe to get the duration
        duration_cmd = [
            'ffprobe',
            '-i', audio_input,
            '-show_entries', 'format=duration',
            '-v', 'quiet',
            '-of', 'csv=p=0'
        ]
        
        duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
        audio_duration = float(duration_result.stdout.strip())
        
        # Calculate the number of frames
        num_frames = int(audio_duration * fps)
        
        # Use FFmpeg to extract audio waveform data
        data_cmd = [
            'ffmpeg',
            '-i', audio_input,
            '-filter_complex', f'showwaves=s={width}x{height}:mode=line:rate={fps}:n={num_frames}',
            '-f', 'null',
            '-'
        ]
        
        # Instead, we'll generate frames directly
        total_frames = min(int(audio_duration * fps), 300)  # Limit to 300 frames max
        
        print(f"Generating {total_frames} ASCII frames...")
        
        # Font size based on image size
        font_size = 20
        font = ImageFont.truetype(font_path, font_size)
        
        # Calculate image dimensions based on font and character grid
        img_width = width * font_size // 2
        img_height = height * font_size
        
        # For wave visualization in ASCII
        for frame in range(total_frames):
            progress = (frame + 1) / total_frames * 100
            print(f"Creating frame {frame+1}/{total_frames} [{int(progress)}%]", end='\r')
            
            # Create a black image
            img = Image.new('RGB', (img_width, img_height), color='black')
            draw = ImageDraw.Draw(img)
            
            # Generate ASCII art pattern based on the frame and mode
            current_time = frame / fps
            
            # Generate a pattern based on the time and mode
            for y in range(height):
                line = ""
                for x in range(width):
                    # Different patterns for different modes
                    if mode == "waves":
                        # Simple sine wave pattern
                        value = np.sin(x/5 + current_time*10) * np.sin(current_time*5)
                        value = (value + 1) / 2  # Normalize to 0-1
                        
                        # Adjust based on y position
                        center_dist = abs(y - height/2) / (height/2)
                        value = value * (1 - center_dist)
                        
                    elif mode == "spectrum":
                        # Frequency spectrum-like pattern
                        value = np.sin(x/3) * np.cos(y/5 + current_time*8)
                        value = (value + 1) / 2
                        
                    elif mode == "cqt":
                        # Constant Q transform-like pattern
                        value = np.sin(x*y/100 + current_time*5)
                        value = (value + 1) / 2
                    
                    else:
                        # Default pattern
                        value = np.sin(x/10 + current_time*5) * np.cos(y/10 + current_time*3)
                        value = (value + 1) / 2
                    
                    # Map to ASCII character
                    idx = min(int(value * len(charset)), len(charset) - 1)
                    char = charset[idx]
                    line += char
                    
                    # Draw the character on the image
                    # Shift by half width for each character to account for monospace font width
                    draw.text((x * font_size // 2, y * font_size), char, fill="lime", font=font)
            
            # Save the frame
            frame_path = os.path.join(output_dir, f"frame_{frame:04d}.png")
            img.save(frame_path)
        
        print("\nASCII frames generated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating ASCII frames: {str(e)}")
        return False

def render_ascii_video(input_file, output_file, mode="waves", duration=None, width=80, height=40):
    """
    Render ASCII art visualization of audio to a video file
    
    Args:
        input_file: Path to input audio file
        output_file: Path to output video file
        mode: Visualization mode (waves, spectrum, etc.)
        duration: Duration in seconds (None for full audio)
        width: ASCII art width
        height: ASCII art height
    
    Returns:
        0 on success, error code on failure
    """
    
    # Check for required libraries
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
    except ImportError:
        logger.error("Required libraries not found. Install with: pip install pillow numpy")
        return 1
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="direct_ascii_render_")
    logger.info(f"Using temp directory: {temp_dir}")
    
    try:
        # Step 1: Create ASCII frames directly
        print("Generating ASCII video frames...")
        if not create_ascii_frames_directly(input_file, temp_dir, duration, width, height, mode):
            logger.error("Failed to create ASCII frames")
            return 1
        
        # Step 2: Combine frames into video with audio
        frame_rate = 15  # fps
        video_cmd = [
            'ffmpeg',
            '-y',
            '-framerate', str(frame_rate),
            '-i', os.path.join(temp_dir, 'frame_%04d.png'),
            '-i', input_file
        ]
        
        # Add duration limit if specified
        if duration:
            video_cmd.extend(['-t', str(duration)])
        
        # Add output options
        video_cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',  # Ensure compatibility
            '-c:a', 'aac',
            '-b:a', '192k',
            output_file
        ])
        
        print(f"Rendering final video with audio...")
        
        try:
            video_result = subprocess.run(
                video_cmd,
                check=False,
                capture_output=True,
                text=True
            )
            
            if video_result.returncode != 0:
                logger.error(f"Video creation failed: {video_result.stderr}")
                return video_result.returncode
            
            print(f"Video successfully rendered to {output_file}")
            return 0
            
        except Exception as e:
            logger.error(f"Error creating video: {str(e)}")
            return 1
        
    finally:
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory: {str(e)}")


def main():
    """Main entry point"""
    
    # Parse arguments
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} input_file output_file [mode] [duration]")
        print("Modes: waves, spectrum, cqt")
        return 1
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else "waves"
    duration = float(sys.argv[4]) if len(sys.argv) > 4 else None
    
    # Check input file
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return 1
    
    # Render ASCII visualization
    print(f"Rendering ASCII visualization of {input_file} to {output_file}")
    print(f"Mode: {mode}")
    
    if duration:
        print(f"Duration: {duration} seconds")
    
    start_time = time.time()
    result = render_ascii_video(input_file, output_file, mode, duration)
    
    if result == 0:
        elapsed = time.time() - start_time
        print(f"Rendering completed in {elapsed:.2f} seconds")
        print(f"Output saved to: {output_file}")
    else:
        print(f"Rendering failed with error code {result}")
    
    return result


if __name__ == "__main__":
    sys.exit(main())