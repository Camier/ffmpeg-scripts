"""
AsciiSymphony Pro: Enterprise-Grade ASCII Art Audio Visualizer
Python Implementation v3.0.0
This Python implementation provides all the functionality of the original
AsciiSymphony Pro Bash script with improved structure, error handling,
and extensibility.
Features:

GPU-accelerated rendering
Real-time audio input processing
Advanced visualization modes
User preset management system
Adaptive quality control
Intelligent error recovery
Cross-platform support
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
from enum import Enum, auto
from pathlib import Path

# Conditionally import numpy and pyaudio - these may not be available on all systems
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    # Define a minimal replacement for commonly used numpy functions
    class NumpyShim:
        """A minimal shim providing basic numpy functionality when numpy is not available."""

        @staticmethod
        def frombuffer(buffer, dtype=None):
            """Simple replacement for numpy's frombuffer function."""
            return buffer

        @staticmethod
        def array(data, dtype=None):
            """Simple replacement for numpy.array."""
            if isinstance(data, (list, tuple)):
                return data
            return [data]

        @staticmethod
        def zeros(shape, dtype=None):
            """Create an array of zeros."""
            if isinstance(shape, (list, tuple)):
                size = 1
                for dim in shape:
                    size *= dim
            else:
                size = shape
            return [0] * size

        @staticmethod
        def linspace(start, stop, num=50):
            """Create a linear space between start and stop with num points."""
            step = (stop - start) / (num - 1)
            return [start + step * i for i in range(num)]

        @staticmethod
        def arange(start, stop=None, step=1):
            """Create a range similar to numpy.arange."""
            if stop is None:
                stop = start
                start = 0
            return list(range(start, stop, step))

        @staticmethod
        def abs(x):
            """Absolute value, element-wise."""
            if isinstance(x, (list, tuple)):
                return [abs(i) for i in x]
            return abs(x)

        @staticmethod
        def mean(a, axis=None):
            """Calculate the mean of array elements."""
            if not a:
                return 0
            if isinstance(a, (list, tuple)):
                return sum(a) / len(a)
            return a

        @staticmethod
        def max(a, axis=None):
            """Return the maximum of an array or maximum along an axis."""
            if isinstance(a, (list, tuple)):
                if not a:
                    return 0
                return max(a)
            return a

        class fft:
            """Minimal FFT shim."""
            @staticmethod
            def rfft(x):
                """Return a dummy frequency spectrum."""
                if isinstance(x, (list, tuple)):
                    size = len(x) // 2 + 1
                    return [0] * size
                return [0]

    # Replace numpy with our shim
    np = NumpyShim()

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

# ============================================================================
# CONFIGURATION
# ============================================================================
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
            'charset': 'unicode',
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

# ============================================================================
# LOGGING
# ============================================================================
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

# ============================================================================
# ERROR HANDLING
# ============================================================================
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

# ============================================================================
# AUDIO DEVICE MANAGEMENT
# ============================================================================
class AudioDeviceManager:
    """Manages audio device detection and selection across platforms."""
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("asciisymphony.audio")
        self.devices = []
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

        if PYAUDIO_AVAILABLE:
            # Use PyAudio for more reliable cross-platform device detection
            self._detect_devices_pyaudio()
        else:
            # Use system-specific FFmpeg-compatible detection methods
            self._detect_devices_ffmpeg()

        self.logger.info(f"Found {len(self.devices)} audio input devices")

        # If no devices were detected, add a default device
        if not self.devices:
            self._add_default_device()

        return self.devices

    def _detect_devices_pyaudio(self):
        """Detect audio devices using PyAudio."""
        try:
            pa = pyaudio.PyAudio()

            try:
                device_count = pa.get_device_count()
                device_found = False

                for i in range(device_count):
                    try:
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
                            device_found = True
                    except Exception as e:
                        self.logger.warning(f"Error getting PyAudio device info for index {i}: {str(e)}")

                # If no input devices found, try to at least add the default device
                if not device_found:
                    try:
                        default_info = pa.get_default_input_device_info()
                        if default_info:
                            self.devices.append({
                                'index': default_info.get('index', 0),
                                'name': default_info.get('name', 'Default Input'),
                                'channels': default_info.get('maxInputChannels', 2),
                                'sample_rate': int(default_info.get('defaultSampleRate', 44100)),
                                'system': self.system
                            })
                    except:
                        self.logger.warning("Could not get default input device info")
            finally:
                pa.terminate()

        except Exception as e:
            self.logger.error(f"Error initializing PyAudio: {str(e)}")
            # If PyAudio fails completely, fall back to system-specific methods
            self._detect_devices_ffmpeg()

    def _detect_devices_ffmpeg(self):
        """Detect audio devices using system-specific tools."""
        if self.system == "pulse":
            self._detect_devices_pulse()
        elif self.system == "alsa":
            self._detect_devices_alsa()
        elif self.system == "avfoundation":
            self._detect_devices_avfoundation()
        elif self.system == "dshow":
            self._detect_devices_dshow()
        else:
            # Add a default device as fallback
            self._add_default_device()

    def _detect_devices_pulse(self):
        """Detect PulseAudio input devices."""
        try:
            # Use pactl to list sources
            result = subprocess.run(
                ["pactl", "list", "sources"],
                capture_output=True,
                text=True,
                check=True
            )

            source_index = None
            source_name = None
            channels = 2

            for line in result.stdout.splitlines():
                line = line.strip()

                if line.startswith("Source #"):
                    # Start of a new source
                    if source_index is not None and source_name is not None:
                        self.devices.append({
                            'index': source_index,
                            'name': source_name,
                            'channels': channels,
                            'sample_rate': 44100,
                            'system': 'pulse'
                        })

                    source_index = int(line.split('#')[1])
                    source_name = None
                    channels = 2

                elif "Name:" in line:
                    source_name = line.split("Name:")[1].strip()

                elif "Channels:" in line:
                    try:
                        ch_str = line.split("Channels:")[1].strip()
                        if "mono" in ch_str.lower():
                            channels = 1
                        elif "stereo" in ch_str.lower():
                            channels = 2
                        elif "surround" in ch_str.lower():
                            channels = 6
                        else:
                            # Try to parse the number
                            ch_match = re.search(r'(\d+)', ch_str)
                            if ch_match:
                                channels = int(ch_match.group(1))
                    except:
                        channels = 2

            # Add last device if there was one
            if source_index is not None and source_name is not None:
                self.devices.append({
                    'index': source_index,
                    'name': source_name,
                    'channels': channels,
                    'sample_rate': 44100,
                    'system': 'pulse'
                })

        except (subprocess.SubprocessError, ValueError, IndexError) as e:
            self.logger.error(f"Error detecting PulseAudio devices: {str(e)}")
            self._add_default_device()

    def _detect_devices_alsa(self):
        """Detect ALSA input devices."""
        try:
            # Use arecord to list devices
            result = subprocess.run(
                ["arecord", "-L"],
                capture_output=True,
                text=True,
                check=True
            )

            current_index = 0
            for line in result.stdout.splitlines():
                line = line.strip()

                # Skip headers, comments and empty lines
                if not line or line.startswith(' ') or line.startswith('#'):
                    continue

                # Device names are at the beginning of lines
                self.devices.append({
                    'index': current_index,
                    'name': line,
                    'channels': 2,
                    'sample_rate': 44100,
                    'system': 'alsa'
                })
                current_index += 1

        except (subprocess.SubprocessError, ValueError) as e:
            self.logger.error(f"Error detecting ALSA devices: {str(e)}")
            self._add_default_device()

    def _detect_devices_avfoundation(self):
        """Detect AVFoundation (macOS) input devices."""
        try:
            # Use ffmpeg to list devices
            result = subprocess.run(
                ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                capture_output=True,
                text=True
            )

            current_index = 0
            reading_audio = False

            for line in result.stderr.splitlines():
                line = line.strip()

                if "AVFoundation audio devices" in line:
                    reading_audio = True
                    continue

                if "AVFoundation video devices" in line:
                    reading_audio = False
                    continue

                if reading_audio and re.search(r'\[\d+\]', line):
                    # Extract device info
                    match = re.search(r'\[(\d+)\] (.+)', line)
                    if match:
                        device_index = int(match.group(1))
                        device_name = match.group(2)

                        self.devices.append({
                            'index': device_index,
                            'name': device_name,
                            'channels': 2,
                            'sample_rate': 44100,
                            'system': 'avfoundation'
                        })

        except (subprocess.SubprocessError, ValueError) as e:
            self.logger.error(f"Error detecting AVFoundation devices: {str(e)}")
            self._add_default_device()

    def _detect_devices_dshow(self):
        """Detect DirectShow (Windows) input devices."""
        try:
            # Use ffmpeg to list devices
            result = subprocess.run(
                ["ffmpeg", "-f", "dshow", "-list_devices", "true", "-i", "dummy"],
                capture_output=True,
                text=True
            )

            current_index = 0
            reading_audio = False

            for line in result.stderr.splitlines():
                line = line.strip()

                if "DirectShow audio devices" in line:
                    reading_audio = True
                    continue

                if "DirectShow video devices" in line:
                    reading_audio = False
                    continue

                if reading_audio and "Alternative name" not in line:
                    # Extract device info
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        device_name = match.group(1)

                        self.devices.append({
                            'index': current_index,
                            'name': device_name,
                            'channels': 2,
                            'sample_rate': 44100,
                            'system': 'dshow'
                        })
                        current_index += 1

        except (subprocess.SubprocessError, ValueError) as e:
            self.logger.error(f"Error detecting DirectShow devices: {str(e)}")
            self._add_default_device()

    def _add_default_device(self):
        """Add a default device as fallback."""
        self.logger.warning("No audio devices detected, adding fallback default device")

        # System-specific default device
        if self.system == "pulse":
            default_name = "default"
        elif self.system == "alsa":
            default_name = "hw:0,0"
        elif self.system == "avfoundation":
            default_name = "Default"
        elif self.system == "dshow":
            default_name = "audio=Microphone"
        else:
            default_name = "default"

        self.devices.append({
            'index': 0,
            'name': default_name,
            'channels': 2,
            'sample_rate': 44100,
            'system': self.system
        })

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

class LiveAudioProcessor:
    """Processes live audio input for visualization."""
    def __init__(self, config, device_manager):
        self.config = config
        self.device_manager = device_manager
        self.logger = logging.getLogger("asciisymphony.audio")
        self.audio_queue = queue.Queue(maxsize=100)
        self.stop_event = threading.Event()
        self.audio_thread = None

        if not PYAUDIO_AVAILABLE:
            self.logger.warning("PyAudio not available. Live audio capture will use FFmpeg instead.")

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
        if not PYAUDIO_AVAILABLE:
            self._ffmpeg_audio_capture_thread(device)
            return

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

    def _ffmpeg_audio_capture_thread(self, device):
        """Alternative audio capture using FFmpeg."""
        # Get FFmpeg input arguments
        ffmpeg_args = self.get_ffmpeg_input_args(device)

        # Set output format to raw PCM
        ffmpeg_args.extend([
            '-f', 's16le',    # 16-bit signed little endian
            '-ar', str(self.config.get('sample_rate', 44100)),
            '-ac', str(self.config.get('channels', 2)),
            '-'              # Output to stdout
        ])

        # Start FFmpeg process
        cmd = ['ffmpeg'] + ffmpeg_args
        self.logger.info(f"Starting FFmpeg audio capture: {' '.join(cmd)}")

        # Use universal_newlines=False to get binary output
        ffmpeg_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1024 * 8,  # Buffer size
            universal_newlines=False
        )

        buffer_size = int(self.config.get('buffer_size', 1024))
        bytes_per_sample = 2  # 16-bit = 2 bytes
        channels = int(self.config.get('channels', 2))
        chunk_size = buffer_size * bytes_per_sample * channels

        try:
            # Read audio data from FFmpeg output
            while not self.stop_event.is_set():
                try:
                    audio_data = ffmpeg_process.stdout.read(chunk_size)
                    if not audio_data:
                        # If we've reached EOF, restart the stream if possible
                        if ffmpeg_process.poll() is not None:
                            self.logger.warning("FFmpeg process ended, restarting...")
                            ffmpeg_process.terminate()
                            ffmpeg_process = subprocess.Popen(
                                cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                bufsize=1024 * 8,
                                universal_newlines=False
                            )
                            continue
                        else:
                            break

                    # Convert to data structure for processing
                    if NUMPY_AVAILABLE:
                        try:
                            audio_array = np.frombuffer(audio_data, dtype=np.int16)
                        except Exception as np_err:
                            self.logger.warning(f"NumPy error: {str(np_err)}, falling back to raw data")
                            audio_array = audio_data
                    else:
                        # Create a basic structure that mimics some numpy array behaviors
                        audio_array = self._create_audio_array_shim(audio_data)

                    # Put in queue if not full
                    if not self.audio_queue.full():
                        self.audio_queue.put(audio_array, block=False)

                except Exception as e:
                    self.logger.error(f"Error reading FFmpeg audio: {str(e)}")
                    time.sleep(0.1)  # Prevent tight loop on error

        finally:
            # Clean up
            try:
                ffmpeg_process.terminate()
                ffmpeg_process.wait(timeout=2.0)
            except:
                ffmpeg_process.kill()

    def _create_audio_array_shim(self, audio_data):
        """Create a simple shim for audio data when NumPy isn't available."""
        # This provides a minimal object with some properties similar to numpy arrays
        class AudioArrayShim:
            def __init__(self, data):
                self.data = data
                self.shape = (len(data) // 2,)  # Assume 16-bit samples

            def __len__(self):
                return self.shape[0]

            def mean(self):
                # Crude approximation of mean for 16-bit PCM data
                if not self.data:
                    return 0
                # Sample a few values for efficiency
                samples = min(100, len(self.data) // 2)
                total = 0
                for i in range(0, len(self.data), len(self.data) // samples):
                    if i + 1 < len(self.data):
                        # Convert two bytes to signed 16-bit int
                        value = int.from_bytes(self.data[i:i+2], byteorder='little', signed=True)
                        total += value
                return total / samples

            def max(self):
                # Crude approximation of max for 16-bit PCM data
                if not self.data:
                    return 0
                # Sample values for efficiency
                samples = min(100, len(self.data) // 2)
                max_val = -32768  # Minimum 16-bit signed value
                for i in range(0, len(self.data), len(self.data) // samples):
                    if i + 1 < len(self.data):
                        value = int.from_bytes(self.data[i:i+2], byteorder='little', signed=True)
                        max_val = max(max_val, value)
                return max_val

            def min(self):
                # Crude approximation of min for 16-bit PCM data
                if not self.data:
                    return 0
                # Sample values for efficiency
                samples = min(100, len(self.data) // 2)
                min_val = 32767  # Maximum 16-bit signed value
                for i in range(0, len(self.data), len(self.data) // samples):
                    if i + 1 < len(self.data):
                        value = int.from_bytes(self.data[i:i+2], byteorder='little', signed=True)
                        min_val = min(min_val, value)
                return min_val

            def __getitem__(self, idx):
                if isinstance(idx, slice):
                    # Handle slice notation
                    start = idx.start if idx.start is not None else 0
                    stop = idx.stop if idx.stop is not None else len(self.data) // 2
                    step = idx.step if idx.step is not None else 1

                    result = []
                    for i in range(start, stop, step):
                        if i*2+1 < len(self.data):
                            result.append(int.from_bytes(self.data[i*2:i*2+2],
                                                        byteorder='little', signed=True))
                    return result
                else:
                    # Handle integer indexing
                    if idx*2+1 < len(self.data):
                        return int.from_bytes(self.data[idx*2:idx*2+2],
                                             byteorder='little', signed=True)
                    return 0

        return AudioArrayShim(audio_data)

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

        if PYAUDIO_AVAILABLE:
            # Use PyAudio if available
            return self._create_temp_wav_pyaudio(temp_filename, device, duration, sample_rate, channels, buffer_size)
        else:
            # Use FFmpeg fallback
            return self._create_temp_wav_ffmpeg(temp_filename, device, duration, sample_rate, channels)

    def _create_temp_wav_pyaudio(self, temp_filename, device, duration, sample_rate, channels, buffer_size):
        """Create a temporary WAV file using PyAudio."""
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
            self.logger.info(f"Recording {duration} seconds of audio to {temp_filename} using PyAudio")

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

    def _create_temp_wav_ffmpeg(self, temp_filename, device, duration, sample_rate, channels):
        """Create a temporary WAV file using FFmpeg."""
        self.logger.info(f"Recording {duration} seconds of audio to {temp_filename} using FFmpeg")

        # Get FFmpeg input arguments
        ffmpeg_args = self.get_ffmpeg_input_args(device)

        # Add output arguments for WAV file
        record_args = [
            'ffmpeg',
            '-v', 'error'
        ] + ffmpeg_args + [
            '-t', str(duration),  # Duration in seconds
            '-ar', str(sample_rate),
            '-ac', str(channels),
            '-f', 'wav',
            temp_filename
        ]

        try:
            # Start recording
            self.logger.info(f"Running FFmpeg: {' '.join(record_args)}")
            subprocess.run(record_args, check=True)

            # Verify file was created
            if not os.path.exists(temp_filename):
                raise RuntimeError(f"Failed to create WAV file: {temp_filename}")

            # Get file size
            file_size = os.path.getsize(temp_filename)
            self.logger.info(f"Recorded {file_size} bytes to {temp_filename}")

            if file_size < 1000:  # Very small file suggests an error
                self.logger.warning(f"Warning: Recorded WAV file is very small ({file_size} bytes)")

            return temp_filename

        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg recording error: {str(e)}")
            # Create a silent WAV file as fallback
            return self._create_silent_wav(temp_filename, duration, sample_rate, channels)

    def _create_silent_wav(self, temp_filename, duration, sample_rate, channels):
        """Create a silent WAV file as fallback."""
        self.logger.warning(f"Creating silent WAV file as fallback: {temp_filename}")

        # Create WAV file
        wf = wave.open(temp_filename, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)

        # Generate silence (all zeros)
        frames_count = int(duration * sample_rate)
        silence_data = b'\x00\x00' * frames_count * channels

        # Write silence to file
        wf.writeframes(silence_data)
        wf.close()

        return temp_filename

    def get_ffmpeg_input_args(self, device_id=None):
        """Get FFmpeg input arguments for live audio capture."""
        device = self.device_manager.get_device_by_id(device_id)
        
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
        if device['system'] == 'pulse':
            args.extend(['-f', 'pulse', '-i', str(device['index'])])
        elif device['system'] == 'alsa':
            args.extend(['-f', 'alsa', '-i', f"hw:{device['index']}"])
        elif device['system'] == 'avfoundation':
            args.extend(['-f', 'avfoundation', '-i', f":{device['index']}"])
        elif device['system'] == 'dshow':
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

# ============================================================================
# PRESET MANAGEMENT
# ============================================================================
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
            "charset": "unicode",
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

# ============================================================================
# VISUALIZATION
# ============================================================================
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
        return f"[0:a]showwaves=s={width}x{height}:mode=line[waves];" \
               f"[0:a]showspectrum=s={width}x{height}:mode=combined[spectrum];" \
               f"[waves][spectrum]blend=all_mode=addition,format=rgb24"

class EdgeMode(VisualizationMode):
    """Edge-detected audio visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        return f"[0:a]showcqt=s={width}x{height}[cqt];" \
               f"[cqt]edgedetect=low=0.1:high=0.4,format=rgb24"

class KaleidoscopeMode(VisualizationMode):
    """Kaleidoscope effect on spectrum."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        return f"[0:a]showspectrum=s={width}x{height}:slide=replace:mode=combined,format=yuv420p[vis];" \
               f"[vis]kaleidoscope=pattern=1:angle=0,format=rgb24"

class NeuralMode(VisualizationMode):
    """Neural network-inspired multi-band visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        height_third = height // 3
        
        return f"[0:a]asplit=3[bass][mid][high]," \
               f"[bass]bandpass=f=100:width_type=h:w=200[filtered_bass]," \
               f"[mid]bandpass=f=1000:width_type=h:w=800[filtered_mid]," \
               f"[high]highpass=f=4000[filtered_high]," \
               f"[filtered_bass]showwaves=s={width}x{height_third}:mode=cline:colors=0x00ffff[wave_bass]," \
               f"[filtered_mid]showspectrum=s={width}x{height_third}:slide=scroll:mode=combined:color=rainbow[spec_mid]," \
               f"[filtered_high]showcqt=s={width}x{height_third}:count=8:gamma=5[cqt_high]," \
               f"[wave_bass][spec_mid][cqt_high]vstack=inputs=3," \
               f"hue='h=t/20':s='1+sin(t/10)/4'," \
               f"boxblur=10:enable='if(eq(mod(t,4),0),1,0)',format=rgb24"

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
        
        return f"[0:a]asplit=2[a1][a2]," \
               f"[a1]showwaves=s={width}x{height}:mode=cline:draw=full:colors=0xffffff[bg]," \
               f"[a2]avectorscope=s={width}x{height}:zoom=1.5:draw=full[fg]," \
               f"[bg][fg]blend=all_mode=screen:all_opacity=0.8,format=yuv422p," \
               f"drawtext=text='AUDIO':fontsize=w/5:x=(w-text_w)/2:y=(h-text_h)/2:" \
               f"fontcolor=ffffff@0.8:enable='between(mod(t,2),0,0.3)'," \
               f"drawtext=text='SYMPHONY':fontsize=w/8:x=(w-text_w)/2:y=(h-text_h)/2+h/4:" \
               f"fontcolor=00ffff@0.6:enable='between(mod(t,2),0.3,0.6)'," \
               f"drawtext=textfile={path}:reload=1:fontsize='w/20*sin(t)+w/10':" \
               f"x='w/2+w/4*sin(t/2)':y='h/2+h/4*cos(t/2)':fontcolor=ffffff@0.7," \
               f"format=rgb24"

class ParticlesMode(VisualizationMode):
    """Particle system visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        
        return f"[0:a]asplit=2[a][b]," \
               f"[a]showwaves=s={width}x{height}:mode=cline:rate=60[waves]," \
               f"[b]showspectrum=s={width}x{height}:slide=scroll:mode=combined[spectrum]," \
               f"[waves][spectrum]blend=all_mode=screen:all_opacity=0.5," \
               f"format=rgba," \
               f"split=3[s1][s2][s3]," \
               f"[s1]rotate=angle='t/10':fillcolor=0x00000000[r1]," \
               f"[s2]rotate=angle='-t/15':fillcolor=0x00000000[r2]," \
               f"[s3]rotate=angle='sin(t)*PI/4':fillcolor=0x00000000[r3]," \
               f"[r1][r2][r3]blend=all_mode=lighten,format=rgb24"

class FractalMode(VisualizationMode):
    """Fractal-inspired recursive visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        
        return f"[0:a]showcqt=s={width}x{height}:count=12:" \
               f"attack=0.5:gamma=4:sono_v=fim," \
               f"split=4[q1][q2][q3][q4]," \
               f"[q1]crop=iw/2:ih/2:0:0,scale={width}x{height}[c1]," \
               f"[q2]crop=iw/2:ih/2:iw/2:0,scale={width}x{height}[c2]," \
               f"[q3]crop=iw/2:ih/2:0:ih/2,scale={width}x{height}[c3]," \
               f"[q4]crop=iw/2:ih/2:iw/2:ih/2,scale={width}x{height}[c4]," \
               f"[c1][c2]hstack[top]," \
               f"[c3][c4]hstack[bottom]," \
               f"[top][bottom]vstack,hue='h=t/15',format=rgb24"

class VortexMode(VisualizationMode):
    """Rotating audio vortex visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        
        return f"[0:a]showspectrum=s={width}x{height}:slide=replace:mode=combined[spec]," \
               f"[spec]rotate=angle='t*2':fillcolor=black@0.5," \
               f"hue=h='2*PI*t':s=1.5,format=rgb24"

class SpectrosynthMode(VisualizationMode):
    """Multi-band spectral synthesis visualization."""
    def get_filter_chain(self):
        width = self.config.get('width')
        height = self.config.get('height')
        
        return f"[0:a]asplit=3[main][spec][wave]," \
               f"[main]showfreqs=s={width}x{height//3}:scale=log:win_size=2048[freqs]," \
               f"[spec]showspectrum=s={width}x{height//3}:mode=combined:slide=scroll[spectrum]," \
               f"[wave]showwaves=s={width}x{height//3}:mode=p2p:split_channels=1[waves]," \
               f"[freqs][spectrum][waves]vstack=inputs=3,format=rgb24"

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

# ============================================================================
# RENDERING
# ============================================================================
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
            '-color', 'full',
            '-charset', self.config.get('charset', 'unicode'),
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
        if self.ffmpeg_process.poll() is not None and self.ffmpeg_process.returncode != 0:
            stderr = self.ffmpeg_process.stderr.read()
            raise RuntimeError(f"FFmpeg error: {stderr}")
        
        return self.ffmpeg_process.returncode

class FileRenderer(Renderer):
    """Renderer that outputs video file."""
    def render(self, input_stream, output_file):
        """Render the visualization to a file."""
        if not output_file:
            raise ValueError("Output file required for file renderer")
        
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
        
        # Add filter chain
        cmd.extend([
            '-lavfi', filter_chain,
            '-f', 'caca',
            '-color', 'full',
            '-charset', self.config.get('charset', 'unicode'),
            '-algorithm', self.config.get('dither', 'fstein'),
            '-'
        ])
        
        # Start FFmpeg process for the ASCII art generation
        self.logger.info(f"Generating ASCII art with FFmpeg")
        
        with tempfile.NamedTemporaryFile(suffix='.rgb', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        try:
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Process the raw output and write to temp file
            with open(temp_filename, 'wb') as f:
                for chunk in iter(lambda: self.ffmpeg_process.stdout.read(4096), b''):
                    f.write(chunk)
            
            if self.ffmpeg_process.wait() != 0:
                stderr = self.ffmpeg_process.stderr.read()
                raise RuntimeError(f"FFmpeg error: {stderr}")
            
            # Get encoder settings
            encoder_args = self._get_encoder_settings()
            
            # Process the temp file to create the final output
            self.logger.info(f"Encoding final video to {output_file}")
            
            # Build second FFmpeg command for encoding
            cmd2 = [
                'ffmpeg',
                '-v', 'warning',
                '-f', 'rawvideo',
                '-pix_fmt', 'rgb24',
                '-s', f"{self.config.get('width')}x{self.config.get('height')}",
                '-i', temp_filename
            ]
            
            # Add encoder settings
            cmd2.extend(shlex.split(encoder_args))
            
            # Add metadata and output file
            cmd2.extend([
                '-metadata', 'title="AsciiSymphony Pro"',
                '-movflags', '+faststart',
                output_file
            ])
            
            # Run second FFmpeg process
            result = subprocess.run(cmd2, check=True)
            
            return result.returncode
        
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_filename)
            except:
                pass

    def _get_encoder_settings(self):
        """Get encoder settings based on configuration."""
        encoder = self.config.get('encoder', 'h264')
        
        if encoder == 'h264':
            return "-c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p"
        elif encoder == 'vp9':
            return "-c:v libvpx-vp9 -crf 30 -b:v 0 -pix_fmt yuv420p"
        elif encoder == 'gif':
            return '-filter_complex "[0:v]split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -f gif'
        else:
            # Default to h264
            return "-c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p"

# ============================================================================
# MAIN APPLICATION
# ============================================================================
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
            
            # Create renderer
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
            # Use FFmpeg to optimize MP4
            cmd = [
                'ffmpeg', 
                '-v', 'error', 
                '-i', output_file, 
                '-c', 'copy', 
                '-movflags', 'faststart', 
                temp_file
            ]
            
            result = subprocess.run(cmd, check=True)
            
            # Replace original with optimized version
            os.replace(temp_file, output_file)
            
            self.logger.info("MP4 optimization complete")
            
        except Exception as e:
            self.logger.error(f"MP4 optimization failed: {str(e)}")
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                os.unlink(temp_file)

def main():
    """Main entry point."""
    app = AsciiSymphony()
    try:
        return app.run()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())