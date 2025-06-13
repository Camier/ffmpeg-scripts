#!/bin/bash

# =============================================================================
# AsciiSymphony: Advanced Modular ASCII Art Audio Visualizer (Enhanced Edition)
# =============================================================================
# A sophisticated, modular system for creating artistic ASCII visualizations
# from audio files using FFmpeg and libcaca, now with exotic visualizations.
# 
# Usage: ./ascii_symphony.sh input.flac output.mp4 [options]
# =============================================================================

# =============================================================================
# CONFIGURATION MANAGEMENT
# =============================================================================

# Configuration defaults with single source of truth
declare -A CONFIG
initialize_config() {
    # Visualization settings
    CONFIG[VIZ_WIDTH]=640
    CONFIG[VIZ_HEIGHT]=480
    CONFIG[VIZ_MODE]="adaptive"  # adaptive, spectrum, waveform, combined, multi_view,
                                # fractal_soundscape, neural_circuit, vector_field,
                                # digital_rain, quantum_flux, time_warp, dimension_fold,
                                # atomic_resonance
    CONFIG[COLOR_SCHEME]="rainbow"  # rainbow, thermal, matrix, grayscale
    CONFIG[CHARSET]="blocks"  # ascii, blocks, shades
    CONFIG[DITHER_ALGO]="fstein"  # fstein, ordered4, random
    CONFIG[EFFECT_LEVEL]="medium"  # minimal, medium, intense

    # Output settings
    CONFIG[FONT]="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    CONFIG[OUTPUT_WIDTH]=1280
    CONFIG[OUTPUT_HEIGHT]=720
    CONFIG[VIDEO_QUALITY]="high"  # draft, normal, high, ultra
    CONFIG[FPS]=25

    # Processing settings
    CONFIG[TEMP_DIR]=""
    CONFIG[DEBUG]=false
    CONFIG[FORCE_FALLBACK]=false
    CONFIG[INPUT]=""
    CONFIG[OUTPUT]=""
    CONFIG[MAX_FRAMES]=0  # 0 means process entire file

    # Runtime paths - centralized for easy reference
    CONFIG[ASCII_FILE]=""
    CONFIG[PREVIEW_FILE]=""
    CONFIG[TEMP_VIDEO]=""
    CONFIG[AUDIO_INFO]=""
    CONFIG[ERROR_LOG]=""
}

# Validate configuration after parsing arguments
validate_config() {
    local errors=0

    # Required inputs validation
    if [[ ! -f "${CONFIG[INPUT]}" ]]; then
        log_error "Input file does not exist: ${CONFIG[INPUT]}"
        errors=$((errors + 1))
    fi

    if [[ -z "${CONFIG[OUTPUT]}" ]]; then
        log_error "Output file not specified"
        errors=$((errors + 1))
    fi

    # Visualization mode validation
    local valid_modes=("adaptive" "spectrum" "waveform" "combined" "multi_view" 
                      "fractal_soundscape" "neural_circuit" "vector_field" 
                      "digital_rain" "quantum_flux" "time_warp" "dimension_fold" 
                      "atomic_resonance")
    
    if ! array_contains "${CONFIG[VIZ_MODE]}" "${valid_modes[@]}"; then
        log_error "Invalid visualization mode: ${CONFIG[VIZ_MODE]}"
        log_info "Valid modes: ${valid_modes[*]}"
        errors=$((errors + 1))
    fi

    # Return error count (0 means success)
    return $errors
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Array contains helper
array_contains() {
    local needle="$1"; shift
    local item
    for item in "$@"; do
        [[ "$item" == "$needle" ]] && return 0
    done
    return 1
}

# Execute command with error handling
execute_command() {
    local cmd_description="$1"
    local error_file="$2"
    local exit_on_error="${3:-true}"
    shift 3
    
    log_debug "Executing: $*"
    
    # Execute the command, capturing stderr
    if ! "$@" 2>"$error_file"; then
        log_error "Failed: $cmd_description"
        log_error "$(cat "$error_file")"
        
        if [[ "$exit_on_error" == true ]]; then
            return 1
        fi
    fi
    
    return 0
}

# Centralized logging functions with consistent formatting
log_info() { echo -e "\033[0;34m[INFO]\033[0m $1"; }
log_success() { echo -e "\033[0;32m[SUCCESS]\033[0m $1"; }
log_warning() { echo -e "\033[0;33m[WARNING]\033[0m $1"; }
log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1"; }
log_debug() { [[ "${CONFIG[DEBUG]}" == true ]] && echo -e "\033[0;35m[DEBUG]\033[0m $1"; }

# Resource management - centralized temp directory handling
setup_resources() {
    # Create temp directory
    CONFIG[TEMP_DIR]=$(mktemp -d)
    if [[ ! -d "${CONFIG[TEMP_DIR]}" ]]; then
        log_error "Failed to create temporary directory"
        return 1
    fi
    
    # Set derived paths
    CONFIG[ASCII_FILE]="${CONFIG[TEMP_DIR]}/ascii_art.txt"
    CONFIG[PREVIEW_FILE]="${CONFIG[TEMP_DIR]}/preview.mp4"
    CONFIG[TEMP_VIDEO]="${CONFIG[TEMP_DIR]}/temp_video.mp4"
    CONFIG[AUDIO_INFO]="${CONFIG[TEMP_DIR]}/audio_info.txt"
    CONFIG[ERROR_LOG]="${CONFIG[TEMP_DIR]}/error.log"
    
    log_debug "Created temporary directory: ${CONFIG[TEMP_DIR]}"
    return 0
}

cleanup_resources() {
    if [[ -d "${CONFIG[TEMP_DIR]}" ]]; then
        if [[ "${CONFIG[DEBUG]}" == true ]]; then
            log_info "Keeping temporary files in: ${CONFIG[TEMP_DIR]}"
        else
            rm -rf "${CONFIG[TEMP_DIR]}"
            [[ $? -ne 0 ]] && log_warning "Failed to clean up temporary directory: ${CONFIG[TEMP_DIR]}"
        fi
    fi
}

# Dependency checking with clear feedback
check_dependencies() {
    local missing_deps=false
    
    # Check for ffmpeg with libcaca support
    if ! ffmpeg -version 2>/dev/null | grep -q "enable-libcaca"; then
        log_error "FFmpeg is not installed or does not have libcaca support"
        missing_deps=true
    fi
    
    # Check for advanced filter support
    if ! ffmpeg -filters 2>/dev/null | grep -q "showcqt\|mandelbrot\|avectorscope"; then
        log_warning "Your FFmpeg may not support all visualization modes"
        # Not setting missing_deps to true, as this is just a warning
    fi
    
    # Check for bc (used for calculations)
    if ! command -v bc &> /dev/null; then
        log_error "bc is not installed"
        missing_deps=true
    fi
    
    # Check for font file
    if [ ! -f "${CONFIG[FONT]}" ]; then
        log_warning "Font file '${CONFIG[FONT]}' not found, trying to find a suitable alternative"
        if command -v fc-match &> /dev/null; then
            CONFIG[FONT]=$(fc-match -f "%{file}" "monospace")
            if [ -z "${CONFIG[FONT]}" ] || [ ! -f "${CONFIG[FONT]}" ]; then
                log_error "Could not find a suitable monospace font"
                missing_deps=true
            else
                log_info "Using font: ${CONFIG[FONT]}"
            fi
        else
            # Try some common paths as fallback
            for f in /usr/share/fonts/truetype/*/Mono*.ttf /usr/share/fonts/TTF/mono*.ttf; do
                if [ -f "$f" ]; then
                    CONFIG[FONT]="$f"
                    log_info "Using font: ${CONFIG[FONT]}"
                    break
                fi
            done
            
            if [ ! -f "${CONFIG[FONT]}" ]; then
                log_error "Could not find a suitable monospace font"
                missing_deps=true
            fi
        fi
    fi
    
    [[ "$missing_deps" == true ]] && return 1
    
    log_success "All dependencies are satisfied"
    return 0
}

# =============================================================================
# AUDIO ANALYSIS FUNCTIONS
# =============================================================================

# Single responsibility: Extract and store audio metadata
analyze_audio() {
    local input="${CONFIG[INPUT]}"
    local output_file="${CONFIG[TEMP_DIR]}/audio_analysis.json"
    
    log_info "Analyzing audio characteristics..."
    
    # Extract audio information
    if ! execute_command "audio analysis" "${CONFIG[ERROR_LOG]}" \
        ffprobe -v quiet -print_format json -show_format -show_streams "$input" > "$output_file"; then
        return 1
    fi
    
    # Process the extracted information
    parse_audio_metadata "$output_file"
    
    # Determine best visualization mode adaptively
    if [[ "${CONFIG[VIZ_MODE]}" == "adaptive" ]] && [[ "${CONFIG[FORCE_FALLBACK]}" != true ]]; then
        determine_optimal_visualization
    elif [[ "${CONFIG[FORCE_FALLBACK]}" == true ]]; then
        CONFIG[VIZ_MODE]="spectrum"
        log_info "Forced fallback mode: spectrum"
    fi
    
    return 0
}

# Parse the FFprobe output into a more accessible format
parse_audio_metadata() {
    local json_file="$1"
    
    # Extract key information using grep and awk
    local duration=$(grep -o '"duration": "[^"]*"' "$json_file" | head -1 | cut -d'"' -f4)
    local sample_rate=$(grep -o '"sample_rate": "[^"]*"' "$json_file" | head -1 | cut -d'"' -f4)
    local channels=$(grep -o '"channels": [0-9]*' "$json_file" | head -1 | awk '{print $2}')
    
    # Save to a more accessible format for other functions
    echo "DURATION=$duration" > "${CONFIG[AUDIO_INFO]}"
    echo "SAMPLE_RATE=$sample_rate" >> "${CONFIG[AUDIO_INFO]}"
    echo "CHANNELS=$channels" >> "${CONFIG[AUDIO_INFO]}"
    
    # Store key values in CONFIG for easy access
    CONFIG[AUDIO_DURATION]="$duration"
    CONFIG[AUDIO_SAMPLE_RATE]="$sample_rate"
    CONFIG[AUDIO_CHANNELS]="$channels"
    
    log_info "Audio duration: $duration seconds"
    log_info "Sample rate: $sample_rate Hz"
    log_info "Channels: $channels"
}

# Choose the best visualization mode based on audio characteristics
determine_optimal_visualization() {
    log_info "Determining optimal visualization mode..."
    
    # Simple spectrum analysis to detect dominant characteristics
    execute_command "frequency analysis" "${CONFIG[ERROR_LOG]}" false \
        ffmpeg -v quiet -i "${CONFIG[INPUT]}" -filter_complex "showspectrum=s=100x100" -frames:v 1 -f null - 2>/dev/null
    
    # Based on frequency analysis and channels, set the most appropriate mode
    if [[ "${CONFIG[AUDIO_CHANNELS]}" -gt 1 ]]; then
        if (( RANDOM % 10 < 8 )); then
            # 80% chance for combined mode
            CONFIG[VIZ_MODE]="combined"
            log_info "Selected mode: combined (based on multi-channel audio)"
        else
            # 20% chance for an exotic mode
            local exotic_modes=("fractal_soundscape" "neural_circuit" "vector_field" "digital_rain")
            CONFIG[VIZ_MODE]="${exotic_modes[RANDOM % ${#exotic_modes[@]}]}"
            log_info "Selected exotic mode: ${CONFIG[VIZ_MODE]} (based on multi-channel audio)"
        fi
    else
        if (( RANDOM % 10 < 7 )); then
            # 70% chance for spectrum mode
            CONFIG[VIZ_MODE]="spectrum"
            log_info "Selected mode: spectrum (based on mono audio)"
        else
            # 30% chance for an exotic mode
            local exotic_modes=("quantum_flux" "time_warp" "dimension_fold" "atomic_resonance")
            CONFIG[VIZ_MODE]="${exotic_modes[RANDOM % ${#exotic_modes[@]}]}"
            log_info "Selected exotic mode: ${CONFIG[VIZ_MODE]} (based on mono audio)"
        fi
    fi
}

# =============================================================================
# FILTER CHAIN MANAGEMENT
# =============================================================================

# Centralized filter string generation with improved readability
build_filter_chain() {
    local mode="${CONFIG[VIZ_MODE]}"
    local width="${CONFIG[VIZ_WIDTH]}"
    local height="${CONFIG[VIZ_HEIGHT]}"
    local color="${CONFIG[COLOR_SCHEME]}"
    local fps="${CONFIG[FPS]}"
    
    # Common filter parameters - reduces repetition
    local filter_params="s=${width}x${height}:fps=${fps}"
    local filter_complex=""
    
    case "$mode" in
        "spectrum")
            filter_complex="[0:a]showspectrum=${filter_params}:slide=scroll:mode=combined:scale=log:color=${color},format=rgb24[v]"
            ;;
            
        "waveform")
            filter_complex="[0:a]showwaves=${filter_params}:mode=p2p:n=30:draw=full:colors=0x00FFFF:rate=${fps},format=rgb24[v]"
            ;;
            
        "combined") 
            # Calculate component heights proportionally
            local spec_height=$((height/2))
            local wave_height=$((height/3))
            local vol_height=$((height/6))
            
            # Build filter complex in a more readable way
            filter_complex="[0:a]asplit=3[a1][a2][a3];"
            filter_complex+="[a1]showspectrum=s=${width}x${spec_height}:mode=combined:slide=scroll:scale=log:color=${color}:fps=${fps}[spectrum];"
            filter_complex+="[a2]showwaves=s=${width}x${wave_height}:mode=p2p:n=30:rate=${fps}:draw=full:colors=0x00FFFF[waves];"
            filter_complex+="[a3]showvolume=f=0.8:b=4:w=${width}:h=${vol_height}:c=0xFFFFFF[volume];"
            filter_complex+="[spectrum][waves]vstack[upper];"
            filter_complex+="[upper][volume]vstack[combined];"
            filter_complex+="[combined]hue=h=t*5[colored];"
            filter_complex+="[colored]format=rgb24[v]"
            ;;
            
        "multi_view")
            local cell_width=$((width/2))
            local cell_height=$((height/2))
            
            filter_complex="[0:a]asplit=4[a1][a2][a3][a4];"
            filter_complex+="[a1]showspectrum=s=${cell_width}x${cell_height}:mode=combined:slide=scroll:scale=log:color=rainbow:fps=${fps}[sp];"
            filter_complex+="[a2]showwaves=s=${cell_width}x${cell_height}:mode=p2p:n=30:rate=${fps}:colors=0x00FFFF[wv];"
            filter_complex+="[a3]showspectrum=s=${cell_width}x${cell_height}:mode=combined:slide=scroll:scale=sqrt:color=hue:fps=${fps}[sp2];"
            filter_complex+="[a4]showwaves=s=${cell_width}x${cell_height}:mode=cline:rate=${fps}:colors=0xFFFFFF[wv2];"
            filter_complex+="[sp][wv]hstack[top];"
            filter_complex+="[sp2][wv2]hstack[bottom];"
            filter_complex+="[top][bottom]vstack[grid];"
            filter_complex+="[grid]format=rgb24[v]"
            ;;

        # EXOTIC VISUALIZATION MODES START HERE
        "fractal_soundscape")
            filter_complex="[0:a]asplit=2[a1][a2];"
            filter_complex+="[a1]astats=metadata=1:reset=1,ametadata=mode=print:key=lavfi.astats.Overall.RMS_level[stats];"
            filter_complex+="[a2]showcqt=size=${width}x${height}:count=8:csp=bt709:bar_g=2[cqt];"
            filter_complex+="color=s=${width}x${height}:c=black[base];"
            filter_complex+="[base][stats]mandelbrot=size=${width}x${height}:rate=${fps}:inner=mincol:outer=cycle:start_scale=0.01:end_scale=0.05:end_pt=-1.313575+-0.0537015i[fractal];"
            filter_complex+="[fractal][cqt]blend=all_mode=overlay:all_opacity=0.5,format=rgb24[v]"
            ;;
            
        "neural_circuit")
            filter_complex="[0:a]asplit=2[a1][a2];"
            filter_complex+="[a1]aphasemeter=s=${width}x${height}:mpc=0.5[phase];"
            filter_complex+="[phase]edgedetect=mode=canny:low=0.1:high=0.4[edges];"
            filter_complex+="[edges]lutyuv=y='clipval(val,minval,maxval*(key+1)/10)':u=maxval:v=maxval[bright];"
            filter_complex+="[a2]showcqt=s=${width}x${height}:count=8:csp=bt709[cqt];"
            filter_complex+="[bright][cqt]blend=all_mode=screen:all_opacity=0.6,format=rgb24[v]"
            ;;
            
        "vector_field")
            filter_complex="[0:a]asplit=2[a1][a2];"
            filter_complex+="[a1]avectorscope=s=${width}x${height}:mode=lissajous_xy:zoom=1.5:draw=line[vector];"
            filter_complex+="[vector]hue=H=t*45:s=t+1[colored_vector];"
            filter_complex+="[a2]showcqt=s=${width}x${height}:count=1:csp=bt709:bar_g=2[cqt];"
            filter_complex+="[colored_vector][cqt]blend=all_mode=lighten:all_opacity=0.7,format=rgb24[v]"
            ;;
            
        "digital_rain")
            filter_complex="[0:a]asplit=2[a1][a2];"
            filter_complex+="[a1]showspectrum=s=${width}x${height}:slide=scroll:mode=combined:scale=log:color=channel[spectrum];"
            filter_complex+="[spectrum]crop=iw:${height}/2:0:0[top_spectrum];"
            filter_complex+="[top_spectrum]tile=1x2[tiled];"
            filter_complex+="[tiled]scroll=vertical=0.005*sin(t*0.1)[scrolled];"
            filter_complex+="[scrolled]edgedetect=mode=colormix:low=0.1:high=0.4[edge];"
            filter_complex+="[edge]lutrgb=g=val*1.5:b=val*0.5[green];"
            filter_complex+="[a2]showvolume=f=1:b=4:w=${width}:h=${height}/6:c=0x00FF00[volume];"
            filter_complex+="[green][volume]vstack,format=rgb24[v]"
            ;;
            
        "quantum_flux")
            filter_complex="[0:a]asplit=2[a1][a2];"
            filter_complex+="[a1]oscilloscope=s=${width}x${height}:draw=scale[scope];"
            filter_complex+="color=s=${width}x${height}:c=black,geq=random(1):128:128[noise];"
            filter_complex+="[noise][scope]blend=all_mode=screen:all_opacity=0.8[base];"
            filter_complex+="[a2]showcqt=s=${width}x${height}:count=4:csp=bt709[cqt];"
            filter_complex+="[base][cqt]blend=all_mode=addition:all_opacity=0.3,format=rgb24[v]"
            ;;
            
        "time_warp")
            filter_complex="[0:a]asplit=2[a1][a2];"
            filter_complex+="[a1]showspectrum=s=${width}x${height}:slide=scroll:mode=combined:scale=log:color=rainbow[spectrum];"
            filter_complex+="[spectrum]tblend=all_mode=grainmerge:all_opacity=0.7[blended];"
            filter_complex+="[a2]showwaves=s=${width}x${height}:mode=cline:n=80:draw=full:colors=0xFFFFFF[waves];"
            filter_complex+="[blended][waves]blend=all_mode=overlay:all_opacity=0.4[temp];"
            filter_complex+="[temp]hue=h=t*10:s=1+0.5*sin(t*0.25),format=rgb24[v]"
            ;;
            
        "dimension_fold")
            filter_complex="[0:a]asplit=2[a1][a2];"
            filter_complex+="[a1]showwaves=s=${width}x${height}:mode=p2p:n=50:draw=full:colors=0xFFFFFF[waves];"
            filter_complex+="[waves]kaleidoscope=angle=0:patterns=8:mirror=1[kaleid];"
            filter_complex+="[a2]showspectrum=s=${width}x${height}:mode=combined[spectrum];"
            filter_complex+="[kaleid][spectrum]blend=all_mode=screen:all_opacity=0.7,format=rgb24[v]"
            ;;
            
        "atomic_resonance")
            filter_complex="[0:a]asplit=2[a1][a2];"
            filter_complex+="color=s=${width}x${height}:c=black,format=rgba[bg];"
            filter_complex+="[bg][a1]avectorscope=s=${width}x${height}:mode=lissajous_xy:zoom=1.5:draw=dot:scale=sqrt[vector];"
            filter_complex+="[a2]showcqt=s=${width}x${height}:count=6:csp=bt709[cqt];"
            filter_complex+="[vector][cqt]blend=all_mode=screen:all_opacity=0.5[temp];"
            filter_complex+="[temp]rotate=t*0.05:fillcolor=0x00000000[rotated];"
            filter_complex+="[rotated]hue=h=t*20,format=rgb24[v]"
            ;;
            
        *)
            log_error "Unsupported visualization mode: $mode"
            return 1
            ;;
    esac
    
    # Return the filter complex
    echo "$filter_complex"
    return 0
}

# Generate a fallback filter for exotic modes
generate_fallback_filter() {
    local mode="${CONFIG[VIZ_MODE]}"
    local width="${CONFIG[VIZ_WIDTH]}"
    local height="${CONFIG[VIZ_HEIGHT]}"
    local color="${CONFIG[COLOR_SCHEME]}"
    local fps="${CONFIG[FPS]}"
    
    # Generate a simpler but visually similar fallback filter
    case "$mode" in
        "fractal_soundscape"|"neural_circuit")
            # Fallback to spectrum with edge detection
            echo "[0:a]showspectrum=s=${width}x${height}:slide=scroll:mode=combined:scale=log:color=${color},edgedetect=mode=colormix,format=rgb24[v]"
            ;;
        "vector_field"|"atomic_resonance")
            # Fallback to vectorscope (simpler version)
            echo "[0:a]avectorscope=s=${width}x${height}:mode=lissajous_xy:draw=line,format=rgb24[v]"
            ;;
        "digital_rain"|"quantum_flux")
            # Fallback to waveform with green tint
            echo "[0:a]showwaves=s=${width}x${height}:mode=p2p:n=40:colors=0x00FF00,lutrgb=g=val*1.5:b=val*0.3,format=rgb24[v]"
            ;;
        "time_warp"|"dimension_fold")
            # Fallback to spectrum with color effects
            echo "[0:a]showspectrum=s=${width}x${height}:slide=scroll:mode=combined:scale=log:color=rainbow,hue=h=t*5:s=t/10+1,format=rgb24[v]"
            ;;
        *)
            # Default fallback for any other mode
            echo "[0:a]showspectrum=s=${width}x${height}:slide=scroll:mode=combined:scale=log:color=${color},format=rgb24[v]"
            ;;
    esac
}

# =============================================================================
# VISUALIZATION GENERATION
# =============================================================================

# Generate the ASCII visualization
generate_visualization() {
    local input="${CONFIG[INPUT]}"
    local output_file="${CONFIG[ASCII_FILE]}"
    local frames_option=""
    
    log_info "Generating ASCII visualization using mode: ${CONFIG[VIZ_MODE]}"
    
    # Set max frames option if specified
    if [[ "${CONFIG[MAX_FRAMES]}" -gt 0 ]]; then
        frames_option="-frames:v ${CONFIG[MAX_FRAMES]}"
        log_info "Processing ${CONFIG[MAX_FRAMES]} frames"
    fi
    
    # Get filter complex
    local filter_complex=$(build_filter_chain)
    [[ $? -ne 0 ]] && return 1
    
    # Generate ASCII art - first try with the selected mode
    if ! generate_ascii_with_filter "$filter_complex" "$frames_option"; then
        log_warning "Primary visualization failed, trying fallback..."
        
        # Fallback to a simpler filter
        local fallback_filter=$(generate_fallback_filter)
        
        if ! generate_ascii_with_filter "$fallback_filter" "$frames_option"; then
            # If both the primary and first fallback fail, use the simplest possible filter
            log_warning "Fallback visualization also failed, trying basic visualization..."
            CONFIG[VIZ_MODE]="spectrum"
            filter_complex=$(build_filter_chain)
            
            if ! generate_ascii_with_filter "$filter_complex" "$frames_option"; then
                log_error "All visualization attempts failed"
                return 1
            fi
            
            log_success "Basic visualization succeeded"
        else
            log_success "Fallback visualization succeeded"
        fi
    else
        log_success "ASCII visualization generated successfully"
    fi
    
    # Create a small preview for verification if in debug mode
    if [[ "${CONFIG[DEBUG]}" == true ]]; then
        create_debug_preview
    fi
    
    return 0
}

# Execute the FFmpeg command to generate ASCII art
generate_ascii_with_filter() {
    local filter="$1"
    local frames_opt="$2"
    local error_file="${CONFIG[TEMP_DIR]}/ffmpeg_error.log"
    
    log_info "Running FFmpeg for ASCII generation..."
    
    # Execute FFmpeg with the specified filter
    execute_command "ASCII generation" "$error_file" false \
        ffmpeg -i "${CONFIG[INPUT]}" -filter_complex "$filter" -map "[v]" $frames_opt \
        -f caca -charset "${CONFIG[CHARSET]}" -algorithm "${CONFIG[DITHER_ALGO]}" \
        -color full16 "${CONFIG[ASCII_FILE]}"
    
    # Check if the output was created successfully
    if [[ ! -f "${CONFIG[ASCII_FILE]}" ]] || [[ ! -s "${CONFIG[ASCII_FILE]}" ]]; then
        return 1
    fi
    
    return 0
}

# Create a debug preview of the ASCII output
create_debug_preview() {
    log_debug "Creating debug preview..."
    
    execute_command "debug preview creation" "${CONFIG[ERROR_LOG]}" false \
        ffmpeg -f lavfi -i "color=c=black:s=640x480:r=30" \
        -vf "drawtext=fontfile=${CONFIG[FONT]}:fontsize=10:fontcolor=white:x=10:y=10:textfile=${CONFIG[ASCII_FILE]}" \
        -t 5 -c:v libx264 -preset ultrafast "${CONFIG[PREVIEW_FILE]}" 2>/dev/null
    
    log_debug "Debug preview created: ${CONFIG[PREVIEW_FILE]}"
}

# =============================================================================
# VIDEO RENDERING
# =============================================================================

# Master function for the rendering process
render_final_video() {
    log_info "Preparing to render final video..."
    
    # 1. Calculate optimal font size
    local font_size=$(calculate_font_size "${CONFIG[OUTPUT_HEIGHT]}")
    log_debug "Using font size: $font_size"
    
    # 2. Get encoding parameters
    local encoding_params=$(get_encoding_params "${CONFIG[VIDEO_QUALITY]}")
    log_info "Rendering with quality: ${CONFIG[VIDEO_QUALITY]} ($encoding_params)"
    
    # 3. Render ASCII art as video
    if ! render_ascii_video "$font_size" "$encoding_params"; then
        log_error "Failed to render ASCII video"
        return 1
    fi
    
    # 4. Add audio to the video
    if ! add_audio_to_video; then
        log_error "Failed to add audio to video"
        return 1
    fi
    
    log_success "Final video rendered successfully: ${CONFIG[OUTPUT]}"
    return 0
}

# Calculate optimal font size based on resolution
calculate_font_size() {
    local height="$1"
    local font_size=$(echo "scale=0; ($height / 60)" | bc)
    [[ "$font_size" -lt 10 ]] && font_size=10
    echo "$font_size"
}

# Get encoding parameters based on quality setting
get_encoding_params() {
    local quality="$1"
    
    case "$quality" in
        "draft")    echo "preset=ultrafast:crf=28" ;;
        "normal")   echo "preset=medium:crf=23" ;;
        "high")     echo "preset=slow:crf=18" ;;
        "ultra")    echo "preset=veryslow:crf=15" ;;
        *)          
            log_warning "Unknown quality: $quality, using defaults"
            echo "preset=medium:crf=23"
            ;;
    esac
}

# Render the ASCII art as a video
render_ascii_video() {
    local font_size="$1"
    local encoding="$2"
    local preset=$(echo "$encoding" | cut -d':' -f1 | cut -d'=' -f2)
    local crf=$(echo "$encoding" | cut -d':' -f2 | cut -d'=' -f2)
    
    # Get appropriate effect filter
    local vf_effects=$(build_effect_filter "$font_size")
    
    log_info "Creating video with ASCII art..."
    
    # Render the video
    execute_command "video rendering" "${CONFIG[TEMP_DIR]}/render_error.log" \
        ffmpeg -f lavfi -i "color=c=black:s=${CONFIG[OUTPUT_WIDTH]}x${CONFIG[OUTPUT_HEIGHT]}:r=${CONFIG[FPS]}" \
        -vf "$vf_effects" -c:v libx264 -preset "$preset" -crf "$crf" -pix_fmt yuv420p \
        "${CONFIG[TEMP_VIDEO]}"
    
    return $?
}

# Build the appropriate effect filter based on effect level
build_effect_filter() {
    local font_size="$1"
    local level="${CONFIG[EFFECT_LEVEL]}"
    local mode="${CONFIG[VIZ_MODE]}"
    
    # Basic text rendering is common to all effect levels
    local base_text="drawtext=fontfile=${CONFIG[FONT]}:fontsize=$font_size:fontcolor=white:x=10:y=10:textfile=${CONFIG[ASCII_FILE]}"
    
    # Customize effects based on mode and level
    case "$level" in
        "minimal")
            # For minimal, just use the base text
            echo "$base_text"
            ;;
            
        "medium") 
            # For medium, add some color effects based on the visualization mode
            case "$mode" in
                "fractal_soundscape"|"neural_circuit")
                    echo "$base_text,hue=h=t*5:s=1.1:b=1.05"
                    ;;
                "vector_field"|"atomic_resonance")
                    echo "$base_text,hue=h=t*10:s=1.2"
                    ;;
                "digital_rain"|"quantum_flux")
                    echo "$base_text,hue=h=120:s=1.3"  # Green tint for matrix-like modes
                    ;;
                "time_warp"|"dimension_fold")
                    echo "$base_text,hue=h=t*7:s=t/50+1:b=1.05"
                    ;;
                *)
                    echo "$base_text,hue=h=t*5:s=1.1"
                    ;;
            esac
            ;;
            
        "intense")
            # For intense, add more pronounced effects based on the visualization mode
            case "$mode" in
                "fractal_soundscape"|"neural_circuit")
                    echo "$base_text,hue=h=t*10:s=t/100+1:b=1.1,eq=brightness=0.03:contrast=1.2:saturation=1.2"
                    ;;
                "vector_field"|"atomic_resonance")
                    echo "$base_text,hue=h=t*20:s=t/80+1.2,eq=brightness=0.05:contrast=1.3:saturation=1.4"
                    ;;
                "digital_rain"|"quantum_flux")
                    # Matrix-style effect with scan lines
                    echo "$base_text,lutrgb=g=val*1.6:r=val*0.2:b=val*0.2,vignette=angle=PI/6,drawgrid=width=100:height=100:color=0x00440022@0.1"
                    ;;
                "time_warp"|"dimension_fold")
                    # Psychedelic time-warping effects
                    echo "$base_text,hue=h=t*15:s=1+0.6*sin(t*0.5):b=1+0.2*sin(t*0.2),eq=brightness=0.02:contrast=1.3:saturation=1.5"
                    ;;
                *)
                    echo "$base_text,hue=h=t*10:s=t/100+1:b=1.1,eq=brightness=0.03:contrast=1.2:saturation=1.2"
                    ;;
            esac
            ;;
            
        *)
            log_warning "Unknown effect level: $level, using defaults"
            echo "$base_text"
            ;;
    esac
}

# Add the original audio to the video
add_audio_to_video() {
    log_info "Adding audio to video..."
    
    # Calculate audio duration for proper sync
    local duration_arg=""
    if [[ -n "${CONFIG[AUDIO_DURATION]}" ]] && [[ "${CONFIG[AUDIO_DURATION]}" != "N/A" ]]; then
        duration_arg="-t ${CONFIG[AUDIO_DURATION]}"
    fi
    
    # Mux audio and video
    execute_command "audio addition" "${CONFIG[TEMP_DIR]}/mux_error.log" \
        ffmpeg -i "${CONFIG[TEMP_VIDEO]}" -i "${CONFIG[INPUT]}" -map 0:v -map 1:a \
        -c:v copy -c:a aac -b:a 320k -shortest $duration_arg "${CONFIG[OUTPUT]}"
    
    return $?
}

# =============================================================================
# ARGUMENT PARSING
# =============================================================================

# Parse command line arguments
parse_arguments() {
    # Check for minimum required arguments
    if [[ "$#" -lt 2 ]]; then
        show_usage
        return 1
    fi
    
    # Get input and output files
    CONFIG[INPUT]="$1"
    CONFIG[OUTPUT]="$2"
    shift 2
    
    # Process options using a more structured approach
    while [[ "$#" -gt 0 ]]; do
        case "$1" in
            --mode)     CONFIG[VIZ_MODE]="$2"; shift 2 ;;
            --colors)   CONFIG[COLOR_SCHEME]="$2"; shift 2 ;;
            --charset)  CONFIG[CHARSET]="$2"; shift 2 ;;
            --dither)   CONFIG[DITHER_ALGO]="$2"; shift 2 ;;
            --effects)  CONFIG[EFFECT_LEVEL]="$2"; shift 2 ;;
            --width)    CONFIG[VIZ_WIDTH]="$2"; shift 2 ;;
            --height)   CONFIG[VIZ_HEIGHT]="$2"; shift 2 ;;
            --quality)  CONFIG[VIDEO_QUALITY]="$2"; shift 2 ;;
            --fps)      CONFIG[FPS]="$2"; shift 2 ;;
            --max-frames) CONFIG[MAX_FRAMES]="$2"; shift 2 ;;
            --fallback) CONFIG[FORCE_FALLBACK]=true; shift ;;
            --debug)    CONFIG[DEBUG]=true; shift ;;
            --help)     show_usage; return 1 ;;
            *)          
                log_error "Unknown option: $1"
                show_usage
                return 1
                ;;
        esac
    done
    
    return 0
}

# Show usage information
show_usage() {
    cat << EOF
AsciiSymphony: Advanced Modular ASCII Art Audio Visualizer (Enhanced Edition)
Usage: $0 input.flac output.mp4 [options]

Options:
  --mode MODE         Visualization mode (adaptive, spectrum, waveform, combined, multi_view,
                      fractal_soundscape, neural_circuit, vector_field, digital_rain,
                      quantum_flux, time_warp, dimension_fold, atomic_resonance)
  --colors SCHEME     Color scheme (rainbow, thermal, matrix, grayscale)
  --charset SET       Character set (ascii, blocks, shades)
  --dither ALGO       Dithering algorithm (fstein, ordered4, random)
  --effects LEVEL     Effect intensity (minimal, medium, intense)
  --width WIDTH       Visualization width
  --height HEIGHT     Visualization height
  --quality LEVEL     Output video quality (draft, normal, high, ultra)
  --fps FPS           Frames per second (default: 25)
  --max-frames N      Only process N frames (default: entire file)
  --fallback          Force fallback mode (simpler but more reliable)
  --debug             Enable debug mode
  --help              Show this help message
EOF
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

# Main function with clearer flow
main() {
    echo "=========================================="
    echo "AsciiSymphony: Advanced Audio Visualizer"
    echo "Enhanced Edition with Exotic Visualizations"
    echo "=========================================="
    
    # Initialize configuration defaults
    initialize_config
    
    # Parse command line arguments
    parse_arguments "$@" || return $?
    
    # Validate configuration
    validate_config || return $?
    
    # Check dependencies
    check_dependencies || return $?
    
    # Setup resources (temp directories, etc.)
    setup_resources || return $?
    
    # Set trap for cleanup
    trap cleanup_resources EXIT INT TERM
    
    # Main processing pipeline
    analyze_audio || return $?
    generate_visualization || return $?
    render_final_video || return $?
    
    echo "=========================================="
    echo "Visualization complete: ${CONFIG[OUTPUT]}"
    echo "=========================================="
    
    return 0
}

# Execute the main function
main "$@"
exit $?