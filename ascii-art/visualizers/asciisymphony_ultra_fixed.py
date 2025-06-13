"""
AsciiSymphony Pro: Enterprise-Grade ASCII Art Audio Visualizer
Python Implementation v3.0.0

This Python implementation provides all the functionality of the original
AsciiSymphony Pro Bash script with improved structure, error handling,
and extensibility.

Features:
- GPU-accelerated rendering
- Real-time audio input processing
- Advanced visualization modes
- User preset management system
- Adaptive quality control
- Intelligent error recovery
- Cross-platform support
"""

import argparse
import base64
import datetime
import fcntl
import json
import logging
import os
import platform
import queue
import re
import shlex
import struct
import subprocess
import sys
import tempfile
import termios
import threading
import time
import wave
from contextlib import contextmanager
from enum import Enum, auto
from pathlib import Path

# Handle NumPy import compatibility with Python 3.12
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError as e:
    NUMPY_AVAILABLE = False
    print("Warning: NumPy import failed. This may be due to compatibility issues with Python 3.12.")
    print("Consider upgrading NumPy with: pip install numpy --upgrade")
    print("Error details:", e)
    print("Falling back to basic functionality without NumPy.\n")

    # Create a minimal numpy-like array implementation for basic functionality
    class NumpyArrayFallback:
        def __init__(self, data, dtype=None):
            self.data = data
            self.dtype = dtype
            
        def __len__(self):
            return len(self.data)

    # Create a minimal numpy module fallback
    class NumpyFallback:
        def frombuffer(self, buffer, dtype=None):
            # Convert bytes to a list of integers when NumPy is not available
            if dtype == 'int16':
                # Unpack 16-bit integers from buffer
                import array
                return NumpyArrayFallback(array.array('h', buffer))
            return NumpyArrayFallback(list(buffer))
        
    # Use fallback if NumPy is not available
    if not NUMPY_AVAILABLE:
        np = NumpyFallback()

# Check PyAudio availability
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("Warning: PyAudio import failed. Live audio processing will not be available.")
    print("Install PyAudio with: pip install pyaudio")
    print("On Ubuntu/Debian, you may need: sudo apt-get install python3-pyaudio\n")

# =============================================================================
# CONFIGURATION
# =============================================================================
class Config:
    """Configuration management class."""
    def __init__(self):
        # Default settings
        self.settings = {
            'fps': 30,
            'width': 1280,
            'height': 720,
            'quality': 'balanced',
            'mode': 'waves',
            'charset': 'ascii',  # Changed from unicode to ascii for better compatibility
            'dither': 'fstein',
            'colors': 'thermal',
            'threads': os.cpu_count() // 2 if os.cpu_count() else 2,
            'gpu': 'auto',
            'latency': 'normal',
            'buffer_size': 1024,
            'sample_rate': 44100,
            'channels': 2,
            'renderer': 'file'
        }

    def get(self, key, default=None):
        """Get a configuration value."""
        return self.settings.get(key, default)

    def update(self, settings):
        """Update configuration with new settings."""
        self.settings.update(settings)

# =============================================================================
# LOGGING
# =============================================================================
def setup_logging(debug=False):
    """Set up logging for the application."""
    log_dir = Path(os.environ.get('TMPDIR', '/tmp')) / "asciisymphony"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "asymphony.log"

    log_level = logging.DEBUG if debug else logging.INFO

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler(log_file)
        ]
    )

    return logging.getLogger("asciisymphony")

# =============================================================================
# ERROR HANDLING
# =============================================================================
class ErrorClass(Enum):
    """Error classification based on the Core Architecture Model."""
    TECHNICAL = auto()  # T-Class errors
    CREATIVE = auto()   # C-Class errors
    HYBRID = auto()     # H-Class errors

class ErrorHandler:
    """Handles errors and implements fallback mechanisms."""
    def __init__(self, app):
        self.app = app
        self.logger = app.logger
        self.config = app.config
        self.fallback_attempts = 0
        self.max_fallback_attempts = 3

    def handle_error(self, error, error_class=ErrorClass.TECHNICAL):
        """Handle an error with appropriate fallback."""
        self.logger.error(f"Error encountered: {str(error)}")
        
        if self.fallback_attempts >= self.max_fallback_attempts:
            self.logger.critical("Maximum fallback attempts reached, giving up")
            raise error
        
        self.fallback_attempts += 1
        
        # Handle different error classes
        if error_class == ErrorClass.TECHNICAL:
            return self._handle_technical_error(error)
        elif error_class == ErrorClass.CREATIVE:
            return self._handle_creative_error(error)
        else:  # HYBRID
            return self._handle_hybrid_error(error)

    def _handle_technical_error(self, error):
        """Handle technical errors (T-Class)."""
        self.logger.info("Handling technical error with T-Mitigation")
        
        # Check error type and apply appropriate fallback
        if "GPU" in str(error) or "hardware" in str(error).lower():
            # Disable GPU acceleration
            self.logger.info("Disabling GPU acceleration")
            self.config.update({"gpu": 0})
            return True
        
        elif "memory" in str(error).lower():
            # Reduce quality
            quality = self.config.get("quality", "balanced")
            if quality == "ultra":
                new_quality = "high"
            elif quality == "high":
                new_quality = "balanced"
            else:
                new_quality = "low"
            
            self.logger.info(f"Reducing quality from {quality} to {new_quality}")
            self.config.update({"quality": new_quality})
            return True
        
        elif "filter" in str(error).lower():
            # Fall back to simpler visualization mode
            current_mode = self.config.get("mode", "waves")
            fallback_modes = {
                "neural": "spectrum",
                "typography": "waves",
                "particles": "waves",
                "fractal": "cqt",
                "spectrosynth": "spectrum",
                "vortex": "waves",
                "kaleidoscope": "spectrum"
            }
            
            new_mode = fallback_modes.get(current_mode, "waves")
            self.logger.info(f"Falling back from {current_mode} to {new_mode}")
            self.config.update({"mode": new_mode})
            return True
        
        # No specific fallback found
        return False

    def _handle_creative_error(self, error):
        """Handle creative errors (C-Class)."""
        self.logger.info("Handling creative error with C-Revision")
        
        # Typically these are errors related to styling or aesthetic issues
        if "color" in str(error).lower():
            # Reset to default color scheme
            self.logger.info("Resetting to default color scheme")
            self.config.update({"colors": "thermal"})
            return True
        
        elif "effect" in str(error).lower():
            # Disable effects
            self.logger.info("Disabling effects")
            self.config.update({"effects": "none"})
            return True
        
        # No specific fallback found
        return False

    def _handle_hybrid_error(self, error):
        """Handle hybrid errors (H-Class)."""
        self.logger.info("Handling hybrid error with Cross-Domain Review")
        
        # These are more complex errors that might require multiple changes
        # First try technical fallback
        if self._handle_technical_error(error):
            return True
        
        # Then try creative fallback
        if self._handle_creative_error(error):
            return True
        
        # If all else fails, reset to most basic configuration
        self.logger.info("Resetting to basic configuration")
        basic_config = {
            "mode": "waves",
            "quality": "low",
            "fps": 15,
            "gpu": 0,
            "effects": "none",
            "charset": "ascii"
        }
        self.config.update(basic_config)
        return True

    def check_ffmpeg_capabilities(self):
        """Check FFmpeg capabilities and set fallback paths if needed."""
        # Check for libcaca support using -formats instead of -filters
        try:
            format_info = subprocess.run(
                ["ffmpeg", "-formats"],
                capture_output=True,
                text=True,
                timeout=3
            )
            # Set defaults directly if command fails
            if format_info.returncode != 0:
                raise subprocess.SubprocessError("FFmpeg formats command failed")
        except Exception as e:
            self.logger.warning(f"FFmpeg format check failed: {str(e)}")
            format_info = type('obj', (object,), {'stdout': '', 'returncode': 1})
            
        try:
            # Check if FFmpeg is installed
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            # Check for libcaca support
            result = subprocess.run(
                ["ffmpeg", "-filters"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            if "caca" not in result.stdout:
                self.logger.warning("FFmpeg does not have libcaca support, ASCII output may be limited")
            
            # Check for GPU acceleration support
            result = subprocess.run(
                ["ffmpeg", "-hwaccels"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            # Update config based on available hardware acceleration
            if "vulkan" in result.stdout:
                self.logger.info("Vulkan hardware acceleration available")
                self.config.update({"vulkan": 1})
            else:
                self.config.update({"vulkan": 0})
            
            # Check for libplacebo support
            result = subprocess.run(
                ["ffmpeg", "-v", "quiet", "-filters"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            if "libplacebo" in result.stdout:
                self.logger.info("libplacebo GPU processing available")
                self.config.update({"gpu": 1})
            else:
                self.config.update({"gpu": 0})
            
            return True
            
        except (subprocess.SubprocessError) as e:
            self.logger.error(f"Error checking FFmpeg capabilities: {str(e)}")
            # Assume minimal capabilities
            self.config.update({"vulkan": 0, "gpu": 0})
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error checking FFmpeg: {str(e)}")
            return False

# =============================================================================
# AUDIO DEVICE MANAGEMENT
# =============================================================================
class AudioDeviceManager:
    """Manages audio device detection and selection across platforms."""
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("asciisymphony.audio")
        self.devices = []
        
        # Check if audio device management is available
        if not PYAUDIO_AVAILABLE:
            self.logger.warning("PyAudio is not available. Audio device detection is limited.")
            self.system = "unavailable"
        else:
            self.system = self._detect_system()

    def _detect_system(self):
        """Detect the audio system to use based on platform."""
        system = platform.system()
        
        if system == "Linux":
            # Check for PulseAudio/PipeWire
            if self._command_exists("pactl"):
                return "pulse"
            # Check for ALSA
            elif self._command_exists("arecord"):
                return "alsa"
            
        elif system == "Darwin":  # macOS
            return "avfoundation"
            
        elif system == "Windows":
            return "dshow"
        
        # Default fallback
        return "default"

    def _command_exists(self, cmd):
        """Check if a command exists in the system path."""
        try:
            subprocess.run(
                ["which", cmd], 
                capture_output=True, 
                check=True
            )
            return True
        except subprocess.SubprocessError:
            return False

    def detect_devices(self):
        """Detect available audio input devices."""
        self.logger.info(f"Detecting audio input devices on {self.system}")
        self.devices = []
        
        # Check if PyAudio is available
        if not PYAUDIO_AVAILABLE:
            self.logger.warning("PyAudio is not available. Using fallback device.")
            # Add a fallback default device
            self.devices.append({
                'index': 0,
                'name': 'Default Audio Device (PyAudio not available)',
                'channels': 2,
                'sample_rate': 44100,
                'system': 'fallback'
            })
            return self.devices
            
        # Use PyAudio for more reliable cross-platform device detection
        pa = pyaudio.PyAudio()
        
        try:
            device_count = pa.get_device_count()
            
            for i in range(device_count):
                device_info = pa.get_device_info_by_index(i)
                
                # Only include input devices
                if device_info.get('maxInputChannels') > 0:
                    self.devices.append({
                        'index': i,
                        'name': device_info.get('name'),
                        'channels': device_info.get('maxInputChannels'),
                        'sample_rate': int(device_info.get('defaultSampleRate')),
                        'system': self.system
                    })
        finally:
            pa.terminate()
        
        self.logger.info(f"Found {len(self.devices)} audio input devices")
        
        return self.devices

    def get_device_by_id(self, device_id):
        """Get device information by ID."""
        if not self.devices:
            self.detect_devices()
        
        # If device_id is None, return the default device
        if device_id is None:
            # Return the first device or None if no devices
            return self.devices[0] if self.devices else None
        
        # If device_id is an integer, use it as an index
        if isinstance(device_id, int):
            for device in self.devices:
                if device['index'] == device_id:
                    return device
        
        # If device_id is a string, try to match by name
        elif isinstance(device_id, str):
            for device in self.devices:
                if device_id in device['name']:
                    return device
        
        # No matching device found
        raise ValueError(f"Device not found: {device_id}")

    def list_devices(self):
        """List all available audio input devices."""
        if not self.devices:
            self.detect_devices()
        
        return [(device['index'], device['name']) for device in self.devices]

    def get_ffmpeg_input_args(self, device_id=None):
        """Get FFmpeg input arguments for live audio capture."""
        device = self.get_device_by_id(device_id)
        
        if not device:
            raise ValueError("No audio input device available")
        
        # Get configuration
        sample_rate = self.config.get('sample_rate', device['sample_rate'])
        channels = self.config.get('channels', min(device['channels'], 2))
        buffer_size = self.config.get('buffer_size', 1024)
        latency = self.config.get('latency', 'normal')
        
        # Base arguments
        args = []
        
        # System-specific arguments
        system = platform.system()
        
        if system == "Linux":
            if device['system'] == 'pulse':
                args.extend(['-f', 'pulse', '-i', str(device['index'])])
            else:
                # Use ALSA for non-PulseAudio devices
                args.extend(['-f', 'alsa', '-i', f"hw:{device['index']}"])
        elif system == "Darwin":  # macOS
            args.extend(['-f', 'avfoundation', '-i', f":{device['index']}"])
        elif system == "Windows":
            args.extend(['-f', 'dshow', '-audio_buffer_size', str(buffer_size), 
                        '-i', f"audio={device['name']}"])
        else:
            # Generic fallback
            args.extend(['-f', 'pulse', '-i', str(device['index'])])
        
        # Common arguments
        args.extend(['-sample_rate', str(sample_rate), '-channels', str(channels)])
        
        # Low latency options
        if latency == 'low':
            args.extend(['-avioflags', 'direct', '-fflags', 'nobuffer',
                         '-flags', 'low_delay', '-strict', 'experimental'])
        
        return args

class LiveAudioProcessor:
    """Processes live audio input for visualization."""
    def __init__(self, config, device_manager):
        self.config = config
        self.device_manager = device_manager
        self.logger = logging.getLogger("asciisymphony.audio")
        self.audio_queue = queue.Queue(maxsize=100)
        self.stop_event = threading.Event()
        self.audio_thread = None
        
        # Check if live audio processing is available
        if not PYAUDIO_AVAILABLE:
            self.logger.error("PyAudio is not available. Live audio processing is disabled.")
            raise ImportError("PyAudio is required for live audio processing")

    def start_capture(self, device_id=None):
        """Start capturing audio from the specified device."""
        device = self.device_manager.get_device_by_id(device_id)
        
        if not device:
            raise ValueError("No audio input device available")
        
        self.logger.info(f"Starting audio capture from device: {device['name']}")
        
        # Clear queue and reset stop event
        while not self.audio_queue.empty():
            self.audio_queue.get()
        
        self.stop_event.clear()
        
        # Start audio capture thread
        self.audio_thread = threading.Thread(
            target=self._audio_capture_thread,
            args=(device,),
            daemon=True
        )
        self.audio_thread.start()
        
        return self.audio_queue

    def stop_capture(self):
        """Stop audio capture."""
        if self.audio_thread and self.audio_thread.is_alive():
            self.stop_event.set()
            self.audio_thread.join(timeout=2.0)
            self.logger.info("Audio capture stopped")

    def _audio_capture_thread(self, device):
        """Audio capture thread function."""
        # Get configuration
        sample_rate = int(self.config.get('sample_rate', device['sample_rate']))
        channels = int(self.config.get('channels', min(device['channels'], 2)))
        buffer_size = int(self.config.get('buffer_size', 1024))
        
        # Initialize PyAudio
        pa = pyaudio.PyAudio()
        
        try:
            # Open audio stream
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                input=True,
                input_device_index=device['index'],
                frames_per_buffer=buffer_size
            )
            
            # Process audio
            while not self.stop_event.is_set():
                try:
                    audio_data = stream.read(buffer_size)
                    
                    # Convert to numpy array for easier processing
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    
                    # Put in queue if not full
                    if not self.audio_queue.full():
                        self.audio_queue.put(audio_array, block=False)
                    
                except (IOError, OSError) as e:
                    self.logger.error(f"Error reading audio: {str(e)}")
                    time.sleep(0.1)  # Prevent tight loop on error
        
        finally:
            # Clean up
            try:
                stream.stop_stream()
                stream.close()
            except:
                pass
            
            pa.terminate()

    def create_temp_wav(self, duration=5):
        """Create a temporary WAV file from live audio for FFmpeg processing."""
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_filename = temp_file.name
        temp_file.close()
        
        device_id = self.config.get('audio_device')
        device = self.device_manager.get_device_by_id(device_id)
        
        if not device:
            raise ValueError("No audio input device available")
        
        # Get configuration
        sample_rate = int(self.config.get('sample_rate', device['sample_rate']))
        channels = int(self.config.get('channels', min(device['channels'], 2)))
        buffer_size = int(self.config.get('buffer_size', 1024))
        
        # Initialize PyAudio
        pa = pyaudio.PyAudio()
        
        try:
            # Open audio stream
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                input=True,
                input_device_index=device['index'],
                frames_per_buffer=buffer_size
            )
            
            # Open WAV file
            wf = wave.open(temp_filename, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            
            # Record audio
            self.logger.info(f"Recording {duration} seconds of audio to {temp_filename}")
            
            frames = []
            for _ in range(0, int(sample_rate / buffer_size * duration)):
                data = stream.read(buffer_size)
                frames.append(data)
            
            # Write to file
            wf.writeframes(b''.join(frames))
            wf.close()
            
            # Clean up audio
            stream.stop_stream()
            stream.close()
            
            return temp_filename
            
        finally:
            pa.terminate()

# =============================================================================
# PRESET MANAGEMENT
# =============================================================================
class PresetManager:
    """Manages saving, loading, exporting, and importing presets."""
    PRESET_FORMAT_VERSION = "1.0"

    def __init__(self, config):
        self.config = config
        self.preset_dir = self._get_preset_dir()
        self._ensure_preset_dir()

    def _get_preset_dir(self):
        """Get the preset directory path."""
        home_dir = Path.home()
        return home_dir / ".asciisymphony" / "presets"

    def _ensure_preset_dir(self):
        """Ensure the preset directory exists."""
        if not self.preset_dir.exists():
            self.preset_dir.mkdir(parents=True)
            self._create_default_preset()

    def _create_default_preset(self):
        """Create a default preset."""
        default_preset = {
            "mode": "waves",
            "fps": 30,
            "quality": "balanced",
            "colors": "thermal",
            "charset": "ascii",
            "dither": "fstein",
            "hue": 1.5,
            "saturation": 1.2,
            "threads": os.cpu_count() // 2 if os.cpu_count() else 2,
            "gpu": "auto",
            "latency": "normal",
            "width": 1280,
            "height": 720
        }
        
        self._save_preset_file("default", default_preset)

    def _save_preset_file(self, name, preset_data):
        """Save a preset to a file."""
        preset_path = self.preset_dir / f"{name}.preset"
        
        # Add metadata
        preset_data["_meta"] = {
            "version": self.PRESET_FORMAT_VERSION,
            "created": datetime.datetime.now().isoformat(),
            "name": name
        }
        
        with open(preset_path, 'w') as f:
            json.dump(preset_data, f, indent=2)
        
        return preset_path

    def save_preset(self, name):
        """Save current configuration as a preset."""
        if not name:
            raise ValueError("No preset name provided")
        
        # Get current configuration
        preset_data = {k: v for k, v in self.config.settings.items()}
        
        # Save preset
        preset_path = self._save_preset_file(name, preset_data)
        
        return str(preset_path)

    def load_preset(self, name):
        """Load a preset and apply its settings."""
        if not name:
            raise ValueError("No preset name provided")
        
        # Add .preset extension if not present
        if not name.endswith(".preset"):
            name = f"{name}.preset"
        
        preset_path = self.preset_dir / name
        
        if not preset_path.exists():
            raise FileNotFoundError(f"Preset not found: {name}")
        
        # Load preset
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)
        
        # Remove metadata
        if "_meta" in preset_data:
            del preset_data["_meta"]
        
        # Update configuration
        self.config.update(preset_data)
        
        return preset_data

    def list_presets(self):
        """List all available presets."""
        presets = []
        
        for preset_file in self.preset_dir.glob("*.preset"):
            try:
                with open(preset_file, 'r') as f:
                    preset_data = json.load(f)
                
                meta = preset_data.get("_meta", {})
                preset_info = {
                    "name": preset_file.stem,
                    "path": str(preset_file),
                    "version": meta.get("version", "unknown"),
                    "created": meta.get("created", "unknown"),
                    "mode": preset_data.get("mode", "unknown")
                }
                presets.append(preset_info)
            except:
                # Skip invalid presets
                continue
        
        return presets

    def export_preset(self, name, export_path=None):
        """Export a preset to a shareable file."""
        if not name:
            raise ValueError("No preset name provided")
        
        # Add .preset extension if not present
        if not name.endswith(".preset"):
            name = f"{name}.preset"
        
        preset_path = self.preset_dir / name
        
        if not preset_path.exists():
            raise FileNotFoundError(f"Preset not found: {name}")
        
        # If no export path specified, use preset name
        if not export_path:
            export_path = f"{preset_path.stem}.aspreset"
        
        # Read preset file
        with open(preset_path, 'rb') as f:
            preset_data = f.read()
        
        # Encode preset data
        encoded_data = base64.b64encode(preset_data).decode('utf-8')
        
        # Create export file
        with open(export_path, 'w') as f:
            f.write(f"# AsciiSymphony Pro Portable Preset\n")
            f.write(f"# Version: {self.PRESET_FORMAT_VERSION}\n")
            f.write(f"# Original: {preset_path.stem}\n")
            f.write(f"# Exported: {datetime.datetime.now().isoformat()}\n")
            f.write("\n")
            f.write(encoded_data)
        
        return export_path

    def import_preset(self, import_path):
        """Import a preset from a shareable file."""
        if not os.path.exists(import_path):
            raise FileNotFoundError(f"Import file not found: {import_path}")
        
        # Read import file
        with open(import_path, 'r') as f:
            lines = f.readlines()
        
        # Extract metadata
        preset_name = None
        for line in lines[:5]:
            if line.startswith("# Original:"):
                preset_name = line.replace("# Original:", "").strip()
                break
        
        # If no preset name found, use import filename
        if not preset_name:
            preset_name = Path(import_path).stem
            if preset_name.endswith(".aspreset"):
                preset_name = preset_name[:-9]
        
        # Extract encoded data
        encoded_data = ''.join(lines[5:])
        
        # Decode preset data
        try:
            preset_data = base64.b64decode(encoded_data)
        except:
            raise ValueError(f"Invalid preset format: {import_path}")
        
        # Save decoded preset
        preset_path = self.preset_dir / f"{preset_name}.preset"
        with open(preset_path, 'wb') as f:
            f.write(preset_data)
        
        return str(preset_path)

# =============================================================================
# VISUALIZATION
# =============================================================================
class VisualizationMode:
    """Base class for visualization modes."""
    def __init__(self, config):
        self.config = config
        self.temp_files = []

    def get_filter_chain(self):
        """Get FFmpeg filter chain for this visualization mode."""
        raise NotImplementedError("Subclasses must implement get_filter_chain()")

    def __del__(self):
        """Clean up temporary files when the visualization mode is destroyed."""
        for path in self.temp_files:
            try:
                os.remove(path)
            except:
                pass

class WavesMode(VisualizationMode):
    """Classic audio waveform visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        return f"showwaves=s={width}x{height}:mode=line,format=rgb24"

class SpectrumMode(VisualizationMode):
    """Frequency spectrum visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        return f"showspectrum=s={width}x{height}:mode=combined,format=rgb24"

class CqtMode(VisualizationMode):
    """Constant Q transform visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        return f"showcqt=s={width}x{height},format=rgb24"

class ComboMode(VisualizationMode):
    """Combined waveform and spectrum visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        return (f"[0:a]showwaves=s={width}x{height}:mode=line[waves];"
                f"[0:a]showspectrum=s={width}x{height}:mode=combined[spectrum];"
                f"[waves][spectrum]blend=all_mode=addition,format=rgb24")

class EdgeMode(VisualizationMode):
    """Edge-detected audio visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        return (f"[0:a]showcqt=s={width}x{height}[cqt];"
                f"[cqt]edgedetect=low=0.1:high=0.4,format=rgb24")

class KaleidoscopeMode(VisualizationMode):
    """Kaleidoscope effect on spectrum."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        return (f"[0:a]showspectrum=s={width}x{height}:slide=replace:mode=combined,format=yuv420p[vis];"
                f"[vis]kaleidoscope=pattern=1:angle=0,format=rgb24")

class NeuralMode(VisualizationMode):
    """Neural network-inspired multi-band visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')

        # Make sure each section is at least 30 pixels high to avoid errors
        # Minimum height for each section is 30 pixels for showcqt
        min_height = 30

        # Check if height is adequate for three equal bands
        if height < min_height * 3:
            # Use a simpler filter chain if the height is too small
            return f"showspectrum=s={width}x{height}:mode=combined:color=rainbow,format=rgb24"

        # Calculate the height of each section
        height_third = max(min_height, height // 3)

        return (f"[0:a]asplit=3[bass][mid][high],"
                f"[bass]bandpass=f=100:width_type=h:w=200[filtered_bass],"
                f"[mid]bandpass=f=1000:width_type=h:w=800[filtered_mid],"
                f"[high]highpass=f=4000[filtered_high],"
                f"[filtered_bass]showwaves=s={width}x{height_third}:mode=cline:colors=0x00ffff[wave_bass],"
                f"[filtered_mid]showspectrum=s={width}x{height_third}:slide=scroll:mode=combined:color=rainbow[spec_mid],"
                f"[filtered_high]showcqt=s={width}x{height_third}:count=8:gamma=5[cqt_high],"
                f"[wave_bass][spec_mid][cqt_high]vstack=inputs=3,"
                f"hue='h=t/20':s='1+sin(t/10)/4',"
                f"boxblur=10:enable='if(eq(mod(t,4),0),1,0)',format=rgb24")

class TypographyMode(VisualizationMode):
    """Text-based reactive visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        
        # Create temporary lyrics file
        lyrics = [
            "♫ ♪ ♬ ♩ ♭",
            "ASCII SYMPHONY",
            "VISUAL SOUNDSCAPE",
            "AUDIO WAVES",
            "DIGITAL RHYTHM",
            "SONIC PATTERNS"
        ]
        
        # Use a temp file for the lyrics
        fd, path = tempfile.mkstemp(suffix='.txt')
        with os.fdopen(fd, 'w') as f:
            f.write('\n'.join(lyrics))
        
        self.temp_files.append(path)  # Store for cleanup later
        
        return (f"[0:a]asplit=2[a1][a2],"
                f"[a1]showwaves=s={width}x{height}:mode=cline:draw=full:colors=0xffffff[bg],"
                f"[a2]avectorscope=s={width}x{height}:zoom=1.5:draw=full[fg],"
                f"[bg][fg]blend=all_mode=screen:all_opacity=0.8,format=yuv422p,"
                f"drawtext=text='AUDIO':fontsize=w/5:x=(w-text_w)/2:y=(h-text_h)/2:"
                f"fontcolor=ffffff@0.8:enable='between(mod(t,2),0,0.3)',"
                f"drawtext=text='SYMPHONY':fontsize=w/8:x=(w-text_w)/2:y=(h-text_h)/2+h/4:"
                f"fontcolor=00ffff@0.6:enable='between(mod(t,2),0.3,0.6)',"
                f"drawtext=textfile={path}:reload=1:fontsize='w/20*sin(t)+w/10':"
                f"x='w/2+w/4*sin(t/2)':y='h/2+h/4*cos(t/2)':fontcolor=ffffff@0.7,"
                f"format=rgb24")

class ParticlesMode(VisualizationMode):
    """Particle system visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        
        return (f"[0:a]asplit=2[a][b],"
                f"[a]showwaves=s={width}x{height}:mode=cline:rate=60[waves],"
                f"[b]showspectrum=s={width}x{height}:slide=scroll:mode=combined[spectrum],"
                f"[waves][spectrum]blend=all_mode=screen:all_opacity=0.5,"
                f"format=rgba,"
                f"split=3[s1][s2][s3],"
                f"[s1]rotate=angle='t/10':fillcolor=0x00000000[r1],"
                f"[s2]rotate=angle='-t/15':fillcolor=0x00000000[r2],"
                f"[s3]rotate=angle='sin(t)*PI/4':fillcolor=0x00000000[r3],"
                f"[r1][r2][r3]blend=all_mode=lighten,format=rgb24")

class FractalMode(VisualizationMode):
    """Fractal-inspired recursive visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        
        return (f"[0:a]showcqt=s={width}x{height}:count=12:"
                f"attack=0.5:gamma=4:sono_v=fim,"
                f"split=4[q1][q2][q3][q4],"
                f"[q1]crop=iw/2:ih/2:0:0,scale={width}x{height}[c1],"
                f"[q2]crop=iw/2:ih/2:iw/2:0,scale={width}x{height}[c2],"
                f"[q3]crop=iw/2:ih/2:0:ih/2,scale={width}x{height}[c3],"
                f"[q4]crop=iw/2:ih/2:iw/2:ih/2,scale={width}x{height}[c4],"
                f"[c1][c2]hstack[top],"
                f"[c3][c4]hstack[bottom],"
                f"[top][bottom]vstack,hue='h=t/15',format=rgb24")

class VortexMode(VisualizationMode):
    """Rotating audio vortex visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        
        return (f"[0:a]showspectrum=s={width}x{height}:slide=replace:mode=combined[spec],"
                f"[spec]rotate=angle='t*2':fillcolor=black@0.5,"
                f"hue=h='2*PI*t':s=1.5,format=rgb24")

class SpectrosynthMode(VisualizationMode):
    """Multi-band spectral synthesis visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        
        return (f"[0:a]asplit=3[main][spec][wave],"
                f"[main]showfreqs=s={width}x{height//3}:scale=log:win_size=2048[freqs],"
                f"[spec]showspectrum=s={width}x{height//3}:mode=combined:slide=scroll[spectrum],"
                f"[wave]showwaves=s={width}x{height//3}:mode=p2p:split_channels=1[waves],"
                f"[freqs][spectrum][waves]vstack=inputs=3,format=rgb24")

class VisualizationEngine:
    """Engine for managing visualizations."""
    def __init__(self, config):
        self.config = config
        self.modes = self._load_visualization_modes()

    def _load_visualization_modes(self):
        """Load all available visualization modes."""
        return {
            'waves': WavesMode(self.config),
            'spectrum': SpectrumMode(self.config),
            'cqt': CqtMode(self.config),
            'combo': ComboMode(self.config),
            'edge': EdgeMode(self.config),
            'kaleidoscope': KaleidoscopeMode(self.config),
            'neural': NeuralMode(self.config),
            'typography': TypographyMode(self.config),
            'particles': ParticlesMode(self.config),
            'fractal': FractalMode(self.config),
            'vortex': VortexMode(self.config),
            'spectrosynth': SpectrosynthMode(self.config)
        }

    def get_visualization(self, mode_name=None):
        """Get visualization mode by name."""
        mode_name = mode_name or self.config.get('mode', 'waves')
        return self.modes.get(mode_name)

# =============================================================================
# RENDERING
# =============================================================================
class Renderer:
    """Abstract base class for renderers."""
    @staticmethod
    def create(config):
        """Factory method to create the appropriate renderer."""
        render_type = config.get('renderer', 'terminal')

        if render_type == 'terminal':
            return TerminalRenderer(config)
        elif render_type == 'file':
            return FileRenderer(config)
        else:
            raise ValueError(f"Unknown renderer type: {render_type}")

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("asciisymphony.renderer")
        self.ffmpeg_process = None

    def render(self, input_stream, output_stream):
        """Render the visualization."""
        raise NotImplementedError("Subclasses must implement render()")

    def stop(self):
        """Stop rendering."""
        if self.ffmpeg_process and self.ffmpeg_process.poll() is None:
            self.ffmpeg_process.terminate()
            try:
                self.ffmpeg_process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.kill()
            
            self.ffmpeg_process = None

class TerminalRenderer(Renderer):
    """Renderer that outputs ASCII art to the terminal."""
    def __init__(self, config):
        super().__init__(config)
        self.terminal_size = self._get_terminal_size()

    def _get_terminal_size(self):
        """Get the terminal size."""
        try:
            if platform.system() == 'Windows':
                # Windows
                from ctypes import windll, create_string_buffer
                h = windll.kernel32.GetStdHandle(-12)  # stderr
                csbi = create_string_buffer(22)
                windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
                import struct
                (_, _, _, _, _, left, top, right, bottom, _, _) = struct.unpack("hhhhHhhhhhh", csbi.raw)
                width = right - left + 1
                height = bottom - top + 1
            else:
                # Unix/Linux/macOS
                width, height = struct.unpack('HHHH', 
                    fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, 
                                struct.pack('HHHH', 0, 0, 0, 0))
                )[:2]
            
            return width, height
        except:
            # Default fallback
            return 80, 24

    def _adapt_config_to_terminal(self):
        """Adapt configuration to terminal size."""
        term_width, term_height = self._get_terminal_size()
        
        # Calculate aspect-correct size that fits in terminal
        # Each ASCII character is approximately 1:2 (width:height) ratio
        width = self.config.get('width', 160)
        height = self.config.get('height', 90)
        
        # Calculate max width and height that fit in terminal
        max_width = term_width
        max_height = term_height * 2  # Account for character aspect ratio
        
        # Maintain aspect ratio
        aspect_ratio = width / height
        
        if width > max_width:
            width = max_width
            height = int(width / aspect_ratio)
        
        if height > max_height:
            height = max_height
            width = int(height * aspect_ratio)
        
        # Ensure minimum size
        width = max(width, 40)
        height = max(height, 24)
        
        # Update config
        self.config.update({
            'width': width,
            'height': height
        })

    def render(self, input_stream, output_stream=None):
        """Render the visualization to the terminal."""
        # Adapt config to terminal size
        self._adapt_config_to_terminal()
        
        # Get visualization mode
        mode_name = self.config.get('mode', 'waves')
        mode = VisualizationEngine(self.config).get_visualization(mode_name)
        
        if not mode:
            raise ValueError(f"Unknown visualization mode: {mode_name}")
        
        # Get filter chain
        filter_chain = mode.get_filter_chain()
        
        # Build FFmpeg command
        cmd = [
            'ffmpeg',
            '-v', 'error',
            '-nostdin'
        ]
        
        # Add input arguments
        if isinstance(input_stream, str):
            # Input file
            cmd.extend(['-i', input_stream])
        else:
            # Live input arguments
            cmd.extend(input_stream)
        
        # Add filter chain
        cmd.extend([
            '-lavfi', filter_chain,
            '-f', 'caca',
            '-color', 'default',
            '-charset', 'ascii',  # Changed from unicode to ascii which is more compatible
            '-algorithm', self.config.get('dither', 'fstein'),
            '-'
        ])
        
        # Start FFmpeg process
        self.logger.info(f"Running FFmpeg: {' '.join(cmd)}")
        
        self.ffmpeg_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            universal_newlines=True
        )
        
        # Stream output to terminal
        try:
            # Clear screen
            print("\033[2J\033[H", end='')

            if self.ffmpeg_process and self.ffmpeg_process.stdout:
                for line in self.ffmpeg_process.stdout:
                    if output_stream:
                        output_stream.write(line)
                        output_stream.flush()
                    else:
                        print(line, end='')
                        sys.stdout.flush()

        except KeyboardInterrupt:
            self.stop()

        # Check for errors
        if self.ffmpeg_process and self.ffmpeg_process.poll() is not None and self.ffmpeg_process.returncode != 0:
            if hasattr(self.ffmpeg_process, 'stderr') and self.ffmpeg_process.stderr:
                stderr = self.ffmpeg_process.stderr.read()
                raise RuntimeError(f"FFmpeg error: {stderr}")
            else:
                raise RuntimeError("FFmpeg process failed with unknown error")

        return 0 if not self.ffmpeg_process else self.ffmpeg_process.returncode

class FileRenderer(Renderer):
    """Renderer that outputs to a video file with optimized processing."""
    try:
        # Try to import the fixed implementation
        from fixed_asciisymphony import FileRenderer as FixedFileRenderer
        _run_ascii_generator = FixedFileRenderer._run_ascii_generator
        _get_encoder_settings = FixedFileRenderer._get_encoder_settings
        _run_encoder = FixedFileRenderer._run_encoder
        _generate_ascii_art = FixedFileRenderer._generate_ascii_art
    except ImportError:
        # If import fails, we'll use the implementation in this file
        pass
    def render(self, input_stream, output_file):
        """Render the visualization to a file."""
        if not output_file:
            raise ValueError("Output file required for file renderer")

        # Get visualization mode
        mode_name = self.config.get('mode', 'waves')
        mode = VisualizationEngine(self.config).get_visualization(mode_name)

        if not mode:
            raise ValueError(f"Unknown visualization mode: {mode_name}")

        # Double-check that we're using the configured resolution
        width = self.config.get('width', 1280)
        height = self.config.get('height', 720)

        # Ensure dimensions are even (required for h264 encoding)
        if width % 2 != 0:
            width += 1
        if height % 2 != 0:
            height += 1

        # Update config with final dimensions
        self.config.update({
            'width': width,
            'height': height
        })

        # Report actual resolution being used
        print(f"\nGenerating video at {width}x{height} resolution...")

        # Get filter chain
        filter_chain = mode.get_filter_chain()

        # Build FFmpeg command for video generation
        cmd = [
            'ffmpeg',
            '-v', 'info',
            '-nostdin',
            '-y'  # Overwrite output file
        ]

        # Add input arguments
        if isinstance(input_stream, str):
            # Input file
            cmd.extend(['-i', input_stream])
        else:
            # Live input arguments
            cmd.extend(input_stream)

        # Add filter chain - will be modified in _run_ascii_generator
        cmd.extend([
            '-lavfi', filter_chain,
            '-f', 'caca',
            '-color', 'default',
            '-charset', 'ascii',  # Changed from unicode to ascii which is more compatible
            '-algorithm', self.config.get('dither', 'fstein'),
            '-'
        ])

        # Create temp file for intermediate output
        with tempfile.NamedTemporaryFile(suffix='.rgb', delete=False) as temp_file:
            temp_filename = temp_file.name

        # Run the video generator with proper error handling
        try:
            self.logger.info(f"Generating visualization with FFmpeg")
            return_code = self._run_ascii_generator(cmd, temp_filename)

            if return_code != 0:
                raise RuntimeError(f"Visualization generation failed with code {return_code}")

            # Process the temp file to create the final output
            self.logger.info(f"Encoding final video to {output_file}")

            # Build encoder command
            encoder_args = self._get_encoder_settings()

            # Get the original input file from the first command
            original_input = None
            for i, arg in enumerate(cmd):
                if arg == "-i" and i+1 < len(cmd):
                    original_input = cmd[i+1]
                    break

            # Build second FFmpeg command for encoding
            # Start with basic command structure
            cmd2 = [
                'ffmpeg',
                '-v', 'warning',
                '-f', 'rawvideo',
                '-pix_fmt', 'rgb24',
                '-s', f"{self.config.get('width')}x{self.config.get('height')}",
                '-r', str(self.config.get('fps', 30)),  # Add frame rate
                '-i', temp_filename
            ]

            # Add audio if available
            if original_input and os.path.exists(original_input):
                # Add second input for audio
                cmd2.extend([
                    # Input 2: The original audio file
                    '-i', original_input,
                    # Map streams
                    '-map', '0:v',      # Video from first input (raw video)
                    '-map', '1:a',      # Audio from second input (original file)
                    # Video codec settings
                    '-c:v', 'libx264',
                    '-crf', '23',
                    '-preset', 'medium',
                    '-pix_fmt', 'yuv420p',
                    # Audio codec settings
                    '-c:a', 'aac',
                    '-q:a', '1',
                    '-shortest'         # End when shortest stream ends
                ])
            else:
                # No audio - encode only video
                cmd2.extend(shlex.split(encoder_args))

            # Complete the command with output file
            cmd2.extend([
                '-metadata', 'title="AsciiSymphony Pro"',
                '-movflags', '+faststart',
                output_file
            ])

            # Run encoder with proper error handling
            return_code = self._run_encoder(cmd2)

            if return_code != 0:
                raise RuntimeError(f"Video encoding failed with code {return_code}")

            return return_code

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_filename)
            except:
                pass

    def _run_ascii_generator(self, cmd, output_file):
        """Run the ASCII generator process with proper error handling."""
        # Extract the original visualization filter and input file from the command
        input_file = None
        for i, arg in enumerate(cmd):
            if arg == "-i" and i+1 < len(cmd):
                input_file = cmd[i+1]
                break

        if not input_file:
            raise ValueError("Input file not found in command")

        # Find the original filter chain (if any)
        original_filter = ""
        for i, arg in enumerate(cmd):
            if arg == "-lavfi" and i+1 < len(cmd):
                original_filter = cmd[i+1]
                break

        # Get visualization mode from config
        mode = self.config.get('mode', 'waves')
        width = self.config.get('width')
        height = self.config.get('height')
        fps = self.config.get('fps', 30)

        # Determine the appropriate visualization filter if none was found
        if not original_filter:
            if mode == 'waves':
                original_filter = f"showwaves=s={width}x{height}:mode=line:colors=white"
            elif mode == 'spectrum':
                original_filter = f"showspectrum=s={width}x{height}:mode=combined:color=intensity"
            elif mode == 'cqt':
                original_filter = f"showcqt=s={width}x{height}"
            elif mode == 'neural':
                # Simplified neural mode for compatibility
                original_filter = f"showspectrum=s={width}x{height}:mode=combined:color=rainbow"
            else:
                # Default to a simple visualization
                original_filter = f"showwaves=s={width}x{height}:mode=line:colors=white"

        # Calculate proper ASCII grid size based on resolution and mode
        # Choose ASCII density based on mode and user preference
        density_factor = 1.0
        if self.config.get('ascii_density') is not None:
            density_factor = float(self.config.get('ascii_density'))
        else:
            # Mode-specific density adjustments
            mode_density = {
                'neural': 1.5,      # Neural needs more detail
                'typography': 0.8,  # Typography works better with larger cells
                'fractal': 1.3,     # Fractal needs more detail
                'spectrum': 1.2,    # Spectrum needs moderate detail
                'cqt': 1.2,         # CQT needs moderate detail
                'waves': 1.0        # Waves is the baseline
            }
            density_factor = mode_density.get(mode, 1.0)

        # Calculate grid cells based on standard ASCII terminal (80x25 characters)
        # and adjust by density factor and resolution
        base_cols = 80
        base_rows = 40

        # Adjust based on resolution
        resolution_factor = min(width / 1280.0, height / 720.0)
        grid_cols = int(base_cols * resolution_factor * density_factor)
        grid_rows = int(base_rows * resolution_factor * density_factor)

        # Ensure minimum and maximum grid size for proper ASCII effect
        grid_cols = min(max(30, grid_cols), width // 8)
        grid_rows = min(max(20, grid_rows), height // 8)

        # Calculate cell dimensions
        cell_width = width // grid_cols
        cell_height = height // grid_rows

        # Create the complete ASCII filter chain
        ascii_filter = (
            # Downscale to grid size (creates the ASCII character cells effect)
            f"scale={grid_cols}:{grid_rows},"

            # Upscale with nearest neighbor to maintain pixelation
            f"scale={width}:{height}:flags=neighbor,"

            # Add grid lines to simulate character boundaries
            f"drawgrid=width={cell_width}:height={cell_height}:color=black@0.2"
        )

        # Apply color theme based on user selection
        color_scheme = self.config.get('colors', 'thermal')
        color_filter = ""

        # Simple color mapping with basic filters
        if color_scheme == 'green':
            color_filter = ",hue=s=0.8:h=0.333"  # Green tint
        elif color_scheme == 'amber':
            color_filter = ",hue=s=0.8:h=0.167"  # Amber/gold tint
        elif color_scheme == 'blue':
            color_filter = ",hue=s=0.8:h=0.667"  # Blue tint
        elif color_scheme == 'red':
            color_filter = ",hue=s=0.8:h=0"      # Red tint
        elif color_scheme == 'monochrome':
            color_filter = ",hue=s=0"            # Black and white
        elif color_scheme == 'thermal':
            # Simple thermal-like effect
            color_filter = ",hue=h=0.1"

        # Add subtle scanlines for higher quality settings
        quality = self.config.get('quality', 'balanced')
        scanline_filter = ""
        if quality in ['high', 'ultra'] and height > 400:
            scanline_intensity = 0.05  # Very subtle
            scanline_height = height // 90  # Thin scanlines
            scanline_filter = f",drawgrid=h={scanline_height}:w=0:color=black@{scanline_intensity}"

        # Combine filters: first apply visualization, then ASCII effect, color and scanlines
        # Do not use yuv420p in the filter chain as it conflicts with the rgb24 pixel format
        combined_filter = (
            f"{original_filter},"
            f"{ascii_filter}"
            f"{color_filter}"
            f"{scanline_filter}"
            f"[outv]"  # Add an output label for filter_complex
        )

        # Create direct command to generate raw video frames
        direct_cmd = [
            'ffmpeg',
            '-v', 'verbose',  # Increase verbosity to see detailed errors
            '-nostdin',
            '-y',  # Overwrite
            '-i', input_file,
            '-filter_complex', f"[0:a]{combined_filter}",  # Use filter_complex to convert audio to video
            '-map', '[outv]',  # Map the labeled output from filter_complex
            '-r', str(fps),  # Set frame rate
            '-pix_fmt', 'rgb24',  # Output format needed by renderer
            '-f', 'rawvideo',  # Output as raw video data
            output_file  # Write directly to expected output
        ]

        # Run the command with proper error handling and progress display
        try:
            self.logger.info(f"Running FFmpeg with direct ASCII filter: {' '.join(direct_cmd)}")

            # Get duration for progress calculation
            duration_sec = 0
            try:
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                     "default=noprint_wrappers=1:nokey=1", input_file],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    duration_sec = float(result.stdout.strip())
            except Exception as e:
                self.logger.warning(f"Could not get duration: {str(e)}")

            # Start the process
            process = subprocess.Popen(
                direct_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )

            # Set up progress bar
            if duration_sec > 0:
                total_frames = int(duration_sec * fps)
                print(f"\nGenerating visualization frames from {duration_sec:.1f} seconds of audio...")
                progress = ProgressBar(
                    total=100,  # Use percentage
                    prefix="Generating Frames:",
                    suffix="Complete"
                )
            else:
                # Generic progress indication
                print("\nGenerating visualization... This may take a few minutes.")
                progress = None

            # Monitor stderr for progress updates
            frame_pattern = re.compile(r'frame=\s*(\d+)')

            while process.poll() is None:
                stderr_line = process.stderr.readline()
                if stderr_line:
                    match = frame_pattern.search(stderr_line)
                    if match and progress:
                        frame_count = int(match.group(1))
                        if total_frames > 0:
                            percentage = min(100, int(frame_count / total_frames * 100))
                            progress.print(percentage)

            # Complete the progress bar
            if progress:
                progress.finish()

            # Check for errors
            if process.returncode != 0:
                stderr_output = process.stderr.read()
                self.logger.error(f"FFmpeg error: {stderr_output}")
                return process.returncode

            return 0

        except Exception as e:
            self.logger.error(f"Process execution error: {str(e)}")
            return 1

    """
This is an improved version of the _run_ascii_generator method
for AsciiSymphony Pro. It bypasses the problematic caca format
and creates a more reliable ASCII art effect with all the advanced features.

Copy this method into the FileRenderer class in asciisymphony_ultra_fixed.py
to replace the existing _run_ascii_generator method.
"""

def _run_ascii_generator(self, cmd, output_file):
    """Run the ASCII generator process with proper error handling."""
    # Extract the original visualization filter and input file from the command
    input_file = None
    for i, arg in enumerate(cmd):
        if arg == "-i" and i+1 < len(cmd):
            input_file = cmd[i+1]
            break
            
    if not input_file:
        raise ValueError("Input file not found in command")
        
    # Find the original filter chain (if any)
    original_filter = ""
    for i, arg in enumerate(cmd):
        if arg == "-lavfi" and i+1 < len(cmd):
            original_filter = cmd[i+1]
            break
            
    # Get visualization mode from config
    mode = self.config.get('mode', 'waves')
    width = self.config.get('width')
    height = self.config.get('height')
    fps = self.config.get('fps', 30)
    
    # Determine the appropriate visualization filter if none was found
    if not original_filter:
        if mode == 'waves':
            original_filter = f"showwaves=s={width}x{height}:mode=line:colors=white"
        elif mode == 'spectrum':
            original_filter = f"showspectrum=s={width}x{height}:mode=combined:color=intensity"
        elif mode == 'cqt':
            original_filter = f"showcqt=s={width}x{height}"
        elif mode == 'neural':
            # Simplified neural mode for compatibility
            original_filter = f"showspectrum=s={width}x{height}:mode=combined:color=rainbow"
        else:
            # Default to a simple visualization
            original_filter = f"showwaves=s={width}x{height}:mode=line:colors=white"
    
    # Calculate proper ASCII grid size based on resolution and mode
    # Choose ASCII density based on mode and user preference
    density_factor = 1.0
    if self.config.get('ascii_density') is not None:
        density_factor = float(self.config.get('ascii_density'))
    else:
        # Mode-specific density adjustments
        mode_density = {
            'neural': 1.5,      # Neural needs more detail
            'typography': 0.8,  # Typography works better with larger cells
            'fractal': 1.3,     # Fractal needs more detail
            'spectrum': 1.2,    # Spectrum needs moderate detail
            'cqt': 1.2,         # CQT needs moderate detail
            'waves': 1.0        # Waves is the baseline
        }
        density_factor = mode_density.get(mode, 1.0)
        
    # Calculate grid cells based on standard ASCII terminal (80x25 characters)
    # and adjust by density factor and resolution
    base_cols = 80
    base_rows = 40
    
    # Adjust based on resolution
    resolution_factor = min(width / 1280.0, height / 720.0)
    grid_cols = int(base_cols * resolution_factor * density_factor)
    grid_rows = int(base_rows * resolution_factor * density_factor)
    
    # Ensure minimum and maximum grid size for proper ASCII effect
    grid_cols = min(max(30, grid_cols), width // 8)
    grid_rows = min(max(20, grid_rows), height // 8)
    
    # Calculate cell dimensions
    cell_width = width // grid_cols
    cell_height = height // grid_rows
    
    # Create the complete ASCII filter chain
    ascii_filter = (
        # Downscale to grid size (creates the ASCII character cells effect)
        f"scale={grid_cols}:{grid_rows},"
        
        # Upscale with nearest neighbor to maintain pixelation
        f"scale={width}:{height}:flags=neighbor,"
        
        # Add grid lines to simulate character boundaries
        f"drawgrid=width={cell_width}:height={cell_height}:color=black@0.2"
    )
    
    # Apply color theme based on user selection
    color_scheme = self.config.get('colors', 'thermal')
    color_filter = ""
    
    # Simple color mapping with basic filters
    if color_scheme == 'green':
        color_filter = ",hue=s=0.8:h=0.333"  # Green tint
    elif color_scheme == 'amber':
        color_filter = ",hue=s=0.8:h=0.167"  # Amber/gold tint
    elif color_scheme == 'blue':
        color_filter = ",hue=s=0.8:h=0.667"  # Blue tint
    elif color_scheme == 'red':
        color_filter = ",hue=s=0.8:h=0"      # Red tint
    elif color_scheme == 'monochrome':
        color_filter = ",hue=s=0"            # Black and white
    elif color_scheme == 'thermal':
        # Simple thermal-like effect
        color_filter = ",hue=h=0.1"
    
    # Add subtle scanlines for higher quality settings
    quality = self.config.get('quality', 'balanced')
    scanline_filter = ""
    if quality in ['high', 'ultra'] and height > 400:
        scanline_intensity = 0.05  # Very subtle
        scanline_height = height // 90  # Thin scanlines
        scanline_filter = f",drawgrid=h={scanline_height}:w=0:color=black@{scanline_intensity}"
    
    # Combine filters: first apply visualization, then ASCII effect, color and scanlines
    combined_filter = (
        f"{original_filter},"
        f"{ascii_filter}"
        f"{color_filter}"
        f"{scanline_filter}"
        f"[outv]"  # Add an output label for filter_complex
    )
    
    # Create direct command to generate raw video frames
    direct_cmd = [
        'ffmpeg',
        '-v', 'verbose',  # Increase verbosity to see detailed errors
        '-nostdin',
        '-y',  # Overwrite
        '-i', input_file,
        '-filter_complex', f"[0:a]{combined_filter}",  # Use filter_complex to convert audio to video
        '-map', '[outv]',  # Map the labeled output from filter_complex
        '-r', str(fps),  # Set frame rate
        '-pix_fmt', 'rgb24',  # Output format needed by renderer
        '-f', 'rawvideo',  # Output as raw video data
        output_file  # Write directly to expected output
    ]
    
    # Run the command with proper error handling and progress display
    try:
        self.logger.info(f"Running FFmpeg with direct ASCII filter: {' '.join(direct_cmd)}")
        
        # Get duration for progress calculation
        duration_sec = 0
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                 "default=noprint_wrappers=1:nokey=1", input_file],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                duration_sec = float(result.stdout.strip())
        except Exception as e:
            self.logger.warning(f"Could not get duration: {str(e)}")
        
        # Start the process
        process = subprocess.Popen(
            direct_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        # Set up progress bar
        if duration_sec > 0:
            total_frames = int(duration_sec * fps)
            print(f"\nGenerating visualization frames from {duration_sec:.1f} seconds of audio...")
            progress = ProgressBar(
                total=100,  # Use percentage
                prefix="Generating Frames:",
                suffix="Complete"
            )
        else:
            # Generic progress indication
            print("\nGenerating visualization... This may take a few minutes.")
            progress = None
        
        # Monitor stderr for progress updates
        frame_pattern = re.compile(r'frame=\s*(\d+)')
        
        while process.poll() is None:
            stderr_line = process.stderr.readline()
            if stderr_line:
                match = frame_pattern.search(stderr_line)
                if match and progress:
                    frame_count = int(match.group(1))
                    if total_frames > 0:
                        percentage = min(100, int(frame_count / total_frames * 100))
                        progress.print(percentage)
        
        # Complete the progress bar
        if progress:
            progress.finish()
        
        # Check for errors
        if process.returncode != 0:
            stderr_output = process.stderr.read()
            self.logger.error(f"FFmpeg error: {stderr_output}")
            return process.returncode
        """Get encoder settings based on configuration."""
        encoder = self.config.get('encoder', 'h264')
        quality = self.config.get('quality', 'balanced')

        # Make sure dimensions are even numbers for h264
        width = self.config.get('width', 0)
        height = self.config.get('height', 0)

        # Ensure height and width are even numbers
        if height % 2 != 0:
            height += 1
            self.config.update({'height': height})

        if width % 2 != 0:
            width += 1
            self.config.update({'width': width})

        # Map quality to CRF value (lower is better quality)
        crf_map = {
            'ultra': 18,
            'high': 20,
            'balanced': 23,
            'low': 28
        }

        # Map quality to preset (slower is better quality)
        preset_map = {
            'ultra': 'slow',
            'high': 'medium',
            'balanced': 'medium',
            'low': 'fast'
        }

        crf = crf_map.get(quality, 23)
        preset = preset_map.get(quality, 'medium')

        if encoder == 'h264':
            return f"-c:v libx264 -crf {crf} -preset {preset} -pix_fmt yuv420p"
        elif encoder == 'vp9':
            return f"-c:v libvpx-vp9 -crf {crf} -b:v 0 -pix_fmt yuv420p"
        elif encoder == 'gif':
            return '-filter_complex "[0:v]split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -f gif'
        else:
            # Default to h264
            return f"-c:v libx264 -crf {crf} -preset {preset} -pix_fmt yuv420p"
        
        return 0
        
    except Exception as e:
        self.logger.error(f"Process execution error: {str(e)}")
        return 1

        # Try to get the audio duration to estimate progress
        duration_sec = 0
        input_file = ""
        for i, arg in enumerate(cmd):
            if arg == "-i" and i+1 < len(cmd):
                input_file = cmd[i+1]
                break

        if os.path.exists(input_file):
            try:
                # Get duration using ffprobe
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                     "default=noprint_wrappers=1:nokey=1", input_file],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    duration_sec = float(result.stdout.strip())
            except:
                # If we can't get the duration, we'll use a generic progress bar
                pass

        # Run process with consistent error handling
        try:
            self.logger.info(f"Running FFmpeg: {' '.join(cmd)}")

            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )

            # Set up progress bar
            if duration_sec > 0:
                total_frames = int(duration_sec * self.config.get('fps', 30))
                print(f"\nGenerating visualization frames from {duration_sec:.1f} seconds of audio...")
                progress = ProgressBar(
                    total=100,  # Use percentage instead of frames
                    prefix="Generating Frames:",
                    suffix="Complete"
                )
            else:
                # Generic progress indication
                print("\nGenerating visualization... This may take a few minutes.")
                progress = None

            # Monitor stderr for progress updates
            frame_count = 0
            frame_pattern = re.compile(r'frame=\s*(\d+)')

            while process.poll() is None:
                stderr_line = process.stderr.readline()
                if stderr_line:
                    match = frame_pattern.search(stderr_line)
                    if match and progress:
                        frame_count = int(match.group(1))
                        if total_frames > 0:
                            percentage = min(100, int(frame_count / total_frames * 100))
                            progress.print(percentage)

            # Complete the progress bar if it exists
            if progress:
                progress.finish()

            # Get the final result
            stderr_output = process.stderr.read()
            returncode = process.returncode

            # Check for errors
            if returncode != 0:
                self.logger.error(f"FFmpeg error: {stderr_output}")

            return returncode
        except Exception as e:
            self.logger.error(f"Process execution error: {str(e)}")
            return 1

    def _run_encoder(self, cmd):
        """Run the encoder process with proper error handling."""
        # Run process
        try:
            self.logger.info(f"Running encoder: {' '.join(cmd)}")

            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )

            # Set up a progress bar for encoding
            print("\nEncoding video file...")
            progress = ProgressBar(
                total=100,
                prefix="Encoding Progress:",
                suffix="Complete"
            )

            # Look for progress information
            time_pattern = re.compile(r'time=(\d+):(\d+):(\d+\.\d+)')
            duration_pattern = re.compile(r'Duration: (\d+):(\d+):(\d+\.\d+)')

            duration_seconds = 0

            # Monitor stderr for progress updates
            while process.poll() is None:
                stderr_line = process.stderr.readline()
                if stderr_line:
                    # Look for duration if we don't have it yet
                    if duration_seconds == 0:
                        duration_match = duration_pattern.search(stderr_line)
                        if duration_match:
                            h, m, s = duration_match.groups()
                            duration_seconds = int(h) * 3600 + int(m) * 60 + float(s)

                    # Look for current time position
                    time_match = time_pattern.search(stderr_line)
                    if time_match and duration_seconds > 0:
                        h, m, s = time_match.groups()
                        current_seconds = int(h) * 3600 + int(m) * 60 + float(s)
                        percentage = min(99, int(current_seconds / duration_seconds * 100))
                        progress.print(percentage)

            # Complete the progress
            progress.finish()

            # Get the final result
            stderr_output = process.stderr.read()
            returncode = process.returncode

            # Check for errors
            if returncode != 0:
                self.logger.error(f"Encoding error: {stderr_output}")
                # Print more detailed information for debugging
                if "No such file or directory" in stderr_output:
                    self.logger.error("Input file not found or insufficient permissions")
                elif "Invalid data found when processing input" in stderr_output:
                    self.logger.error("The intermediate file format may be incorrect")
                elif "Unable to find a suitable output format" in stderr_output:
                    self.logger.error("FFmpeg cannot determine output format - check file extension")
                elif "does not contain any stream" in stderr_output:
                    self.logger.error("The temp file does not contain valid video data")
            else:
                self.logger.info("Encoding completed successfully")
                print("\nVideo encoding completed successfully!")

            return returncode
        except Exception as e:
            self.logger.error(f"Encoder process error: {str(e)}")
            return 1

    def _get_encoder_settings(self):
        """Get encoder settings based on configuration."""
        encoder = self.config.get('encoder', 'h264')
        quality = self.config.get('quality', 'balanced')

        # Make sure dimensions are even numbers for h264
        width = self.config.get('width', 0)
        height = self.config.get('height', 0)

        # Ensure height and width are even numbers
        if height % 2 != 0:
            height += 1
            self.config.update({'height': height})

        if width % 2 != 0:
            width += 1
            self.config.update({'width': width})

        # Map quality to CRF value (lower is better quality)
        crf_map = {
            'ultra': 18,
            'high': 20,
            'balanced': 23,
            'low': 28
        }

        # Map quality to preset (slower is better quality)
        preset_map = {
            'ultra': 'slow',
            'high': 'medium',
            'balanced': 'medium',
            'low': 'fast'
        }

        crf = crf_map.get(quality, 23)
        preset = preset_map.get(quality, 'medium')

        if encoder == 'h264':
            return f"-c:v libx264 -crf {crf} -preset {preset} -pix_fmt yuv420p"
        elif encoder == 'vp9':
            return f"-c:v libvpx-vp9 -crf {crf} -b:v 0 -pix_fmt yuv420p"
        elif encoder == 'gif':
            return '-filter_complex "[0:v]split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -f gif'
        else:
            # Default to h264
            return f"-c:v libx264 -crf {crf} -preset {preset} -pix_fmt yuv420p"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
class ProgressBar:
    """Simple text-based progress bar for terminal."""
    def __init__(self, total=100, prefix='Progress:', suffix='Complete', length=50, fill='█', print_end='\r'):
        """Initialize the progress bar.

        Args:
            total: Total iterations (100%)
            prefix: Prefix string
            suffix: Suffix string
            length: Bar length
            fill: Bar fill character
            print_end: End character
        """
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.length = length
        self.fill = fill
        self.print_end = print_end
        self.iteration = 0
        self.start_time = time.time()
        self.last_update_time = 0
        self.update_interval = 0.1  # seconds between updates

    def print(self, iteration=None):
        """Print the progress bar.

        Args:
            iteration: Current iteration
        """
        current_time = time.time()
        if iteration is not None:
            self.iteration = iteration

        # Limit update frequency
        if current_time - self.last_update_time < self.update_interval and self.iteration < self.total:
            return

        self.last_update_time = current_time

        percent = f"{100 * (self.iteration / float(self.total)):.1f}"
        filled_length = int(self.length * self.iteration // self.total)
        bar = self.fill * filled_length + '-' * (self.length - filled_length)

        # Calculate elapsed time
        elapsed = current_time - self.start_time
        time_str = f"{elapsed:.1f}s" if elapsed < 60 else f"{int(elapsed//60)}m {int(elapsed%60)}s"

        # Print progress bar
        sys.stdout.write(f'\r{self.prefix} |{bar}| {percent}% {self.suffix} ({time_str})')
        sys.stdout.flush()

        # Print new line on complete
        if self.iteration >= self.total:
            print()

    def update(self, step=1):
        """Update the progress bar by the specified step.

        Args:
            step: Step size
        """
        self.iteration += step
        self.print()

    def finish(self):
        """Complete the progress bar."""
        self.iteration = self.total
        self.print()

@contextmanager
def progress_tracker(total, description="Processing"):
    """Context manager for progress tracking.

    Args:
        total: Total number of items
        description: Task description
    """
    progress = ProgressBar(total=total, prefix=description)
    progress.print(0)
    try:
        yield progress
    finally:
        progress.finish()

# =============================================================================
# MAIN APPLICATION
# =============================================================================
class AsciiSymphony:
    """Main AsciiSymphony application class."""
    VERSION = "3.0.0"
    DESCRIPTION = "AsciiSymphony Pro: Enterprise-Grade ASCII Art Audio Visualizer"

    def __init__(self):
        self.config = None
        self.logger = None
        self.audio_manager = None
        self.visualization_engine = None
        self.preset_manager = None
        self.renderer = None
        self.error_handler = None
        self.initialized = False

    def initialize(self, args=None):
        """Initialize the application."""
        # Parse arguments and create config
        self.config = Config()
        self.parse_args(args)
        
        # Set up logging
        debug_mode = self.config.get('debug', False)
        self.logger = setup_logging(debug_mode)
        
        # Initialize components
        self.audio_manager = AudioDeviceManager(self.config)
        self.visualization_engine = VisualizationEngine(self.config)
        self.preset_manager = PresetManager(self.config)
        self.error_handler = ErrorHandler(self)
        
        # Check dependencies and capabilities
        self.error_handler.check_ffmpeg_capabilities()
        
        self.initialized = True
        self.logger.info(f"AsciiSymphony Pro {self.VERSION} initialized")

    def parse_args(self, args=None):
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(description=self.DESCRIPTION)
        
        # Input/output options
        parser.add_argument('input', nargs='?', help='Input audio file')
        parser.add_argument('output', nargs='?', help='Output video file')
        
        # Basic options
        parser.add_argument('--mode', help='Visualization mode')
        parser.add_argument('--fps', type=int, help='Frames per second')
        parser.add_argument('--quality', choices=['low', 'balanced', 'high', 'ultra'],
                            help='Quality level')
        parser.add_argument('--colors', help='Color scheme')
        parser.add_argument('--charset', choices=['ascii', 'unicode', 'blocks'],
                            help='ASCII character set')
        parser.add_argument('--dither', help='Dithering algorithm')
        parser.add_argument('--ascii-density', type=float,
                            help='ASCII character density (0.5=sparse, 1.0=normal, 2.0=dense, 3.0=very dense)')
        
        # Live input options
        parser.add_argument('--live', action='store_true', help='Use live audio input')
        parser.add_argument('--device', help='Audio input device')
        parser.add_argument('--list-devices', action='store_true', 
                            help='List available audio input devices')
        parser.add_argument('--latency', choices=['normal', 'low', 'realtime'], 
                            help='Latency mode for live input')
        parser.add_argument('--buffer', type=int, help='Audio buffer size')
        
        # Preset management
        parser.add_argument('--list-presets', action='store_true', 
                            help='List available presets')
        parser.add_argument('--save-preset', help='Save current settings as preset')
        parser.add_argument('--load-preset', help='Load settings from preset')
        parser.add_argument('--export-preset', nargs='+', 
                            help='Export preset to portable format')
        parser.add_argument('--import-preset', help='Import preset from portable format')
        
        # Advanced options
        parser.add_argument('--width', type=int, help='Width in pixels')
        parser.add_argument('--height', type=int, help='Height in pixels')
        parser.add_argument('--gpu', type=int, choices=[0, 1],
                            help='Enable/disable GPU acceleration')
        parser.add_argument('--hdr', action='store_true',
                            help='Enable HDR processing')
        parser.add_argument('--encoder', choices=['h264', 'vp9', 'gif'],
                            help='Output encoder')
        parser.add_argument('--threads', type=int, help='Number of threads')
        parser.add_argument('--renderer', choices=['terminal', 'file'],
                            help='Renderer type')
        parser.add_argument('--preview', action='store_true',
                            help='Show libcaca ASCII preview in terminal while generating file output')
        
        # Debug options
        parser.add_argument('--debug', action='store_true', 
                            help='Enable debug logging')
        
        # Parse arguments
        parsed_args = parser.parse_args(args)
        
        # Convert args to config
        for key, value in vars(parsed_args).items():
            if value is not None:
                self.config.settings[key] = value
        
        return parsed_args

    def run(self):
        """Run the application based on configuration."""
        if not self.initialized:
            self.initialize()
        
        try:
            # Handle special commands
            if self.config.get('list_devices'):
                return self.list_devices()
            
            if self.config.get('list_presets'):
                return self.list_presets()
            
            if self.config.get('save_preset'):
                return self.save_preset(self.config.get('save_preset'))
            
            if self.config.get('load_preset'):
                self.load_preset(self.config.get('load_preset'))
                # Continue with normal execution using loaded preset
            
            if self.config.get('export_preset'):
                args = self.config.get('export_preset')
                preset_name = args[0]
                export_file = args[1] if len(args) > 1 else None
                return self.export_preset(preset_name, export_file)
            
            if self.config.get('import_preset'):
                return self.import_preset(self.config.get('import_preset'))
            
            # Regular execution
            if self.config.get('live'):
                return self.process_live(self.config.get('device'))
            else:
                input_file = self.config.get('input')
                output_file = self.config.get('output')
                
                if not input_file:
                    self.logger.error("Input file required for processing")
                    return 1
                
                if not output_file:
                    self.logger.error("Output file required for processing")
                    return 1
                
                return self.process_file(input_file, output_file)
            
        except Exception as e:
            self.logger.error(f"Error: {str(e)}")
            if self.config.get('debug'):
                import traceback
                self.logger.error(traceback.format_exc())
            
            # Try to handle the error
            try:
                self.error_handler.handle_error(e)
                # If error handling succeeded, retry
                self.logger.info("Retrying after error recovery")
                return self.run()
            except Exception as recovery_error:
                self.logger.error(f"Error recovery failed: {str(recovery_error)}")
                return 1

    def list_devices(self):
        """List available audio input devices."""
        devices = self.audio_manager.list_devices()
        
        print("Available audio input devices:")
        print("-----------------------------")
        for idx, name in devices:
            print(f"[{idx}] {name}")
        
        print("\nUsage:")
        print(f"  {sys.argv[0]} --live --device <device>")
        print(f"Example: {sys.argv[0]} --live --device 0")
        
        return 0

    def list_presets(self):
        """List available presets."""
        presets = self.preset_manager.list_presets()
        
        print("Available presets:")
        print("-----------------")
        
        for preset in presets:
            print(f"{preset['name']:<20} | {preset['mode']:<15} | {preset['created']}")
        
        print("\nUsage:")
        print(f"  {sys.argv[0]} --load-preset PRESET_NAME [input_file] [output_file]")
        print(f"  {sys.argv[0]} --save-preset PRESET_NAME")
        print(f"  {sys.argv[0]} --export-preset PRESET_NAME [export_file]")
        print(f"  {sys.argv[0]} --import-preset IMPORT_FILE")
        
        return 0

    def save_preset(self, preset_name):
        """Save current configuration as a preset."""
        try:
            preset_path = self.preset_manager.save_preset(preset_name)
            print(f"Preset saved: {preset_name}")
            return 0
        except Exception as e:
            self.logger.error(f"Error saving preset: {str(e)}")
            return 1

    def load_preset(self, preset_name):
        """Load a preset and apply its settings."""
        try:
            preset_data = self.preset_manager.load_preset(preset_name)
            print(f"Preset loaded: {preset_name}")
            return 0
        except Exception as e:
            self.logger.error(f"Error loading preset: {str(e)}")
            return 1

    def export_preset(self, preset_name, export_path=None):
        """Export a preset to a shareable file."""
        try:
            export_path = self.preset_manager.export_preset(preset_name, export_path)
            print(f"Preset exported: {export_path}")
            return 0
        except Exception as e:
            self.logger.error(f"Error exporting preset: {str(e)}")
            return 1

    def import_preset(self, import_path):
        """Import a preset from a shareable file."""
        try:
            preset_path = self.preset_manager.import_preset(import_path)
            print(f"Preset imported: {Path(preset_path).stem}")
            return 0
        except Exception as e:
            self.logger.error(f"Error importing preset: {str(e)}")
            return 1

    def process_file(self, input_file, output_file):
        """Process an audio file."""
        self.logger.info(f"Processing file: {input_file} -> {output_file}")

        try:
            # Check input file
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"Input file not found: {input_file}")

            # Check if preview is enabled - remove the preview flag to prevent recursion
            preview_enabled = self.config.settings.pop('preview', False)

            if preview_enabled:
                # Show terminal preview first
                print("Starting libcaca ASCII preview in terminal...")
                print("Press Ctrl+C to stop preview and continue with file generation")

                # Temporarily set renderer to terminal for preview
                original_renderer = self.config.get('renderer')
                self.config.update({'renderer': 'terminal'})

                # Create a separate config for the terminal renderer to prevent resolution changes
                terminal_config = Config()
                terminal_config.settings = dict(self.config.settings)  # Create a copy
                terminal_config.update({'renderer': 'terminal'})

                # Create terminal renderer with the separate config
                terminal_renderer = TerminalRenderer(terminal_config)

                try:
                    # Explicitly set a smaller preview size for the terminal
                    terminal_config.update({
                        'width': min(terminal_config.get('width', 1280), 80),
                        'height': min(terminal_config.get('height', 720), 60)
                    })

                    # Make sure to use a simple visualization mode for preview if using neural
                    # This way we don't run into dimension issues with the preview
                    if terminal_config.get('mode') == 'neural':
                        print("Using spectrum mode for preview (neural mode works better with full render)")
                        terminal_config.update({'mode': 'spectrum'})

                    # Direct render call - will block until complete or Ctrl+C
                    try:
                        print("\nShowing ASCII preview... Press Ctrl+C to stop and proceed to full render")
                        terminal_renderer.render(input_file, None)
                    except KeyboardInterrupt:
                        print("\nPreview stopped. Continuing with file generation...")

                finally:
                    # Stop the renderer if it's still running
                    terminal_renderer.stop()

                    # Make sure we're preserving the original renderer setting
                    # without carrying over any terminal preview display adaptations
                    self.config.update({'renderer': original_renderer})

            # Create renderer for file output
            self.renderer = Renderer.create(self.config)

            # Process file
            start_time = time.time()
            result = self.renderer.render(input_file, output_file)
            elapsed_time = time.time() - start_time

            self.logger.info(f"Processing completed in {elapsed_time:.2f} seconds")

            # Optimize output if needed
            if output_file.endswith('.mp4'):
                self.optimize_mp4(output_file)

            return result

        except Exception as e:
            self.logger.error(f"Error processing file: {str(e)}")
            raise

    def process_live(self, device_id=None):
        """Process live audio input."""
        self.logger.info(f"Processing live audio input")
        
        # Check if PyAudio is available for live processing
        if not PYAUDIO_AVAILABLE:
            self.logger.error("Live audio processing requires PyAudio.")
            print("Error: PyAudio is not installed or couldn't be imported.")
            print("Install PyAudio with: pip install pyaudio")
            print("On Ubuntu/Debian, you may need: sudo apt-get install python3-pyaudio")
            return 1
            
        try:
            # Detect audio devices if needed
            if not self.audio_manager.devices:
                self.audio_manager.detect_devices()
            
            # Create live audio processor
            live_processor = LiveAudioProcessor(self.config, self.audio_manager)
            
            # Create renderer (default to terminal for live)
            if 'renderer' not in self.config.settings:
                self.config.settings['renderer'] = 'terminal'
            
            self.renderer = Renderer.create(self.config)
            
            # Get FFmpeg input arguments for live audio
            ffmpeg_args = live_processor.get_ffmpeg_input_args(device_id)
            
            # Start rendering
            print("Press Ctrl+C to stop")
            result = self.renderer.render(ffmpeg_args, None)
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error processing live audio: {str(e)}")
            raise

    def optimize_mp4(self, output_file):
        """Optimize MP4 file for streaming."""
        self.logger.info(f"Optimizing MP4 file for streaming: {output_file}")

        temp_file = f"{output_file}.temp.mp4"

        try:
            # Show a simple progress message
            print("\nOptimizing MP4 file for web streaming...")
            progress = ProgressBar(total=100, prefix="Optimizing MP4:", suffix="Complete")
            progress.print(0)

            # Use FFmpeg to optimize MP4
            cmd = [
                'ffmpeg',
                '-v', 'warning',
                '-i', output_file,
                '-c', 'copy',
                '-movflags', 'faststart',
                temp_file
            ]

            # Run process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Show simple progress (we don't get much feedback for this operation)
            while process.poll() is None:
                # Simulate progress
                for i in range(10, 95, 5):
                    time.sleep(0.1)
                    progress.print(i)

                # If still running, just wait a bit
                time.sleep(0.5)

            # Finish progress
            progress.print(100)

            # Check result
            if process.returncode != 0:
                stderr_output = process.stderr.read()
                self.logger.error(f"MP4 optimization error: {stderr_output}")
                raise RuntimeError(f"MP4 optimization failed: {stderr_output}")

            # Replace original with optimized version
            os.replace(temp_file, output_file)

            self.logger.info("MP4 optimization complete")
            print("MP4 optimization complete - video is now ready for streaming!")

        except Exception as e:
            self.logger.error(f"MP4 optimization failed: {str(e)}")
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                os.unlink(temp_file)

def check_dependencies():
    """Check and report on critical dependencies."""
    dependencies = []
    
    # Check FFmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            version = result.stdout.split("\n")[0]
            dependencies.append(f"✓ FFmpeg: {version}")
        else:
            dependencies.append("✗ FFmpeg: Not found")
    except FileNotFoundError:
        dependencies.append("✗ FFmpeg: Not found or not in PATH")
    
    # Check NumPy
    if NUMPY_AVAILABLE:
        try:
            dependencies.append(f"✓ NumPy: {np.__version__}")
        except AttributeError:
            dependencies.append(f"✓ NumPy: Available (version unknown)")
    else:
        dependencies.append("✗ NumPy: Not available - install with 'pip install numpy'")
    
    # Check PyAudio
    if PYAUDIO_AVAILABLE:
        try:
            dependencies.append(f"✓ PyAudio: {pyaudio.__version__}")
        except AttributeError:
            dependencies.append(f"✓ PyAudio: Available (version unknown)")
    else:
        dependencies.append("✗ PyAudio: Not available - install with 'pip install pyaudio'")
    
    # Python version
    dependencies.append(f"✓ Python: {sys.version.split()[0]}")
    
    return dependencies

def main():
    """Main entry point."""
    # Print welcome message and version
    print(f"AsciiSymphony Pro v3.0.0")
    print(f"=========================")

    # Check dependencies
    print("\nChecking dependencies:")
    dependencies = check_dependencies()
    for dep in dependencies:
        print(f"  {dep}")
    print()

    # Print usage tips
    print("Tips:")
    print("  • Default resolution: 1280x720 (HD)")
    print("  • Set custom resolution: --width 1920 --height 1080 (Full HD)")
    print("  • Try different modes: --mode neural, --mode spectrum, --mode fractal")
    print("  • Show ASCII preview: --preview")
    print("  • Customize ASCII appearance:")
    print("    - Color themes: --colors thermal|green|blue|red|amber|rainbow|monochrome")
    print("    - Character density: --ascii-density 0.8 (sparse) to 3.0 (very dense)")
    print("    - Higher quality scanlines: --quality high")
    print()

    # Run the application
    app = AsciiSymphony()
    try:
        return_code = app.run()
        if return_code != 0:
            print(f"\nOperation failed with return code {return_code}")
            print("Check logs for more details. Common solutions:")
            print("  • Make sure FFmpeg has libcaca support")
            print("  • Ensure the audio file exists and is a valid format")
            print("  • Check if the output directory is writable")
        return return_code
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        if "FFmpeg" in str(e) and "not found" in str(e).lower():
            print("\nFFmpeg is required but not found. Please install FFmpeg:")
            print("  - Ubuntu/Debian: sudo apt install ffmpeg")
            print("  - macOS: brew install ffmpeg")
            print("  - Windows: Download from https://ffmpeg.org/download.html\n")
        elif "output file does not contain any stream" in str(e).lower():
            print("\nThe visualization couldn't be encoded properly. Possible solutions:")
            print("  - Try a different visualization mode (--mode waves)")
            print("  - Check if your FFmpeg installation supports all required filters")
            print("  - Try a smaller resolution (--width 640 --height 480)")
            print("  - Use a different encoder (--encoder h264)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
