"""
ASCII Symphony Pro GUI
======================
A modular GUI wrapper for the ASCII Symphony Pro script.
Built with Tkinter using MVC architecture for clean separation of concerns.
"""

import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from tkinter.font import Font
import queue

# Import the original ASCII Symphony module
# Assuming it's in the same directory or in the Python path
try:
    # Import the original script as a module
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "asciisymphony", 
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "asciisymphony_pro_python.py")
    )
    asciisymphony = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(asciisymphony)
except Exception as e:
    print(f"Error importing ASCII Symphony module: {e}")
    asciisymphony = None


# ===== Model: Configuration and Settings =====
class Settings:
    """Manages application settings with persistence."""
    DEFAULT_SETTINGS = {
        "theme": "default",
        "font_size": 12,
        "auto_save": False,
        "last_directory": "",
        "width": 80,
        "height": 24,
        "patterns": [],
        "audio_device": "",
        "refresh_rate": 50,  # milliseconds
    }
    
    def __init__(self, config_file="ascii_symphony_settings.json"):
        self.config_file = config_file
        self.settings = self._load_settings()
    
    def _load_settings(self):
        """Load settings from file or use defaults."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return {**self.DEFAULT_SETTINGS, **json.load(f)}
        except Exception as e:
            print(f"Error loading settings: {e}")
        return self.DEFAULT_SETTINGS.copy()
    
    def save_settings(self):
        """Save current settings to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get(self, key, default=None):
        """Get a setting value with optional default."""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set a setting value and save settings."""
        self.settings[key] = value
        self.save_settings()


# ===== Controller: Bridge between GUI and ASCII Symphony =====
class ASCIISymphonyController:
    """Controls the ASCII Symphony functionality from the GUI."""
    
    def __init__(self, app, settings):
        self.app = app
        self.settings = settings
        self.running = False
        self.paused = False
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.worker_thread = None
    
    def start_processing(self, pattern_name=None, **kwargs):
        """Start ASCII processing in a background thread."""
        if self.running and not self.paused:
            return False
        
        if self.paused:
            self.paused = False
            return True
        
        # Prepare parameters for processing
        params = {
            "width": self.settings.get("width"),
            "height": self.settings.get("height"),
            "pattern": pattern_name,
            **kwargs
        }
        
        self.running = True
        self.worker_thread = threading.Thread(
            target=self._processing_worker, 
            args=(params,),
            daemon=True
        )
        self.worker_thread.start()
        return True
    
    def pause_processing(self):
        """Pause the current processing."""
        if self.running and not self.paused:
            self.paused = True
            return True
        return False
    
    def stop_processing(self):
        """Stop the current processing."""
        if self.running:
            self.running = False
            self.paused = False
            if self.worker_thread and self.worker_thread.is_alive():
                self.worker_thread.join(timeout=1.0)
            return True
        return False
    
    def _processing_worker(self, params):
        """Background worker that runs the ASCII processing."""
        try:
            # This is a placeholder for the actual call to the ASCII Symphony functions
            # Adapt this based on the actual API of the original script
            if asciisymphony and hasattr(asciisymphony, 'generate_ascii'):
                while self.running and not self.paused:
                    # Call the actual function from the original script
                    result = asciisymphony.generate_ascii(**params)
                    
                    # Put the result in the queue for the UI to pick up
                    self.result_queue.put(result)
                    
                    # Check for new parameters in the task queue
                    try:
                        new_params = self.task_queue.get_nowait()
                        params.update(new_params)
                        self.task_queue.task_done()
                    except queue.Empty:
                        pass
            else:
                # Fallback with mock data for testing the UI
                import time
                import random
                import string
                
                while self.running and not self.paused:
                    # Generate mock ASCII art for testing
                    width = params.get("width", 80)
                    height = params.get("height", 24)
                    
                    # Simple mock ASCII generation for testing
                    chars = string.ascii_letters + string.digits + string.punctuation
                    mock_result = "\n".join(
                        "".join(random.choice(chars) for _ in range(width))
                        for _ in range(height)
                    )
                    
                    self.result_queue.put(mock_result)
                    time.sleep(0.1)  # Simulate processing time
                    
                    # Check for new parameters
                    try:
                        new_params = self.task_queue.get_nowait()
                        params.update(new_params)
                        self.task_queue.task_done()
                    except queue.Empty:
                        pass
        except Exception as e:
            # Report errors back to the UI
            self.result_queue.put({"error": str(e)})
        finally:
            self.running = False
            self.paused = False
    
    def update_parameters(self, **kwargs):
        """Update parameters for the current processing."""
        if self.running:
            self.task_queue.put(kwargs)
            return True
        return False
    
    def save_output(self, output, file_path):
        """Save the current ASCII output to a file."""
        try:
            with open(file_path, 'w') as f:
                f.write(output)
            return True
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save file: {e}")
            return False
    
    def load_file(self, file_path):
        """Load a configuration or pattern file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load file: {e}")
            return None


# ===== View: The GUI Implementation =====
class ASCIISymphonyGUI(tk.Tk):
    """Main GUI class for ASCII Symphony Pro."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize settings
        self.settings = Settings()
        
        # Initialize the controller
        self.controller = ASCIISymphonyController(self, self.settings)
        
        # Set up the UI
        self.setup_ui()
        
        # Set up periodic tasks
        self.setup_periodic_tasks()
    
    def setup_ui(self):
        """Set up the main user interface."""
        self.title("ASCII Symphony Pro")
        self.geometry("800x600")
        
        # Set up fonts
        self.monospace_font = Font(family="Courier", size=self.settings.get("font_size"))
        
        # Create the main menu
        self.create_menu()
        
        # Create the main frame for content
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs for different functionality
        self.tab_control = ttk.Notebook(main_frame)
        
        # Main visualization tab
        viz_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(viz_tab, text="Visualization")
        self.setup_visualization_tab(viz_tab)
        
        # Settings tab
        settings_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(settings_tab, text="Settings")
        self.setup_settings_tab(settings_tab)
        
        # Help tab
        help_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(help_tab, text="Help")
        self.setup_help_tab(help_tab)
        
        self.tab_control.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_menu(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_project)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Export ASCII", command=self.export_ascii)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_app)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Copy ASCII", command=self.copy_ascii)
        edit_menu.add_command(label="Preferences", command=lambda: self.tab_control.select(1))  # Select Settings tab
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Zoom In", command=self.zoom_in)
        view_menu.add_command(label="Zoom Out", command=self.zoom_out)
        view_menu.add_command(label="Reset Zoom", command=self.reset_zoom)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.config(menu=menubar)
    
    def setup_visualization_tab(self, parent):
        """Set up the main visualization tab."""
        # Split pane - controls on left, display on right
        paned_window = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left side - controls
        control_frame = ttk.Frame(paned_window)
        paned_window.add(control_frame, weight=1)
        
        # Pattern selection
        ttk.Label(control_frame, text="Pattern:").pack(anchor=tk.W, pady=(10, 0))
        
        # Use a Combobox for pattern selection
        self.pattern_var = tk.StringVar()
        patterns = ["Random", "Wave", "Matrix", "Spectrum"]  # Placeholder patterns
        pattern_combo = ttk.Combobox(control_frame, textvariable=self.pattern_var, values=patterns)
        pattern_combo.current(0)
        pattern_combo.pack(fill=tk.X, padx=5, pady=5)
        
        # Width and height settings
        settings_frame = ttk.LabelFrame(control_frame, text="Dimensions")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Width
        width_frame = ttk.Frame(settings_frame)
        width_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(width_frame, text="Width:").pack(side=tk.LEFT)
        self.width_var = tk.IntVar(value=self.settings.get("width"))
        width_spinner = ttk.Spinbox(width_frame, from_=20, to=200, textvariable=self.width_var, width=5)
        width_spinner.pack(side=tk.RIGHT)
        
        # Height
        height_frame = ttk.Frame(settings_frame)
        height_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(height_frame, text="Height:").pack(side=tk.LEFT)
        self.height_var = tk.IntVar(value=self.settings.get("height"))
        height_spinner = ttk.Spinbox(height_frame, from_=10, to=100, textvariable=self.height_var, width=5)
        height_spinner.pack(side=tk.RIGHT)
        
        # Additional parameters (customizable based on pattern)
        params_frame = ttk.LabelFrame(control_frame, text="Parameters")
        params_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Speed control
        speed_frame = ttk.Frame(params_frame)
        speed_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(speed_frame, variable=self.speed_var, from_=0.1, to=5.0, orient=tk.HORIZONTAL)
        speed_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Density control
        density_frame = ttk.Frame(params_frame)
        density_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(density_frame, text="Density:").pack(side=tk.LEFT)
        self.density_var = tk.DoubleVar(value=0.5)
        density_scale = ttk.Scale(density_frame, variable=self.density_var, from_=0.1, to=1.0, orient=tk.HORIZONTAL)
        density_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Character set selection
        charset_frame = ttk.Frame(params_frame)
        charset_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(charset_frame, text="Charset:").pack(side=tk.LEFT)
        self.charset_var = tk.StringVar(value="Standard")
        charset_combo = ttk.Combobox(charset_frame, textvariable=self.charset_var, 
                                    values=["Standard", "Numbers", "Letters", "Symbols", "Custom"])
        charset_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Audio settings if needed
        audio_frame = ttk.LabelFrame(control_frame, text="Audio Input")
        audio_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Audio device selection
        audio_device_frame = ttk.Frame(audio_frame)
        audio_device_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(audio_device_frame, text="Device:").pack(side=tk.LEFT)
        self.audio_device_var = tk.StringVar()
        audio_device_combo = ttk.Combobox(audio_device_frame, textvariable=self.audio_device_var, 
                                        values=["Default", "Microphone", "System Audio"])
        audio_device_combo.current(0)
        audio_device_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Audio sensitivity
        sensitivity_frame = ttk.Frame(audio_frame)
        sensitivity_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(sensitivity_frame, text="Sensitivity:").pack(side=tk.LEFT)
        self.sensitivity_var = tk.DoubleVar(value=0.5)
        sensitivity_scale = ttk.Scale(sensitivity_frame, variable=self.sensitivity_var, from_=0.0, to=1.0, orient=tk.HORIZONTAL)
        sensitivity_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Control buttons
        control_buttons_frame = ttk.Frame(control_frame)
        control_buttons_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.start_button = ttk.Button(control_buttons_frame, text="Start", command=self.start_visualization)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = ttk.Button(control_buttons_frame, text="Pause", command=self.pause_visualization, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_buttons_frame, text="Stop", command=self.stop_visualization, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Right side - display
        display_frame = ttk.Frame(paned_window)
        paned_window.add(display_frame, weight=3)
        
        # ASCII display area with scrollbars
        self.ascii_display = scrolledtext.ScrolledText(display_frame, wrap=tk.NONE, font=self.monospace_font, bg="black", fg="green")
        self.ascii_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.ascii_display.insert(tk.END, "ASCII Symphony Pro\n\nUse the controls on the left to generate visualizations.")
    
    def setup_settings_tab(self, parent):
        """Set up the settings tab."""
        settings_frame = ttk.Frame(parent)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Application settings
        app_settings = ttk.LabelFrame(settings_frame, text="Application Settings")
        app_settings.pack(fill=tk.X, padx=5, pady=5)
        
        # Theme
        theme_frame = ttk.Frame(app_settings)
        theme_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(theme_frame, text="Theme:").pack(side=tk.LEFT)
        self.theme_var = tk.StringVar(value=self.settings.get("theme"))
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, 
                                 values=["default", "light", "dark"])
        theme_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Font size
        font_frame = ttk.Frame(app_settings)
        font_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(font_frame, text="Font Size:").pack(side=tk.LEFT)
        self.font_size_var = tk.IntVar(value=self.settings.get("font_size"))
        font_size_spinner = ttk.Spinbox(font_frame, from_=8, to=24, textvariable=self.font_size_var, width=5)
        font_size_spinner.pack(side=tk.RIGHT)
        
        # Auto-save
        autosave_frame = ttk.Frame(app_settings)
        autosave_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(autosave_frame, text="Auto-save:").pack(side=tk.LEFT)
        self.autosave_var = tk.BooleanVar(value=self.settings.get("auto_save"))
        autosave_check = ttk.Checkbutton(autosave_frame, variable=self.autosave_var)
        autosave_check.pack(side=tk.RIGHT)
        
        # Performance settings
        perf_settings = ttk.LabelFrame(settings_frame, text="Performance Settings")
        perf_settings.pack(fill=tk.X, padx=5, pady=5)
        
        # Refresh rate
        refresh_frame = ttk.Frame(perf_settings)
        refresh_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(refresh_frame, text="Refresh Rate (ms):").pack(side=tk.LEFT)
        self.refresh_var = tk.IntVar(value=self.settings.get("refresh_rate"))
        refresh_spinner = ttk.Spinbox(refresh_frame, from_=10, to=1000, textvariable=self.refresh_var, width=5)
        refresh_spinner.pack(side=tk.RIGHT)
        
        # Save button
        save_button = ttk.Button(settings_frame, text="Save Settings", command=self.save_settings)
        save_button.pack(pady=10)
    
    def setup_help_tab(self, parent):
        """Set up the help tab."""
        help_frame = ttk.Frame(parent)
        help_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Help text
        help_text = scrolledtext.ScrolledText(help_frame, wrap=tk.WORD)
        help_text.pack(fill=tk.BOTH, expand=True)
        
        # Insert help content
        help_content = """# ASCII Symphony Pro Help

## Overview
ASCII Symphony Pro is a tool for generating and visualizing ASCII art patterns, potentially with audio visualization capabilities.

## Getting Started
1. Select a pattern type from the dropdown menu
2. Adjust the width and height as needed
3. Set any additional parameters
4. Click "Start" to begin the visualization

## Controls
- **Start**: Begin the visualization
- **Pause**: Temporarily pause the visualization
- **Stop**: Stop the visualization completely

## Tips
- Adjust the font size in Settings for optimal viewing
- Experiment with different parameters for unique effects
- Use the "Export ASCII" option to save your creations

## Keyboard Shortcuts
- Ctrl+N: New Project
- Ctrl+O: Open File
- Ctrl+S: Save File
- Ctrl+E: Export ASCII
- Ctrl+C: Copy ASCII to clipboard

## Support
For more help or to report issues, please contact support.
"""
        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)  # Make read-only
    
    def setup_periodic_tasks(self):
        """Set up tasks that run periodically."""
        # Check for results from the processing thread
        self.check_result_queue()
        
        # Schedule the next check
        self.after(self.settings.get("refresh_rate"), self.setup_periodic_tasks)
    
    def check_result_queue(self):
        """Check for and process results from the background worker."""
        try:
            while True:
                result = self.controller.result_queue.get_nowait()
                
                # Handle error results
                if isinstance(result, dict) and "error" in result:
                    self.status_var.set(f"Error: {result['error']}")
                    messagebox.showerror("Processing Error", result["error"])
                    self.stop_visualization()
                    continue
                
                # Update the display with the new ASCII content
                if isinstance(result, str):
                    self.update_ascii_display(result)
                
                self.controller.result_queue.task_done()
        except queue.Empty:
            pass
    
    def update_ascii_display(self, content):
        """Update the ASCII display with new content."""
        self.ascii_display.config(state=tk.NORMAL)
        self.ascii_display.delete(1.0, tk.END)
        self.ascii_display.insert(tk.END, content)
        self.ascii_display.config(state=tk.DISABLED)
    
    # === Event handlers and UI actions ===
    
    def start_visualization(self):
        """Start the ASCII visualization."""
        pattern = self.pattern_var.get()
        width = self.width_var.get()
        height = self.height_var.get()
        
        # Update settings
        self.settings.set("width", width)
        self.settings.set("height", height)
        
        # Additional parameters
        params = {
            "speed": self.speed_var.get(),
            "density": self.density_var.get(),
            "charset": self.charset_var.get(),
            "audio_device": self.audio_device_var.get(),
            "sensitivity": self.sensitivity_var.get(),
        }
        
        # Start processing
        success = self.controller.start_processing(pattern, **params)
        
        if success:
            self.status_var.set(f"Running visualization: {pattern}")
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
    
    def pause_visualization(self):
        """Pause the current visualization."""
        if self.controller.pause_processing():
            if self.controller.paused:
                self.status_var.set("Visualization paused")
                self.pause_button.config(text="Resume")
                self.start_button.config(state=tk.NORMAL)
            else:
                self.status_var.set("Visualization resumed")
                self.pause_button.config(text="Pause")
                self.start_button.config(state=tk.DISABLED)
    
    def stop_visualization(self):
        """Stop the current visualization."""
        if self.controller.stop_processing():
            self.status_var.set("Visualization stopped")
            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED, text="Pause")
            self.stop_button.config(state=tk.DISABLED)
    
    def new_project(self):
        """Create a new project."""
        if self.controller.running:
            if not messagebox.askyesno("Confirm", "Stop the current visualization and start a new project?"):
                return
            self.stop_visualization()
        
        self.ascii_display.config(state=tk.NORMAL)
        self.ascii_display.delete(1.0, tk.END)
        self.ascii_display.insert(tk.END, "New project started. Configure and press Start.")
        self.ascii_display.config(state=tk.DISABLED)
        
        # Reset controls to defaults
        self.pattern_var.set("Random")
        self.width_var.set(self.settings.get("width"))
        self.height_var.set(self.settings.get("height"))
        self.speed_var.set(1.0)
        self.density_var.set(0.5)
        self.charset_var.set("Standard")
        
        self.status_var.set("New project created")
    
    def open_file(self):
        """Open a configuration or saved pattern file."""
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[("ASCII Symphony Files", "*.json;*.ascii"), ("All Files", "*.*")],
            initialdir=self.settings.get("last_directory")
        )
        
        if file_path:
            self.settings.set("last_directory", os.path.dirname(file_path))
            
            # Load the file
            data = self.controller.load_file(file_path)
            if data:
                # Apply loaded settings
                # This depends on the file format - adapt as needed
                if "pattern" in data:
                    self.pattern_var.set(data["pattern"])
                if "width" in data:
                    self.width_var.set(data["width"])
                if "height" in data:
                    self.height_var.set(data["height"])
                # ... other parameters
                
                self.status_var.set(f"Loaded file: {os.path.basename(file_path)}")
    
    def save_file(self):
        """Save the current configuration."""
        # Implement save functionality
        pass
    
    def save_file_as(self):
        """Save the current configuration with a new name."""
        file_path = filedialog.asksaveasfilename(
            title="Save As",
            filetypes=[("ASCII Symphony Files", "*.json"), ("All Files", "*.*")],
            defaultextension=".json",
            initialdir=self.settings.get("last_directory")
        )
        
        if file_path:
            self.settings.set("last_directory", os.path.dirname(file_path))
            
            # Collect current settings
            config = {
                "pattern": self.pattern_var.get(),
                "width": self.width_var.get(),
                "height": self.height_var.get(),
                "speed": self.speed_var.get(),
                "density": self.density_var.get(),
                "charset": self.charset_var.get(),
                "audio_device": self.audio_device_var.get(),
                "sensitivity": self.sensitivity_var.get(),
            }
            
            # Save to file
            try:
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=2)
                self.status_var.set(f"Saved configuration to: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save file: {e}")
    
    def export_ascii(self):
        """Export the current ASCII art to a text file."""
        if not self.ascii_display.get(1.0, tk.END).strip():
            messagebox.showinfo("Export ASCII", "No ASCII content to export.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export ASCII",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            defaultextension=".txt",
            initialdir=self.settings.get("last_directory")
        )
        
        if file_path:
            self.settings.set("last_directory", os.path.dirname(file_path))
            
            # Get the current ASCII content
            ascii_content = self.ascii_display.get(1.0, tk.END)
            
            # Save to file
            self.controller.save_output(ascii_content, file_path)
            self.status_var.set(f"Exported ASCII to: {os.path.basename(file_path)}")
    
    def copy_ascii(self):
        """Copy the current ASCII art to clipboard."""
        ascii_content = self.ascii_display.get(1.0, tk.END)
        self.clipboard_clear()
        self.clipboard_append(ascii_content)
        self.status_var.set("ASCII copied to clipboard")
    
    def save_settings(self):
        """Save the current application settings."""
        self.settings.set("theme", self.theme_var.get())
        self.settings.set("font_size", self.font_size_var.get())
        self.settings.set("auto_save", self.autosave_var.get())
        self.settings.set("refresh_rate", self.refresh_var.get())
        
        # Apply settings immediately
        self.apply_settings()
        
        self.status_var.set("Settings saved")
    
    def apply_settings(self):
        """Apply the current settings to the UI."""
        # Update font
        font_size = self.settings.get("font_size")
        self.monospace_font.configure(size=font_size)
        
        # Update theme (placeholder - would need theme implementation)
        theme = self.settings.get("theme")
        # self.apply_theme(theme)
        
        # Update refresh rate for periodic tasks
        # Already handled by setup_periodic_tasks
    
    def zoom_in(self):
        """Increase the font size of the ASCII display."""
        current_size = self.monospace_font.cget("size")
        self.monospace_font.configure(size=current_size+2)
        self.font_size_var.set(current_size+2)
    
    def zoom_out(self):
        """Decrease the font size of the ASCII display."""
        current_size = self.monospace_font.cget("size")
        if current_size > 6:  # Minimum readable size
            self.monospace_font.configure(size=current_size-2)
            self.font_size_var.set(current_size-2)
    
    def reset_zoom(self):
        """Reset the font size to default."""
        default_size = 12
        self.monospace_font.configure(size=default_size)
        self.font_size_var.set(default_size)
    
    def show_documentation(self):
        """Show the full documentation."""
        # Open documentation in a new window or web browser
        messagebox.showinfo("Documentation", "Documentation would open in a browser.")
    
    def show_about(self):
        """Show information about the application."""
        about_text = "ASCII Symphony Pro\n\n"
        about_text += "A tool for creating and visualizing ASCII art patterns.\n\n"
        about_text += "Version: 1.0\n"
        
        messagebox.showinfo("About ASCII Symphony Pro", about_text)
    
    def quit_app(self):
        """Quit the application with confirmation."""
        if self.controller.running:
            if not messagebox.askyesno("Confirm Exit", "Stop the current visualization and exit?"):
                return
            self.controller.stop_processing()
        
        self.destroy()


# === Main entry point ===
def main():
    app = ASCIISymphonyGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
