#!/usr/bin/env python3
"""
ASCII Art Audio Visualizer
--------------------------
A Python script that creates innovative ASCII art visualizations for audio files 
using FFmpeg and libcaca library with intelligent mode selection and processing.

Requirements:
- FFmpeg with libcaca support
- Python 3.6+
- ffmpeg-python
- numpy
- scipy
"""

import argparse
import ffmpeg
import numpy as np
import os
import subprocess
import sys
import tempfile
import time
from scipy import signal

class ASCIIAudioVisualizer:
    """Main class for ASCII art audio visualization"""
    
    def __init__(self, input_file, output_dir="./output", 
                 width=80, height=40, fps=15, duration=None,
                 mode="auto", temp_dir=None):
        """Initialize the visualizer with configuration parameters
        
        Args:
            input_file (str): Path to the input audio file
            output_dir (str): Directory to save output files
            width (int): Width of the ASCII visualization in characters
            height (int): Height of the ASCII visualization in characters
            fps (int): Frames per second for the visualization
            duration (int): Duration to process in seconds (None for full file)
            mode (str): Visualization mode (auto, waves, spectrum, cqt, combined, reactive)
            temp_dir (str): Directory for temporary files
        """
        self.input_file = input_file
        self.output_dir = output_dir
        self.width = width
        self.height = height
        self.fps = fps
        self.duration = duration
        self.mode = mode
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename based on input
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        self.output_base = os.path.join(output_dir, f"{base_name}")
        
        # Validate input file existence
        if not os.path.isfile(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")

    def analyze_audio(self):
        """Analyze audio file to determine optimal visualization parameters
        
        Returns:
            dict: Analysis results with audio characteristics
        """
        print("Analyzing audio file...")
        
        # Extract audio data using FFmpeg
        try:
            # Get audio to float32 numpy array
            out, _ = (ffmpeg
                .input(self.input_file)
                .output('pipe:', 
                       format='f32le',
                       acodec='pcm_f32le',
                       ac=2,
                       ar=44100)
                .run(capture_stdout=True, capture_stderr=True))
            
            # Convert to numpy array
            audio_data = np.frombuffer(out, np.float32)
            
            # Reshape if stereo (2 channels)
            if len(audio_data) % 2 == 0:
                audio_data = audio_data.reshape(-1, 2)
                # Convert to mono by averaging channels for analysis
                audio_data = np.mean(audio_data, axis=1)
            
            # Calculate basic audio features
            duration = len(audio_data) / 44100
            rms = np.sqrt(np.mean(audio_data**2))
            peak = np.max(np.abs(audio_data))
            crest_factor = peak / rms if rms > 0 else 0
            
            # Calculate spectral centroid (brightness)
            if len(audio_data) > 2048:
                # Use a window size of 2048 samples
                window_size = 2048
                hann_window = np.hanning(window_size)
                num_windows = len(audio_data) // (window_size // 2) - 1
                spectral_centroids = []
                
                for i in range(num_windows):
                    start = i * (window_size // 2)
                    end = start + window_size
                    if end <= len(audio_data):
                        windowed = audio_data[start:end] * hann_window
                        spectrum = np.abs(np.fft.rfft(windowed))
                        freqs = np.fft.rfftfreq(window_size, 1/44100)
                        if np.sum(spectrum) > 0:
                            centroid = np.sum(freqs * spectrum) / np.sum(spectrum)
                            spectral_centroids.append(centroid)
                
                avg_centroid = np.mean(spectral_centroids) if spectral_centroids else 0
            else:
                avg_centroid = 0
            
            # Calculate rhythm features
            if len(audio_data) > 44100:  # At least 1 second of audio
                # Calculate tempo using onset detection
                # Simplistic approach: find peaks in the energy envelope
                frame_size = 1024
                hop_size = 512
                energy = []
                
                for i in range(0, len(audio_data) - frame_size, hop_size):
                    frame = audio_data[i:i+frame_size]
                    energy.append(np.sum(frame**2))
                
                # Calculate onset strength
                energy = np.array(energy)
                diff = np.diff(energy)
                diff[diff < 0] = 0  # Keep only increases in energy
                
                # Find peaks
                peaks, _ = signal.find_peaks(diff, height=np.mean(diff) + 0.5 * np.std(diff), 
                                          distance=5)
                
                # Estimate BPM
                if len(peaks) > 1:
                    avg_peak_distance = np.mean(np.diff(peaks))
                    tempo_estimate = 60 / (avg_peak_distance * hop_size / 44100)
                    # Adjust to reasonable BPM range
                    while tempo_estimate < 60:
                        tempo_estimate *= 2
                    while tempo_estimate > 180:
                        tempo_estimate /= 2
                else:
                    tempo_estimate = 120  # Default assumption
            else:
                tempo_estimate = 120
            
            # Calculate spectral flatness (noise vs. tone)
            if len(audio_data) > 2048:
                spectrum = np.abs(np.fft.rfft(audio_data[:min(len(audio_data), 44100)]))
                geometric_mean = np.exp(np.mean(np.log(spectrum + 1e-10)))
                arithmetic_mean = np.mean(spectrum)
                spectral_flatness = geometric_mean / arithmetic_mean if arithmetic_mean > 0 else 0
            else:
                spectral_flatness = 0
                
            return {
                "duration": duration,
                "rms": float(rms),
                "peak": float(peak),
                "crest_factor": float(crest_factor),
                "spectral_centroid": float(avg_centroid),
                "tempo": float(tempo_estimate),
                "spectral_flatness": float(spectral_flatness)
            }
            
        except ffmpeg.Error as e:
            print(f"FFmpeg error during analysis: {e.stderr.decode('utf8')}")
            # Return default values
            return {
                "duration": 0,
                "rms": 0,
                "peak": 0,
                "crest_factor": 0,
                "spectral_centroid": 0,
                "tempo": 120,
                "spectral_flatness": 0
            }

    def determine_optimal_mode(self, analysis):
        """Determine the optimal visualization mode based on audio analysis
        
        Args:
            analysis (dict): Audio analysis results
            
        Returns:
            str: Optimal visualization mode
        """
        # If user specified a mode other than auto, use that
        if self.mode != "auto":
            return self.mode
        
        print("Determining optimal visualization mode...")
        
        # Extract key features
        spectral_centroid = analysis.get("spectral_centroid", 0)
        crest_factor = analysis.get("crest_factor", 0)
        tempo = analysis.get("tempo", 120)
        spectral_flatness = analysis.get("spectral_flatness", 0)
        
        # Decision logic based on audio characteristics
        if spectral_flatness > 0.2:
            # More noise-like content - use waveform
            print("Audio is noise-like, using waveform visualization")
            return "waves"
        elif spectral_centroid > 5000:
            # Bright/high-frequency content - use spectrum
            print("Audio is bright/high-frequency, using spectrum visualization")
            return "spectrum"
        elif tempo > 130:
            # Fast tempo - use reactive
            print("Audio has fast tempo, using reactive visualization")
            return "reactive"
        elif spectral_centroid < 2000 and crest_factor < 5:
            # Low frequency and steady - use CQT
            print("Audio is low-frequency and steady, using CQT visualization")
            return "cqt"
        else:
            # Default to combined
            print("Using combined visualization mode")
            return "combined"

    def get_character_set(self, mode):
        """Determine the optimal character set based on visualization mode
        
        Args:
            mode (str): Visualization mode
            
        Returns:
            str: Character set name
        """
        if mode in ["waves", "spectrum"]:
            return "ascii"  # Simpler visual, simpler charset
        else:
            return "blocks"  # More detail for complex visuals

    def get_color_mode(self, mode):
        """Determine the optimal color mode based on visualization mode
        
        Args:
            mode (str): Visualization mode
            
        Returns:
            str: Color mode
        """
        if mode == "reactive":
            return "full16"  # Full color for reactive mode
        elif mode == "waves":
            return "mono"  # Monochrome for waves
        else:
            return "full16"  # Default to full color

    def create_visualization(self, mode, analysis):
        """Create the ASCII art visualization based on the selected mode
        
        Args:
            mode (str): Visualization mode
            analysis (dict): Audio analysis results
            
        Returns:
            bool: Success status
        """
        # Prepare output file paths
        ascii_file = f"{self.output_base}_{mode}.txt"
        html_file = f"{self.output_base}_{mode}.html"
        
        # Set parameters based on audio analysis
        charset = self.get_character_set(mode)
        color_mode = self.get_color_mode(mode)
        
        # Build filter complex string based on mode
        filter_complex = ""
        if mode == "waves":
            wave_mode = "line" if analysis.get("crest_factor", 0) < 10 else "p2p"
            colors = "0x000000|0xFFFFFF" if color_mode == "mono" else "white"
            filter_complex = f"showwaves=s={self.width*8}x{self.height*16}:mode={wave_mode}:colors={colors},format=rgb24"
        
        elif mode == "spectrum":
            scale = "log" if analysis.get("spectral_centroid", 0) < 4000 else "lin"
            slide_mode = "scroll" if analysis.get("duration", 0) > 30 else "replace"
            filter_complex = f"showspectrum=s={self.width*8}x{self.height*16}:mode=combined:slide={slide_mode}:scale={scale},format=rgb24"
        
        elif mode == "cqt":
            # Adjust count based on spectral complexity
            count = int(3 + min(5, analysis.get("spectral_flatness", 0) * 10))
            gamma = min(7, max(3, int(analysis.get("crest_factor", 5))))
            filter_complex = f"showcqt=s={self.width*8}x{self.height*16}:count={count}:gamma={gamma},format=rgb24"
        
        elif mode == "combined":
            # Adjust heights for the two visualizations
            upper_height = int(self.height * 12)
            lower_height = int(self.height * 4)
            
            filter_complex = f"""
            [0:a]showspectrum=s={self.width*8}x{upper_height}:mode=combined:scale=log[spectrum];
            [0:a]showwaves=s={self.width*8}x{lower_height}:mode=line:colors=white[waves];
            [spectrum][waves]vstack,format=rgb24
            """
        
        elif mode == "reactive":
            # Reactive visualization with color effects based on tempo
            hue_speed = analysis.get("tempo", 120) / 20
            count = min(8, max(3, int(analysis.get("tempo", 120) / 20)))
            
            filter_complex = f"""
            showcqt=s={self.width*8}x{self.height*16}:count={count},
            hue=h=t*{hue_speed}:s=t+1,format=rgb24
            """
        
        else:
            print(f"Unknown mode: {mode}")
            return False
        
        # Build the FFmpeg command
        try:
            # Use duration parameter if specified
            input_params = {}
            if self.duration is not None:
                input_params['t'] = str(self.duration)
            
            # Create ASCII text output
            print(f"Generating {mode} ASCII visualization to {ascii_file}...")
            
            # Create command for text output
            (ffmpeg
                .input(self.input_file, **input_params)
                .filter_complex(filter_complex)
                .output(ascii_file, 
                        f='caca', 
                        window_size=f"{self.width}x{self.height}",
                        charset=charset,
                        algorithm='fstein',
                        color=color_mode)
                .overwrite_output()
                .run())
            
            # Create HTML output
            print(f"Generating {mode} HTML visualization to {html_file}...")
            
            # Create command for HTML output
            (ffmpeg
                .input(self.input_file, **input_params)
                .filter_complex(filter_complex)
                .output(html_file, 
                        f='caca',
                        window_size=f"{self.width}x{self.height}",
                        charset=charset,
                        algorithm='fstein',
                        color=color_mode)
                .overwrite_output()
                .run())
            
            return True
            
        except ffmpeg.Error as e:
            print(f"FFmpeg error: {e.stderr.decode('utf8')}")
            return False

    def create_multi_mode_visualization(self, analysis):
        """Create multiple visualization modes and combine them
        
        Args:
            analysis (dict): Audio analysis results
            
        Returns:
            bool: Success status
        """
        # Create a multi-mode output combining all visualization types
        multi_file = f"{self.output_base}_multi.html"
        
        try:
            # Determine parameters based on audio characteristics
            tempo = analysis.get("tempo", 120)
            spectral_centroid = analysis.get("spectral_centroid", 0)
            
            # Adjust visualization parameters based on audio features
            cqt_count = min(8, max(3, int(tempo / 20)))
            wave_mode = "line" if analysis.get("crest_factor", 0) < 10 else "p2p"
            spectrum_scale = "log" if spectral_centroid < 4000 else "lin"
            
            # Calculate dimensions for quad layout
            quad_width = self.width * 4  # Half width
            quad_height = self.height * 8  # Half height
            
            print(f"Generating multi-mode visualization to {multi_file}...")
            
            # Use duration parameter if specified
            input_params = {}
            if self.duration is not None:
                input_params['t'] = str(self.duration)
            
            # Create four different visualizations and combine them in a 2x2 grid
            (ffmpeg
                .input(self.input_file, **input_params)
                .filter_complex(f"""
                [0:a]showcqt=s={quad_width}x{quad_height}:count={cqt_count}[cqt];
                [0:a]showspectrum=s={quad_width}x{quad_height}:mode=combined:scale={spectrum_scale}[spectrum];
                [0:a]showwaves=s={quad_width}x{quad_height}:mode={wave_mode}:colors=white[waves];
                [0:a]avectorscope=s={quad_width}x{quad_height}:zoom=1.5:draw=line[scope];
                [cqt][spectrum]hstack[top];
                [waves][scope]hstack[bottom];
                [top][bottom]vstack,format=rgb24
                """)
                .output(multi_file, 
                        f='caca',
                        window_size=f"{self.width}x{self.height}",
                        charset="blocks",
                        algorithm='fstein',
                        color="full16")
                .overwrite_output()
                .run())
            
            return True
            
        except ffmpeg.Error as e:
            print(f"FFmpeg error: {e.stderr.decode('utf8')}")
            return False

    def create_realtime_preview(self, mode, analysis):
        """Create a real-time preview of the ASCII visualization
        
        Args:
            mode (str): Visualization mode
            analysis (dict): Audio analysis results
            
        Returns:
            bool: Success status
        """
        print(f"Starting real-time {mode} preview...")
        
        # Build filter complex string based on mode
        filter_complex = ""
        
        # Set parameters based on audio analysis
        charset = self.get_character_set(mode)
        color_mode = self.get_color_mode(mode)
        
        if mode == "waves":
            wave_mode = "line" if analysis.get("crest_factor", 0) < 10 else "p2p"
            colors = "0x000000|0xFFFFFF" if color_mode == "mono" else "white"
            filter_complex = f"showwaves=s={self.width*8}x{self.height*16}:mode={wave_mode}:colors={colors},format=rgb24"
        
        elif mode == "spectrum":
            scale = "log" if analysis.get("spectral_centroid", 0) < 4000 else "lin"
            filter_complex = f"showspectrum=s={self.width*8}x{self.height*16}:mode=combined:slide=scroll:scale={scale},format=rgb24"
        
        elif mode == "cqt":
            count = int(3 + min(5, analysis.get("spectral_flatness", 0) * 10))
            gamma = min(7, max(3, int(analysis.get("crest_factor", 5))))
            filter_complex = f"showcqt=s={self.width*8}x{self.height*16}:count={count}:gamma={gamma},format=rgb24"
        
        elif mode == "combined":
            upper_height = int(self.height * 12)
            lower_height = int(self.height * 4)
            
            filter_complex = f"""
            [0:a]showspectrum=s={self.width*8}x{upper_height}:mode=combined:scale=log[spectrum];
            [0:a]showwaves=s={self.width*8}x{lower_height}:mode=line:colors=white[waves];
            [spectrum][waves]vstack,format=rgb24
            """
        
        elif mode == "reactive":
            hue_speed = analysis.get("tempo", 120) / 20
            count = min(8, max(3, int(analysis.get("tempo", 120) / 20)))
            
            filter_complex = f"""
            showcqt=s={self.width*8}x{self.height*16}:count={count},
            hue=h=t*{hue_speed}:s=t+1,format=rgb24
            """
        
        else:
            print(f"Unknown mode: {mode}")
            return False
        
        # Build the FFmpeg command for real-time playback
        try:
            # Use duration parameter if specified
            input_params = {}
            if self.duration is not None:
                input_params['t'] = str(self.duration)
            
            # Build the command string
            cmd = [
                "ffplay", "-nostats", "-autoexit",
                "-i", self.input_file
            ]
            
            # Add duration if specified
            if self.duration is not None:
                cmd.extend(["-t", str(self.duration)])
            
            # Add filter complex and output options
            cmd.extend([
                "-filter_complex", filter_complex,
                "-f", "caca",
                "-window_size", f"{self.width}x{self.height}",
                "-charset", charset,
                "-algorithm", "fstein",
                "-color", color_mode
            ])
            
            # Run the command
            subprocess.run(cmd)
            
            return True
            
        except subprocess.SubprocessError as e:
            print(f"Error during real-time preview: {str(e)}")
            return False

    def run(self, preview=False, multi=False):
        """Run the visualization process
        
        Args:
            preview (bool): Whether to show a real-time preview
            multi (bool): Whether to create a multi-mode visualization
            
        Returns:
            bool: Success status
        """
        try:
            # Analyze the audio file
            analysis = self.analyze_audio()
            
            # Print analysis results
            print("\nAudio Analysis Results:")
            print(f"Duration: {analysis.get('duration', 0):.2f} seconds")
            print(f"RMS Level: {analysis.get('rms', 0):.4f}")
            print(f"Peak Level: {analysis.get('peak', 0):.4f}")
            print(f"Crest Factor: {analysis.get('crest_factor', 0):.2f}")
            print(f"Spectral Centroid: {analysis.get('spectral_centroid', 0):.2f} Hz")
            print(f"Estimated Tempo: {analysis.get('tempo', 0):.2f} BPM")
            print(f"Spectral Flatness: {analysis.get('spectral_flatness', 0):.4f}\n")
            
            # Determine the optimal visualization mode
            if self.mode == "auto":
                self.mode = self.determine_optimal_mode(analysis)
            
            print(f"Selected visualization mode: {self.mode}")
            
            # If multi-mode is requested, create all visualizations
            if multi:
                success = self.create_multi_mode_visualization(analysis)
                if not success:
                    print("Failed to create multi-mode visualization")
                    return False
            
            # If preview is requested, show real-time preview
            if preview:
                success = self.create_realtime_preview(self.mode, analysis)
                if not success:
                    print("Failed to create real-time preview")
                    return False
            else:
                # Otherwise create the selected visualization
                success = self.create_visualization(self.mode, analysis)
                if not success:
                    print("Failed to create visualization")
                    return False
            
            print("Visualization completed successfully!")
            return True
            
        except Exception as e:
            print(f"Error during visualization: {str(e)}")
            return False


def main():
    """Main function to parse arguments and run the visualizer"""
    parser = argparse.ArgumentParser(
        description="ASCII Art Audio Visualizer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("input_file", help="Input audio file path")
    
    parser.add_argument(
        "--output-dir", "-o",
        default="./output",
        help="Output directory for generated files"
    )
    
    parser.add_argument(
        "--width", "-W",
        type=int, default=80,
        help="Width of the ASCII visualization in characters"
    )
    
    parser.add_argument(
        "--height", "-H",
        type=int, default=40,
        help="Height of the ASCII visualization in characters"
    )
    
    parser.add_argument(
        "--fps", "-f",
        type=int, default=15,
        help="Frames per second for the visualization"
    )
    
    parser.add_argument(
        "--duration", "-d",
        type=float, default=None,
        help="Duration to process in seconds (default: full file)"
    )
    
    parser.add_argument(
        "--mode", "-m",
        choices=["auto", "waves", "spectrum", "cqt", "combined", "reactive"],
        default="auto",
        help="Visualization mode (auto selects based on audio analysis)"
    )
    
    parser.add_argument(
        "--temp-dir", "-t",
        default=None,
        help="Directory for temporary files (default: system temp dir)"
    )
    
    parser.add_argument(
        "--preview", "-p",
        action="store_true",
        help="Show real-time preview instead of saving files"
    )
    
    parser.add_argument(
        "--multi", "-M",
        action="store_true",
        help="Create multi-mode visualization with all modes"
    )
    
    args = parser.parse_args()
    
    # Create and run the visualizer
    visualizer = ASCIIAudioVisualizer(
        input_file=args.input_file,
        output_dir=args.output_dir,
        width=args.width,
        height=args.height,
        fps=args.fps,
        duration=args.duration,
        mode=args.mode,
        temp_dir=args.temp_dir
    )
    
    success = visualizer.run(preview=args.preview, multi=args.multi)
    
    # Return exit code based on success
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
