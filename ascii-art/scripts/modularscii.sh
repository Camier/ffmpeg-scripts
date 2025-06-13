#!/bin/bash

# AsciiSymphony: Advanced Modular ASCII Art Audio Visualizer
# Usage: ./ascii_symphony.sh input.flac output.mp4 [options]

#==========================================
# CONFIGURATION AND DEFAULT SETTINGS
#==========================================

# Default visualization settings
VIZ_WIDTH=640
VIZ_HEIGHT=480
VIZ_MODE="adaptive"  # Options: adaptive, spectrum, waveform, combined
COLOR_SCHEME="rainbow"  # Options: rainbow, thermal, matrix, grayscale, custom
CHARSET="blocks"  # Options: ascii, blocks, shades
DITHER_ALGO="fstein"  # Options: fstein, ordered4, random
EFFECT_LEVEL="medium"  # Options: minimal, medium, intense

# Default output settings
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
OUTPUT_WIDTH=1280
OUTPUT_HEIGHT=720
VIDEO_QUALITY="high"  # Options: draft, normal, high, ultra

# Processing settings
TEMP_DIR=""
DEBUG=false
INPUT=""
OUTPUT=""

#==========================================
# FUNCTIONS
#==========================================

# Show usage information
show_usage() {
    echo "AsciiSymphony: Advanced Modular ASCII Art Audio Visualizer"
    echo "Usage: $0 input.flac output.mp4 [options]"
    echo ""
    echo "Options:"
    echo "  --mode MODE         Visualization mode (adaptive, spectrum, waveform, combined)"
    echo "  --colors SCHEME     Color scheme (rainbow, thermal, matrix, grayscale, custom)"
    echo "  --charset SET       Character set (ascii, blocks, shades)"
    echo "  --dither ALGO       Dithering algorithm (fstein, ordered4, random)"
    echo "  --effects LEVEL     Effect intensity (minimal, medium, intense)"
    echo "  --width WIDTH       Visualization width"
    echo "  --height HEIGHT     Visualization height"
    echo "  --quality LEVEL     Output video quality (draft, normal, high, ultra)"
    echo "  --debug             Enable debug mode"
    echo "  --help              Show this help message"
}

# Check for required dependencies
check_dependencies() {
    local missing_deps=false
    
    # Check for ffmpeg with libcaca support
    if ! ffmpeg -version | grep -q "enable-libcaca"; then
        echo "Error: FFmpeg is not installed or does not have libcaca support"
        missing_deps=true
    fi
    
    # Check for bc (used for calculations)
    if ! command -v bc &> /dev/null; then
        echo "Error: bc is not installed"
        missing_deps=true
    fi
    
    # Check for font file
    if [ ! -f "$FONT" ]; then
        echo "Warning: Font file '$FONT' not found, will use system default"
        FONT=$(fc-match -f "%{file}" "monospace")
        if [ -z "$FONT" ]; then
            echo "Error: Could not find a suitable monospace font"
            missing_deps=true
        else
            echo "Using font: $FONT"
        fi
    fi
    
    if [ "$missing_deps" = true ]; then
        return 1
    fi
    
    return 0
}

# Setup temporary directory
setup_temp_dir() {
    TEMP_DIR=$(mktemp -d)
    if [ ! -d "$TEMP_DIR" ]; then
        echo "Error: Failed to create temporary directory"
        return 1
    fi
    
    if [ "$DEBUG" = true ]; then
        echo "Created temporary directory: $TEMP_DIR"
    fi
    
    return 0
}

# Clean up resources
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        if [ "$DEBUG" = true ]; then
            echo "Keeping temporary files in: $TEMP_DIR"
        else
            rm -rf "$TEMP_DIR"
            if [ "$?" -ne 0 ]; then
                echo "Warning: Failed to clean up temporary directory: $TEMP_DIR"
            fi
        fi
    fi
}

# Analyze audio to determine characteristics
analyze_audio() {
    local input="$1"
    local output_file="$TEMP_DIR/audio_analysis.json"
    
    echo "Analyzing audio characteristics..."
    
    # Extract audio information (duration, sample rate, etc.)
    ffprobe -v quiet -print_format json -show_format -show_streams "$input" > "$output_file"
    
    if [ ! -f "$output_file" ]; then
        echo "Error: Failed to analyze audio file"
        return 1
    fi
    
    # Extract key information - using grep as jq might not be installed everywhere
    local duration=$(grep -o '"duration": "[^"]*"' "$output_file" | head -1 | cut -d'"' -f4)
    local sample_rate=$(grep -o '"sample_rate": "[^"]*"' "$output_file" | head -1 | cut -d'"' -f4)
    local channels=$(grep -o '"channels": [0-9]*' "$output_file" | head -1 | awk '{print $2}')
    
    echo "Audio duration: $duration seconds"
    echo "Sample rate: $sample_rate Hz"
    echo "Channels: $channels"
    
    # For adaptive mode, analyze frequency content to determine best visualization
    if [ "$VIZ_MODE" = "adaptive" ]; then
        echo "Performing frequency analysis for adaptive visualization..."
        
        # Generate a short spectrum analysis to detect dominant frequency characteristics
        ffmpeg -v quiet -i "$input" -filter_complex "showspectrum=s=100x100" -frames:v 1 -f null - 2>/dev/null
        
        # Based on frequency analysis, we could set adaptive parameters here
        # For now, we'll use a placeholder approach that sets VIZ_MODE based on channels
        if [ "$channels" -gt 1 ]; then
            VIZ_MODE="combined"
            echo "Adaptive mode selected: combined (based on multi-channel audio)"
        else
            VIZ_MODE="spectrum"
            echo "Adaptive mode selected: spectrum (based on mono audio)"
        fi
    fi
    
    return 0
}

# Generate ASCII art visualization - FIXED FUNCTION
generate_visualization() {
    local input="$1"
    local output_file="$TEMP_DIR/ascii_art.txt"
    local preview_file="$TEMP_DIR/preview.mp4"
    local filter_complex=""
    local viz_command=""
    
    echo "Generating ASCII visualization using mode: $VIZ_MODE"
    
    # Construct the filter complex based on visualization mode
    case "$VIZ_MODE" in
        "spectrum")
            filter_complex="[0:a]showspectrum=s=${VIZ_WIDTH}x${VIZ_HEIGHT}:slide=scroll:mode=combined:scale=log:color=${COLOR_SCHEME},format=rgb24[v]"
            ;;
            
        "waveform")
            filter_complex="[0:a]showwaves=s=${VIZ_WIDTH}x${VIZ_HEIGHT}:mode=p2p:n=30:draw=full:colors=0x00FFFF,format=rgb24[v]"
            ;;
            
        combined)
    local spec_height=$(($VIZ_HEIGHT/2))
    local wave_height=$(($VIZ_HEIGHT/3))
    local vol_height=$(($VIZ_HEIGHT/6))
    
    filter_complex="[0:a]asplit=3[a1][a2][a3];\
[a1]showspectrum=s=${VIZ_WIDTH}x${spec_height}:mode=combined:slide=scroll:scale=log:color=${COLOR_SCHEME}[spectrum];\
[a2]showwaves=s=${VIZ_WIDTH}x${wave_height}:mode=p2p:n=30:draw=full:colors=0x00FFFF[waves];\
[a3]showvolume=f=0.8:b=4:w=${VIZ_WIDTH}:h=${vol_height}:c=0xFFFFFF[volume];\
[spectrum][waves]vstack[upper];\
[upper][volume]vstack[combined];\
[combined]hue=h=t*10[colored];\
[colored]format=rgb24[v]"
    ;;
            
        "adaptive")
            # This shouldn't be reached as adaptive mode should be converted to another mode
            echo "Error: Adaptive mode not properly set during analysis"
            return 1
            ;;
            
        *)
            echo "Error: Unknown visualization mode: $VIZ_MODE"
            return 1
            ;;
    esac
    
    # Generate ASCII art - now with more detailed error handling and verbose output
    echo "Running FFmpeg for ASCII generation..."
    # Create a script file for better error handling
    echo "#!/bin/bash" > "$TEMP_DIR/vizgen.sh"
    echo "ffmpeg -i \"$input\" -filter_complex \"$filter_complex\" -map \"[v]\" -f caca -charset $CHARSET -algorithm $DITHER_ALGO -color full16 \"$output_file\" 2>\"$TEMP_DIR/ffmpeg_error.log\"" >> "$TEMP_DIR/vizgen.sh"
    chmod +x "$TEMP_DIR/vizgen.sh"
    
    # Execute the script
    "$TEMP_DIR/vizgen.sh"
    
    # Check if ASCII generation was successful
    if [ ! -f "$output_file" ] || [ ! -s "$output_file" ]; then
        echo "Error: Failed to generate ASCII visualization"
        if [ -f "$TEMP_DIR/ffmpeg_error.log" ]; then
            echo "FFmpeg error log:"
            cat "$TEMP_DIR/ffmpeg_error.log"
        fi
        
        # Try with a simpler approach as fallback within the combined mode
        if [ "$VIZ_MODE" = "combined" ]; then
            echo "Trying fallback approach for combined mode..."
            filter_complex="[0:a]showspectrum=s=${VIZ_WIDTH}x${VIZ_HEIGHT}:slide=scroll:mode=combined:scale=log,format=rgb24[v]"
            ffmpeg -i "$input" -filter_complex "$filter_complex" -map "[v]" -f caca -charset "$CHARSET" -algorithm "$DITHER_ALGO" -color full16 "$output_file" 2>"$TEMP_DIR/ffmpeg_fallback_error.log"
            
            if [ ! -f "$output_file" ] || [ ! -s "$output_file" ]; then
                echo "Error: Fallback approach also failed"
                if [ -f "$TEMP_DIR/ffmpeg_fallback_error.log" ]; then
                    echo "FFmpeg fallback error log:"
                    cat "$TEMP_DIR/ffmpeg_fallback_error.log"
                fi
                return 1
            else
                echo "Fallback approach succeeded"
            fi
        else
            return 1
        fi
    fi
    
    # Create a small preview for verification if in debug mode
    if [ "$DEBUG" = true ]; then
        echo "Creating debug preview..."
        ffmpeg -f lavfi -i "color=c=black:s=640x480:r=30" -vf "drawtext=fontfile=$FONT:fontsize=10:fontcolor=white:x=10:y=10:textfile=$output_file" -t 5 -c:v libx264 -preset ultrafast "$preview_file" 2>/dev/null
        echo "Debug preview created: $preview_file"
    fi
    
    echo "ASCII visualization generated successfully"
    return 0
}

# Render final video with effects
render_video() {
    local input="$1"
    local ascii_file="$TEMP_DIR/ascii_art.txt"
    local temp_video="$TEMP_DIR/temp_video.mp4"
    local output="$2"
    local font_size=0
    local ffmpeg_preset=""
    local crf=0
    
    # Calculate optimal font size based on resolution
    font_size=$(echo "scale=0; ($OUTPUT_HEIGHT / 60)" | bc)
    if [ "$font_size" -lt 10 ]; then font_size=10; fi
    
    # Set encoding parameters based on quality setting
    case "$VIDEO_QUALITY" in
        "draft")
            ffmpeg_preset="ultrafast"
            crf=28
            ;;
        "normal")
            ffmpeg_preset="medium"
            crf=23
            ;;
        "high")
            ffmpeg_preset="slow" 
            crf=18
            ;;
        "ultra")
            ffmpeg_preset="veryslow"
            crf=15
            ;;
        *)
            echo "Unknown quality setting: $VIDEO_QUALITY, using defaults"
            ffmpeg_preset="medium"
            crf=23
            ;;
    esac
    
    echo "Rendering video with quality: $VIDEO_QUALITY (preset=$ffmpeg_preset, crf=$crf)"
    
    # Apply specific effects based on effect level
    local vf_effects=""
    case "$EFFECT_LEVEL" in
        "minimal")
            vf_effects="drawtext=fontfile=$FONT:fontsize=$font_size:fontcolor=white:x=10:y=10:textfile=$ascii_file"
            ;;
            
        "medium")
            # Fix: Simplified medium effects to reduce potential errors
            vf_effects="drawtext=fontfile=$FONT:fontsize=$font_size:fontcolor=white:x=10:y=10:textfile=$ascii_file,hue=h=t*5:s=1.1"
            ;;
            
        "intense")
            # Fix: Split the complex effect chain into stages for better control
            echo "Creating glow effect for intense mode..."
            # Stage 1: Create basic text rendering
            ffmpeg -f lavfi -i "color=c=black:s=${OUTPUT_WIDTH}x${OUTPUT_HEIGHT}:r=30" -vf "drawtext=fontfile=$FONT:fontsize=$font_size:fontcolor=white:x=10:y=10:textfile=$ascii_file" -t 10 -c:v libx264 -preset ultrafast "$TEMP_DIR/stage1.mp4" 2>/dev/null
            
            # Stage 2: Add effects
            vf_effects="hue=h=t*10:s=t/100+1:b=1.1,eq=brightness=0.03:contrast=1.2:saturation=1.2"
            ;;
            
        *)
            echo "Unknown effect level: $EFFECT_LEVEL, using defaults"
            vf_effects="drawtext=fontfile=$FONT:fontsize=$font_size:fontcolor=white:x=10:y=10:textfile=$ascii_file"
            ;;
    esac
    
    # Render the video
    echo "Creating video with ASCII art..."
    
    if [ "$EFFECT_LEVEL" = "intense" ] && [ -f "$TEMP_DIR/stage1.mp4" ]; then
        # For intense mode, process the pre-rendered video with effects
        ffmpeg -i "$TEMP_DIR/stage1.mp4" -vf "$vf_effects" -c:v libx264 -preset "$ffmpeg_preset" -crf "$crf" -pix_fmt yuv420p "$temp_video" 2>"$TEMP_DIR/render_error.log"
    else
        # For other modes, render directly
        ffmpeg -f lavfi -i "color=c=black:s=${OUTPUT_WIDTH}x${OUTPUT_HEIGHT}:r=30" -vf "$vf_effects" -c:v libx264 -preset "$ffmpeg_preset" -crf "$crf" -pix_fmt yuv420p "$temp_video" 2>"$TEMP_DIR/render_error.log"
    fi
    
    # Check if video rendering was successful
    if [ ! -f "$temp_video" ]; then
        echo "Error: Failed to render video"
        if [ -f "$TEMP_DIR/render_error.log" ]; then
            echo "Render error log:"
            cat "$TEMP_DIR/render_error.log"
        fi
        return 1
    fi
    
    # Add audio to the video
    echo "Adding audio to video..."
    ffmpeg -i "$temp_video" -i "$input" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest "$output" 2>"$TEMP_DIR/mux_error.log"
    
    # Check if final output was successful
    if [ ! -f "$output" ]; then
        echo "Error: Failed to add audio to video"
        if [ -f "$TEMP_DIR/mux_error.log" ]; then
            echo "Muxing error log:"
            cat "$TEMP_DIR/mux_error.log"
        fi
        return 1
    fi
    
    echo "Final video rendered successfully: $output"
    return 0
}

# Parse command line arguments
parse_arguments() {
    local input=""
    local output=""
    
    # Check for minimum required arguments
    if [ "$#" -lt 2 ]; then
        show_usage
        return 1
    fi
    
    # Get input and output files
    input="$1"
    output="$2"
    shift 2
    
    # Validate input file
    if [ ! -f "$input" ]; then
        echo "Error: Input file does not exist: $input"
        return 1
    fi
    
    # Process options
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --mode)
                VIZ_MODE="$2"
                shift 2
                ;;
            --colors)
                COLOR_SCHEME="$2"
                shift 2
                ;;
            --charset)
                CHARSET="$2"
                shift 2
                ;;
            --dither)
                DITHER_ALGO="$2"
                shift 2
                ;;
            --effects)
                EFFECT_LEVEL="$2"
                shift 2
                ;;
            --width)
                VIZ_WIDTH="$2"
                shift 2
                ;;
            --height)
                VIZ_HEIGHT="$2"
                shift 2
                ;;
            --quality)
                VIDEO_QUALITY="$2"
                shift 2
                ;;
            --debug)
                DEBUG=true
                shift
                ;;
            --help)
                show_usage
                return 1
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                return 1
                ;;
        esac
    done
    
    # Set the global variables
    INPUT="$input"
    OUTPUT="$output"
    
    return 0
}

# Main function
main() {
    local result=0
    
    echo "=========================================="
    echo "AsciiSymphony: Advanced Audio Visualizer"
    echo "=========================================="
    
    # Parse command line arguments
    parse_arguments "$@"
    result=$?
    if [ $result -ne 0 ]; then
        return $result
    fi
    
    # Check for required dependencies
    check_dependencies
    result=$?
    if [ $result -ne 0 ]; then
        return $result
    fi
    
    # Setup temporary directory
    setup_temp_dir
    result=$?
    if [ $result -ne 0 ]; then
        return $result
    fi
    
    # Set trap for cleanup
    trap cleanup EXIT INT TERM
    
    # Process the audio file
    analyze_audio "$INPUT"
    result=$?
    if [ $result -ne 0 ]; then
        return $result
    fi
    
    # Generate ASCII art visualization
    generate_visualization "$INPUT"
    result=$?
    if [ $result -ne 0 ]; then
        return $result
    fi
    
    # Render final video
    render_video "$INPUT" "$OUTPUT"
    result=$?
    if [ $result -ne 0 ]; then
        return $result
    fi
    
    echo "=========================================="
    echo "Visualization complete: $OUTPUT"
    echo "=========================================="
    
    return 0
}

# Run main function with all arguments
main "$@"
exit $?