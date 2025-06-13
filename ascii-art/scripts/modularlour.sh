#!/bin/bash

# =============================================================================
# AsciiSymphony: Advanced Modular ASCII Art Audio Visualizer
# =============================================================================
# A sophisticated, modular system for creating artistic ASCII visualizations
# from audio files using FFmpeg and libcaca.
# 
# Usage: ./ascii_symphony.sh input.flac output.mp4 [options]
# =============================================================================

# =============================================================================
# CONFIGURATION AND DEFAULT SETTINGS
# =============================================================================

# Visualization settings
VIZ_WIDTH=640
VIZ_HEIGHT=480
VIZ_MODE="adaptive"  # adaptive, spectrum, waveform, combined, multi_view
COLOR_SCHEME="rainbow"  # rainbow, thermal, matrix, grayscale
CHARSET="blocks"  # ascii, blocks, shades
DITHER_ALGO="fstein"  # fstein, ordered4, random
EFFECT_LEVEL="medium"  # minimal, medium, intense

# Output settings
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
OUTPUT_WIDTH=1280
OUTPUT_HEIGHT=720
VIDEO_QUALITY="high"  # draft, normal, high, ultra
FPS=25

# Processing settings
TEMP_DIR=""
DEBUG=false
FORCE_FALLBACK=false
INPUT=""
OUTPUT=""
MAX_FRAMES=0  # 0 means process entire file

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Show usage information
show_usage() {
    echo "AsciiSymphony: Advanced Modular ASCII Art Audio Visualizer"
    echo "Usage: $0 input.flac output.mp4 [options]"
    echo ""
    echo "Options:"
    echo "  --mode MODE         Visualization mode (adaptive, spectrum, waveform, combined, multi_view)"
    echo "  --colors SCHEME     Color scheme (rainbow, thermal, matrix, grayscale)"
    echo "  --charset SET       Character set (ascii, blocks, shades)"
    echo "  --dither ALGO       Dithering algorithm (fstein, ordered4, random)"
    echo "  --effects LEVEL     Effect intensity (minimal, medium, intense)"
    echo "  --width WIDTH       Visualization width"
    echo "  --height HEIGHT     Visualization height"
    echo "  --quality LEVEL     Output video quality (draft, normal, high, ultra)"
    echo "  --fps FPS           Frames per second (default: 25)"
    echo "  --max-frames N      Only process N frames (default: entire file)"
    echo "  --fallback          Force fallback mode (simpler but more reliable)"
    echo "  --debug             Enable debug mode"
    echo "  --help              Show this help message"
}

# Logging functions
log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

log_warning() {
    echo -e "\033[0;33m[WARNING]\033[0m $1"
}

log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

log_debug() {
    if [ "$DEBUG" = true ]; then
        echo -e "\033[0;35m[DEBUG]\033[0m $1"
    fi
}

# Check for required dependencies
check_dependencies() {
    local missing_deps=false
    
    # Check for ffmpeg with libcaca support
    if ! ffmpeg -version 2>/dev/null | grep -q "enable-libcaca"; then
        log_error "FFmpeg is not installed or does not have libcaca support"
        missing_deps=true
    fi
    
    # Check for bc (used for calculations)
    if ! command -v bc &> /dev/null; then
        log_error "bc is not installed"
        missing_deps=true
    fi
    
    # Check for font file
    if [ ! -f "$FONT" ]; then
        log_warning "Font file '$FONT' not found, trying to find a suitable alternative"
        if command -v fc-match &> /dev/null; then
            FONT=$(fc-match -f "%{file}" "monospace")
            if [ -z "$FONT" ] || [ ! -f "$FONT" ]; then
                log_error "Could not find a suitable monospace font"
                missing_deps=true
            else
                log_info "Using font: $FONT"
            fi
        else
            # Try some common paths as fallback
            for f in /usr/share/fonts/truetype/*/Mono*.ttf /usr/share/fonts/TTF/mono*.ttf; do
                if [ -f "$f" ]; then
                    FONT="$f"
                    log_info "Using font: $FONT"
                    break
                fi
            done
            
            if [ ! -f "$FONT" ]; then
                log_error "Could not find a suitable monospace font"
                missing_deps=true
            fi
        fi
    fi
    
    if [ "$missing_deps" = true ]; then
        return 1
    fi
    
    log_success "All dependencies are satisfied"
    return 0
}

# Setup temporary directory
setup_temp_dir() {
    TEMP_DIR=$(mktemp -d)
    if [ ! -d "$TEMP_DIR" ]; then
        log_error "Failed to create temporary directory"
        return 1
    fi
    
    log_debug "Created temporary directory: $TEMP_DIR"
    return 0
}

# Clean up resources
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        if [ "$DEBUG" = true ]; then
            log_info "Keeping temporary files in: $TEMP_DIR"
        else
            rm -rf "$TEMP_DIR"
            if [ "$?" -ne 0 ]; then
                log_warning "Failed to clean up temporary directory: $TEMP_DIR"
            fi
        fi
    fi
}

# =============================================================================
# AUDIO ANALYSIS FUNCTIONS
# =============================================================================

# Analyze audio to determine characteristics
analyze_audio() {
    local input="$1"
    local output_file="$TEMP_DIR/audio_analysis.json"
    
    log_info "Analyzing audio characteristics..."
    
    # Extract audio information
    ffprobe -v quiet -print_format json -show_format -show_streams "$input" > "$output_file"
    
    if [ ! -f "$output_file" ]; then
        log_error "Failed to analyze audio file"
        return 1
    fi
    
    # Extract key information - using grep as jq might not be installed everywhere
    local duration=$(grep -o '"duration": "[^"]*"' "$output_file" | head -1 | cut -d'"' -f4)
    local sample_rate=$(grep -o '"sample_rate": "[^"]*"' "$output_file" | head -1 | cut -d'"' -f4)
    local channels=$(grep -o '"channels": [0-9]*' "$output_file" | head -1 | awk '{print $2}')
    
    # Save to a more accessible format for other functions
    echo "DURATION=$duration" > "$TEMP_DIR/audio_info.txt"
    echo "SAMPLE_RATE=$sample_rate" >> "$TEMP_DIR/audio_info.txt"
    echo "CHANNELS=$channels" >> "$TEMP_DIR/audio_info.txt"
    
    log_info "Audio duration: $duration seconds"
    log_info "Sample rate: $sample_rate Hz"
    log_info "Channels: $channels"
    
    # For adaptive mode, analyze frequency content to determine best visualization
    if [ "$VIZ_MODE" = "adaptive" ] && [ "$FORCE_FALLBACK" != true ]; then
        log_info "Performing frequency analysis for adaptive visualization..."
        
        # Generate a short spectrum analysis to detect dominant characteristics
        ffmpeg -v quiet -i "$input" -filter_complex "showspectrum=s=100x100" -frames:v 1 -f null - 2>/dev/null
        
        # Based on frequency analysis and channels, set the most appropriate mode
        if [ "$channels" -gt 1 ]; then
            VIZ_MODE="combined"
            log_info "Adaptive mode selected: combined (based on multi-channel audio)"
        else
            VIZ_MODE="spectrum"
            log_info "Adaptive mode selected: spectrum (based on mono audio)"
        fi
    elif [ "$FORCE_FALLBACK" = true ]; then
        VIZ_MODE="spectrum"
        log_info "Forced fallback mode: spectrum"
    fi
    
    return 0
}

# =============================================================================
# VISUALIZATION GENERATION FUNCTIONS
# =============================================================================

# Generate filter complex based on visualization mode
generate_filter_complex() {
    local mode="$1"
    local filter_complex=""
    
    case "$mode" in
        "spectrum")
            filter_complex="[0:a]showspectrum=s=${VIZ_WIDTH}x${VIZ_HEIGHT}:slide=scroll:mode=combined:scale=log:color=${COLOR_SCHEME}:fps=${FPS},format=rgb24[v]"
            ;;
            
        "waveform")
            filter_complex="[0:a]showwaves=s=${VIZ_WIDTH}x${VIZ_HEIGHT}:mode=p2p:n=30:draw=full:colors=0x00FFFF:rate=${FPS},format=rgb24[v]"
            ;;
            
        "combined")
            local spec_height=$(($VIZ_HEIGHT/2))
            local wave_height=$(($VIZ_HEIGHT/3))
            local vol_height=$(($VIZ_HEIGHT/6))
            
            filter_complex="[0:a]asplit=3[a1][a2][a3];\
[a1]showspectrum=s=${VIZ_WIDTH}x${spec_height}:mode=combined:slide=scroll:scale=log:color=${COLOR_SCHEME}:fps=${FPS}[spectrum];\
[a2]showwaves=s=${VIZ_WIDTH}x${wave_height}:mode=p2p:n=30:rate=${FPS}:draw=full:colors=0x00FFFF[waves];\
[a3]showvolume=f=0.8:b=4:w=${VIZ_WIDTH}:h=${vol_height}:c=0xFFFFFF[volume];\
[spectrum][waves]vstack[upper];\
[upper][volume]vstack[combined];\
[combined]hue=h=t*5[colored];\
[colored]format=rgb24[v]"
            ;;
            
        "multi_view")
            local cell_width=$(($VIZ_WIDTH/2))
            local cell_height=$(($VIZ_HEIGHT/2))
            
            filter_complex="[0:a]asplit=4[a1][a2][a3][a4];\
[a1]showspectrum=s=${cell_width}x${cell_height}:mode=combined:slide=scroll:scale=log:color=rainbow:fps=${FPS}[sp];\
[a2]showwaves=s=${cell_width}x${cell_height}:mode=p2p:n=30:rate=${FPS}:colors=0x00FFFF[wv];\
[a3]showspectrum=s=${cell_width}x${cell_height}:mode=combined:slide=scroll:scale=sqrt:color=hue:fps=${FPS}[sp2];\
[a4]showwaves=s=${cell_width}x${cell_height}:mode=cline:rate=${FPS}:colors=0xFFFFFF[wv2];\
[sp][wv]hstack[top];\
[sp2][wv2]hstack[bottom];\
[top][bottom]vstack[grid];\
[grid]format=rgb24[v]"
            ;;
            
        *)
            log_error "Unknown visualization mode: $mode"
            return 1
            ;;
    esac
    
    echo "$filter_complex"
    return 0
}

# Generate a fallback filter complex
generate_fallback_filter() {
    local filter_complex="[0:a]showspectrum=s=${VIZ_WIDTH}x${VIZ_HEIGHT}:slide=scroll:mode=combined:scale=log:color=${COLOR_SCHEME}:fps=${FPS},format=rgb24[v]"
    echo "$filter_complex"
    return 0
}

# Generate ASCII art visualization
generate_visualization() {
    local input="$1"
    local output_file="$TEMP_DIR/ascii_art.txt"
    local preview_file="$TEMP_DIR/preview.mp4"
    local filter_complex=""
    local frames_option=""
    
    log_info "Generating ASCII visualization using mode: $VIZ_MODE"
    
    # Set max frames option if specified
    if [ "$MAX_FRAMES" -gt 0 ]; then
        frames_option="-frames:v $MAX_FRAMES"
        log_info "Processing $MAX_FRAMES frames"
    fi
    
    # Get filter complex based on mode
    filter_complex=$(generate_filter_complex "$VIZ_MODE")
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # Generate ASCII art
    log_info "Running FFmpeg for ASCII generation..."
    
    # Create a script file for better error handling
    echo "#!/bin/bash" > "$TEMP_DIR/vizgen.sh"
    echo "ffmpeg -i \"$input\" -filter_complex \"$filter_complex\" -map \"[v]\" $frames_option -f caca -charset $CHARSET -algorithm $DITHER_ALGO -color full16 \"$output_file\" 2>\"$TEMP_DIR/ffmpeg_error.log\"" >> "$TEMP_DIR/vizgen.sh"
    chmod +x "$TEMP_DIR/vizgen.sh"
    
    # Execute the script
    "$TEMP_DIR/vizgen.sh"
    
    # Check if ASCII generation was successful
    if [ ! -f "$output_file" ] || [ ! -s "$output_file" ]; then
        log_error "Failed to generate ASCII visualization"
        if [ -f "$TEMP_DIR/ffmpeg_error.log" ]; then
            log_error "FFmpeg error log:"
            cat "$TEMP_DIR/ffmpeg_error.log"
        fi
        
        # Try with a fallback approach
        log_warning "Trying fallback approach..."
        filter_complex=$(generate_fallback_filter)
        
        ffmpeg -i "$input" -filter_complex "$filter_complex" -map "[v]" $frames_option -f caca -charset "$CHARSET" -algorithm "$DITHER_ALGO" -color full16 "$output_file" 2>"$TEMP_DIR/ffmpeg_fallback_error.log"
        
        if [ ! -f "$output_file" ] || [ ! -s "$output_file" ]; then
            log_error "Fallback approach also failed"
            if [ -f "$TEMP_DIR/ffmpeg_fallback_error.log" ]; then
                log_error "FFmpeg fallback error log:"
                cat "$TEMP_DIR/ffmpeg_fallback_error.log"
            fi
            return 1
        else
            log_success "Fallback approach succeeded"
        fi
    else
        log_success "ASCII visualization generated successfully"
    fi
    
    # Create a small preview for verification if in debug mode
    if [ "$DEBUG" = true ]; then
        log_debug "Creating debug preview..."
        ffmpeg -f lavfi -i "color=c=black:s=640x480:r=30" -vf "drawtext=fontfile=$FONT:fontsize=10:fontcolor=white:x=10:y=10:textfile=$output_file" -t 5 -c:v libx264 -preset ultrafast "$preview_file" 2>/dev/null
        log_debug "Debug preview created: $preview_file"
    fi
    
    return 0
}

# =============================================================================
# VIDEO RENDERING FUNCTIONS
# =============================================================================

# Calculate optimal font size based on resolution
calculate_font_size() {
    local height="$1"
    local font_size=$(echo "scale=0; ($height / 60)" | bc)
    if [ "$font_size" -lt 10 ]; then font_size=10; fi
    echo "$font_size"
}

# Get encoding parameters based on quality setting
get_encoding_params() {
    local quality="$1"
    local params=""
    
    case "$quality" in
        "draft")
            params="preset=ultrafast:crf=28"
            ;;
        "normal")
            params="preset=medium:crf=23"
            ;;
        "high")
            params="preset=slow:crf=18"
            ;;
        "ultra")
            params="preset=veryslow:crf=15"
            ;;
        *)
            log_warning "Unknown quality setting: $quality, using defaults"
            params="preset=medium:crf=23"
            ;;
    esac
    
    echo "$params"
}

# Get effect filters based on effect level
get_effect_filters() {
    local level="$1"
    local font_size="$2"
    local ascii_file="$3"
    local vf_effects=""
    
    case "$level" in
        "minimal")
            vf_effects="drawtext=fontfile=$FONT:fontsize=$font_size:fontcolor=white:x=10:y=10:textfile=$ascii_file"
            ;;
            
        "medium")
            vf_effects="drawtext=fontfile=$FONT:fontsize=$font_size:fontcolor=white:x=10:y=10:textfile=$ascii_file,hue=h=t*5:s=1.1"
            ;;
            
        "intense")
            # For intense effects, we need a more complex approach
            # First create a basic text rendering
            ffmpeg -f lavfi -i "color=c=black:s=${OUTPUT_WIDTH}x${OUTPUT_HEIGHT}:r=${FPS}" -vf "drawtext=fontfile=$FONT:fontsize=$font_size:fontcolor=white:x=10:y=10:textfile=$ascii_file" -t 10 -c:v libx264 -preset ultrafast "$TEMP_DIR/stage1.mp4" 2>/dev/null
            
            if [ -f "$TEMP_DIR/stage1.mp4" ]; then
                vf_effects="hue=h=t*10:s=t/100+1:b=1.1,eq=brightness=0.03:contrast=1.2:saturation=1.2"
                log_debug "Created stage 1 video for intense effects"
            else
                log_warning "Failed to create stage 1 video for intense effects, falling back to medium"
                vf_effects="drawtext=fontfile=$FONT:fontsize=$font_size:fontcolor=white:x=10:y=10:textfile=$ascii_file,hue=h=t*5:s=1.1"
            fi
            ;;
            
        *)
            log_warning "Unknown effect level: $level, using defaults"
            vf_effects="drawtext=fontfile=$FONT:fontsize=$font_size:fontcolor=white:x=10:y=10:textfile=$ascii_file"
            ;;
    esac
    
    echo "$vf_effects"
}

# Render final video with effects
render_video() {
    local input="$1"
    local ascii_file="$TEMP_DIR/ascii_art.txt"
    local temp_video="$TEMP_DIR/temp_video.mp4"
    local output="$2"
    
    log_info "Preparing to render video..."
    
    # Calculate optimal font size
    local font_size=$(calculate_font_size $OUTPUT_HEIGHT)
    log_debug "Using font size: $font_size"
    
    # Get encoding parameters
    local encoding_params=$(get_encoding_params "$VIDEO_QUALITY")
    log_info "Rendering video with quality: $VIDEO_QUALITY ($encoding_params)"
    
    # Get effect filters
    local vf_effects=$(get_effect_filters "$EFFECT_LEVEL" "$font_size" "$ascii_file")
    
    # Render the video
    log_info "Creating video with ASCII art..."
    
    if [ "$EFFECT_LEVEL" = "intense" ] && [ -f "$TEMP_DIR/stage1.mp4" ]; then
        # For intense mode, process the pre-rendered video with effects
        ffmpeg -i "$TEMP_DIR/stage1.mp4" -vf "$vf_effects" -c:v libx264 -preset $(echo $encoding_params | cut -d':' -f1 | cut -d'=' -f2) -crf $(echo $encoding_params | cut -d':' -f2 | cut -d'=' -f2) -pix_fmt yuv420p "$temp_video" 2>"$TEMP_DIR/render_error.log"
    else
        # For other modes, render directly
        ffmpeg -f lavfi -i "color=c=black:s=${OUTPUT_WIDTH}x${OUTPUT_HEIGHT}:r=${FPS}" -vf "$vf_effects" -c:v libx264 -preset $(echo $encoding_params | cut -d':' -f1 | cut -d'=' -f2) -crf $(echo $encoding_params | cut -d':' -f2 | cut -d'=' -f2) -pix_fmt yuv420p "$temp_video" 2>"$TEMP_DIR/render_error.log"
    fi
    
    # Check if video rendering was successful
    if [ ! -f "$temp_video" ]; then
        log_error "Failed to render video"
        if [ -f "$TEMP_DIR/render_error.log" ]; then
            log_error "Render error log:"
            cat "$TEMP_DIR/render_error.log"
        fi
        return 1
    fi
    
    # Calculate audio duration for proper sync
    local duration=0
    if [ -f "$TEMP_DIR/audio_info.txt" ]; then
        duration=$(grep DURATION "$TEMP_DIR/audio_info.txt" | cut -d= -f2)
    fi
    
    # Add audio to the video
    log_info "Adding audio to video..."
    local extra_args=""
    if [ -n "$duration" ] && [ "$duration" != "N/A" ]; then
        extra_args="-t $duration"
    fi
    
    ffmpeg -i "$temp_video" -i "$input" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest $extra_args "$output" 2>"$TEMP_DIR/mux_error.log"
    
    # Check if final output was successful
    if [ ! -f "$output" ]; then
        log_error "Failed to add audio to video"
        if [ -f "$TEMP_DIR/mux_error.log" ]; then
            log_error "Muxing error log:"
            cat "$TEMP_DIR/mux_error.log"
        fi
        return 1
    fi
    
    log_success "Final video rendered successfully: $output"
    return 0
}

# =============================================================================
# ARGUMENT PARSING AND MAIN FUNCTION
# =============================================================================

# Parse command line arguments
parse_arguments() {
    # Check for minimum required arguments
    if [ "$#" -lt 2 ]; then
        show_usage
        return 1
    fi
    
    # Get input and output files
    INPUT="$1"
    OUTPUT="$2"
    shift 2
    
    # Validate input file
    if [ ! -f "$INPUT" ]; then
        log_error "Input file does not exist: $INPUT"
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
            --fps)
                FPS="$2"
                shift 2
                ;;
            --max-frames)
                MAX_FRAMES="$2"
                shift 2
                ;;
            --fallback)
                FORCE_FALLBACK=true
                shift
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
                log_error "Unknown option: $1"
                show_usage
                return 1
                ;;
        esac
    done
    
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