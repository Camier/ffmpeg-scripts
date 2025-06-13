#!/bin/bash
# Requires Bash 4.2+ for associative arrays and advanced features
set -euo pipefail

# =============================================================================
# GLOBAL VARIABLES AND LOGGING
# =============================================================================

# Set up directories (use local directory if HOME is not set)
LOGDIR="${HOME:-.}/.asymphony/logs"
PRESET_DIR="${HOME:-.}/.asymphony/presets"
DEFAULT_PRESET_FILE="$PRESET_DIR/default.preset"
PRESET_FORMAT_VERSION="1.0"

# Ensure log and preset directories exist
mkdir -p "$LOGDIR" "$PRESET_DIR"

log() {
    echo "[LOG] $*" >&2
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [LOG] $*" >> "${LOGDIR}/asymphony.log"
}

# =============================================================================
# RUNTIME EXECUTION
# =============================================================================

check_for_updates() {
    # Checks for the latest version from a remote endpoint (e.g., GitHub)
    local version_url="https://raw.githubusercontent.com/asciisymphony/docs/main/VERSION"
    local latest_version
    if command -v curl >/dev/null; then
        latest_version=$(curl -fsSL "$version_url" 2>/dev/null | head -n1)
    elif command -v wget >/dev/null; then
        latest_version=$(wget -qO- "$version_url" 2>/dev/null | head -n1)
    else
        return
    fi
    if [[ -n "$latest_version" && "$latest_version" != "2.1.1" ]]; then
        echo "--------------------------------------------------"
        echo "  Update available! Latest version: $latest_version"
        echo "  Visit https://github.com/asciisymphony/docs"
        echo "--------------------------------------------------"
    fi
}

interactive_menu() {
    check_for_updates
    echo "=============================================="
    echo "   AsciiSymphony Pro: Interactive Menu"
    echo "=============================================="
    echo "Please select an option:"
    echo "1) Visualize audio file"
    echo "2) Live audio visualization"
    echo "3) List available presets"
    echo "4) Load preset"
    echo "5) Save current settings as preset"
    echo "6) List audio input devices"
    echo "7) Help"
    echo "8) Exit"
    echo "----------------------------------------------"
    read -rp "Enter your choice [1-8]: " choice

    case "$choice" in
        1)
            read -rp "Enter input audio file path: " input
            read -rp "Enter output video file path: " output
            set -- "$input" "$output"
            ;;
        2)
            set -- --live
            ;;
        3)
            list_presets
            exit 0
            ;;
        4)
            read -rp "Enter preset name to load: " preset
            set -- --load-preset "$preset"
            ;;
        5)
            read -rp "Enter name for new preset: " preset
            set -- --save-preset "$preset"
            ;;
        6)
            list_audio_devices
            exit 0
            ;;
        7)
            show_help
            exit 0
            ;;
        8)
            echo "Exiting."
            exit 0
            ;;
        *)
            echo "Invalid choice."
            exit 1
            ;;
    esac
    # Continue with main logic using new arguments
    main "$@"
    exit 0
}

warning() {
    echo "[WARNING] $*" >&2
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [WARNING] $*" >> "${LOGDIR}/asymphony.log"
}

critical_error() {
    echo "[CRITICAL] $*" >&2
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [CRITICAL] $*" >> "${LOGDIR}/asymphony.log"
    exit 1
}

init_engine() {
    local -gA config=(
        [fps]=30
        [width]=1280
        [height]=720
        [quality]="balanced"
        [encoder]="h264"
        [vulkan]=0
        [hdr]=0
        [gpu]=0
        [latency]="normal"
        [mode]="waves"
        [charset]="unicode"
        [dither]="fstein"
        [hue]=1.5
        [saturation]=1.2
        [bitrate]="auto"
        [live_input]=0
        [sample_rate]=44100
        [channels]=2
        [buffer_size]=1024
        [colors]="thermal"
        [threads]="auto"
    )
    
    detect_hardware || warning "Hardware acceleration disabled"
    parse_args "${@:2}"
}

detect_hardware() {
    # Check Vulkan support with version validation
    if [[ $(ffmpeg -hwaccels 2>&1) =~ vulkan ]]; then
        vulkan_info=$(vulkaninfo --summary 2>/dev/null)
        [[ "$vulkan_info" =~ "apiVersion" ]] && config[vulkan]=1
    fi
    
    # Verify libplacebo actually works
    if [[ $(ffmpeg -v quiet -filters | grep libplacebo) ]]; then
        ffmpeg -v error -f lavfi -i "nullsrc=s=2x2" -vf "libplacebo=tonemap=auto" \
            -frames:v 1 -f null - 2>/dev/null && config[gpu]=1
    fi
    
    # Fallback checks
    if (( config[vulkan] )) && ! (( config[gpu] )); then
        warning "Vulkan detected but libplacebo failed - disabling GPU acceleration"
        config[vulkan]=0
    fi
    
    return 0
}

parse_args() {
    local i=0
    while [[ $i -lt $# ]]; do
        arg="${!i}"
        next_i=$((i+1))
        next_arg="${!next_i}"

        case "$arg" in
            --mode=*)
                config[mode]="${arg#*=}"
                ;;
            --mode)
                config[mode]="$next_arg"
                i=$((i+1))
                ;;
            --fps=*)
                config[fps]="${arg#*=}"
                ;;
            --fps)
                config[fps]="$next_arg"
                i=$((i+1))
                ;;
            --quality=*)
                config[quality]="${arg#*=}"
                ;;
            --quality)
                config[quality]="$next_arg"
                i=$((i+1))
                ;;
            --colors=*)
                config[colors]="${arg#*=}"
                ;;
            --colors)
                config[colors]="$next_arg"
                i=$((i+1))
                ;;
            --charset=*)
                config[charset]="${arg#*=}"
                ;;
            --charset)
                config[charset]="$next_arg"
                i=$((i+1))
                ;;
            --dither=*)
                config[dither]="${arg#*=}"
                ;;
            --dither)
                config[dither]="$next_arg"
                i=$((i+1))
                ;;
            --hue=*)
                config[hue]="${arg#*=}"
                ;;
            --hue)
                config[hue]="$next_arg"
                i=$((i+1))
                ;;
            --saturation=*)
                config[saturation]="${arg#*=}"
                ;;
            --saturation)
                config[saturation]="$next_arg"
                i=$((i+1))
                ;;
            # Additional parameters can be added as needed
        esac
        i=$((i+1))
    done
}

# =============================================================================
# VIDEO PIPELINE ENGINE
# =============================================================================

create_visualization() {
    local filter_graph=$(build_filter_chain)
    local ffmpeg_cmd=( ffmpeg -v info -nostdin -y )
    
    # Check if we're using live input
    if [[ "${config[live_input]}" -eq 1 ]]; then
        setup_live_input
        ffmpeg_cmd+=( "${input_args[@]}" )
    else
        ffmpeg_cmd+=( -i "$input" )
    fi
    
    # Continue with existing filter chain and output
    ffmpeg_cmd+=(
        -lavfi "$filter_graph"
        -f caca -color full -charset "${config[charset]}"
        -algorithm "${config[dither]}" -
    )
    
    {
        time "${ffmpeg_cmd[@]}" || trigger_fallback
    } | postprocess_video
}

build_filter_chain() {
    local chain=()
    [[ "${config[gpu]}" -eq 1 ]] && chain+=("hwupload")
    
    case "${config[mode]}" in
        "spectrosynth")
            # Fallback to a compatible filter chain (multi-band spectrum + waveform)
            chain+=("[0:a]showspectrum=s=${config[width]}x${config[height]}:mode=combined:color=rainbow[spectrum];"
                    "[0:a]showwaves=s=${config[width]}x${config[height]}:mode=line:w=2[wave];"
                    "[spectrum][wave]blend=all_mode=addition,format=rgb24")
            ;;
        "vortex")
            chain+=("rotate=angle='t*2':fillcolor=black@0.5"
                "hue=h='2*PI*t':s=1.5")
            ;;
        "waves")
            chain+=("showwaves=s=${config[width]}x${config[height]}:mode=line,format=rgb24")
            ;;
        "spectrum")
            chain+=("showspectrum=s=${config[width]}x${config[height]}:mode=combined,format=rgb24")
            ;;
        "cqt")
            chain+=("showcqt=s=${config[width]}x${config[height]},format=rgb24")
            ;;
        "combo")
            chain+=("[0:a]showwaves=s=${config[width]}x${config[height]}:mode=line[waves];"
                    "[0:a]showspectrum=s=${config[width]}x${config[height]}:mode=combined[spectrum];"
                    "[waves][spectrum]blend=all_mode=addition,format=rgb24")
            ;;
        "edge")
            chain+=("[0:a]showcqt=s=${config[width]}x${config[height]}[cqt];"
                    "[cqt]edgedetect=low=0.1:high=0.4,format=rgb24")
            ;;
        "kaleidoscope")
            chain+=("[0:a]showspectrum=s=${config[width]}x${config[height]}:slide=replace:mode=combined,format=yuv420p[vis];"
                    "[vis]kaleidoscope=pattern=1:angle=0,format=rgb24")
            ;;
        "neural")
            # Neural network-inspired visualization
            chain+=("[0:a]asplit=3[bass][mid][high],"
                   "[bass]bandpass=f=100:width_type=h:w=200[filtered_bass],"
                   "[mid]bandpass=f=1000:width_type=h:w=800[filtered_mid],"
                   "[high]highpass=f=4000[filtered_high],"
                   "[filtered_bass]showwaves=s=${config[width]}x$(( ${config[height]} / 3 )):mode=cline:colors=0x00ffff[wave_bass],"
                   "[filtered_mid]showspectrum=s=${config[width]}x$(( ${config[height]} / 3 )):slide=scroll:mode=combined:color=rainbow[spec_mid],"
                   "[filtered_high]showcqt=s=${config[width]}x$(( ${config[height]} / 3 )):count=8:gamma=5[cqt_high],"
                   "[wave_bass][spec_mid][cqt_high]vstack=inputs=3,"
                   "hue='h=t/20':s='1+sin(t/10)/4',"
                   "boxblur=10:enable='if(eq(mod(t,4),0),1,0)',format=rgb24")
            ;;
        "typography")
            # Typography-based audio reactive visualization
            # Securely create temporary lyrics file
            local lyricfile=$(mktemp /tmp/lyrics.XXXXXXXXXX.txt)
            chmod 600 "$lyricfile"
            cat > "$lyricfile" <<EOF
♫ ♪ ♬ ♩ ♭
ASCII SYMPHONY
VISUAL SOUNDSCAPE
AUDIO WAVES
DIGITAL RHYTHM
SONIC PATTERNS
EOF
            chain+=("[0:a]asplit=2[a1][a2],"
                   "[a1]showwaves=s=${config[width]}x${config[height]}:mode=cline:draw=full:colors=0xffffff[bg],"
                   "[a2]avectorscope=s=${config[width]}x${config[height]}:zoom=1.5:draw=full[fg],"
                   "[bg][fg]blend=all_mode=screen:all_opacity=0.8,format=yuv422p,"
                   "drawtext=text='AUDIO':fontsize=w/5:x=(w-text_w)/2:y=(h-text_h)/2:"
                   "fontcolor=ffffff@0.8:enable='between(mod(t,2),0,0.3)',"
                   "drawtext=text='SYMPHONY':fontsize=w/8:x=(w-text_w)/2:y=(h-text_h)/2+h/4:"
                   "fontcolor=00ffff@0.6:enable='between(mod(t,2),0.3,0.6)',"
                   "drawtext=textfile=${lyricfile}:reload=1:fontsize='w/20*sin(t)+w/10':"
                   "x='w/2+w/4*sin(t/2)':y='h/2+h/4*cos(t/2)':fontcolor=ffffff@0.7,"
                   "format=rgb24")
            ;;
        "particles")
            # Particle system visualization
            chain+=("[0:a]asplit=2[a][b],"
                   "[a]showwaves=s=${config[width]}x${config[height]}:mode=cline:rate=60[waves],"
                   "[b]showspectrum=s=${config[width]}x${config[height]}:slide=scroll:mode=combined[spectrum],"
                   "[waves][spectrum]blend=all_mode=screen:all_opacity=0.5,"
                   "format=rgba,"
                   "split=3[s1][s2][s3],"
                   "[s1]rotate=angle='t/10':fillcolor=0x00000000[r1],"
                   "[s2]rotate=angle='-t/15':fillcolor=0x00000000[r2],"
                   "[s3]rotate=angle='sin(t)*PI/4':fillcolor=0x00000000[r3],"
                   "[r1][r2][r3]blend=all_mode=lighten,format=rgb24")
            ;;
        "fractal")
            # Fractal-inspired audio visualization
            chain+=("[0:a]showcqt=s=${config[width]}x${config[height]}:count=12:"
                   "attack=0.5:gamma=4:sono_v=fim,"
                   "split=4[q1][q2][q3][q4],"
                   "[q1]crop=iw/2:ih/2:0:0,scale=${config[width]}x${config[height]}[c1],"
                   "[q2]crop=iw/2:ih/2:iw/2:0,scale=${config[width]}x${config[height]}[c2],"
                   "[q3]crop=iw/2:ih/2:0:ih/2,scale=${config[width]}x${config[height]}[c3],"
                   "[q4]crop=iw/2:ih/2:iw/2:ih/2,scale=${config[width]}x${config[height]}[c4],"
                   "[c1][c2]hstack[top],"
                   "[c3][c4]hstack[bottom],"
                   "[top][bottom]vstack,hue='h=t/15',format=rgb24")
            ;;
        *)
            warning "Unknown visualization mode: ${config[mode]}"
            warning "Using default waveform visualization"
            chain+=("showwaves=s=${config[width]}x${config[height]}:mode=line,format=rgb24")
            ;;
    esac
    
    [[ "${config[hdr]}" -eq 1 ]] && chain+=("libplacebo=tonemap=auto")
    printf "%s," "${chain[@]}"
}

postprocess_video() {
    local encoder_args=$(get_encoder_settings)
    ffmpeg -v warning -f rawvideo -pix_fmt rgb24 \
        -s "${config[width]}x${config[height]}" \
        -i - ${encoder_args} \
        -metadata title="AsciiSymphony Pro" \
        -movflags +faststart \
        "$output"
}

get_encoder_settings() {
    case "${config[encoder]}" in
        "h264")
            echo "-c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p"
            ;;
        "vp9")
            echo "-c:v libvpx-vp9 -crf 30 -b:v 0 -pix_fmt yuv420p"
            ;;
        "gif")
            echo "-filter_complex \"[0:v]split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse\" -f gif"
            ;;
        *)
            echo "-c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p"
            ;;
    esac
}

# =============================================================================
# LIVE AUDIO PROCESSING
# =============================================================================

detect_audio_devices() {
    log "Detecting audio input devices..."
    case "$(uname -s)" in
        Linux)
            # For PulseAudio/PipeWire systems
            if command -v pactl >/dev/null; then
                mapfile -t AUDIO_DEVICES < <(pactl list sources short | grep -v '.monitor' | awk '{print $1 " " $2}')
                config[audio_system]="pulse"
            # For ALSA systems
            elif command -v arecord >/dev/null; then
                mapfile -t AUDIO_DEVICES < <(arecord -L | grep -v 'plughw' | grep -v 'default')
                config[audio_system]="alsa"
            fi
            ;;
        Darwin)
            # For macOS
            if command -v ffmpeg >/dev/null; then
                mapfile -t AUDIO_DEVICES < <(ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | 
                                          grep -oE '^\[AVFoundation.*\] \[.*\] \[.*\]' | 
                                          grep 'input device')
                config[audio_system]="avfoundation"
            fi
            ;;
        MINGW*|MSYS*)
            # For Windows
            if command -v ffmpeg >/dev/null; then
                mapfile -t AUDIO_DEVICES < <(ffmpeg -list_devices true -f dshow -i dummy 2>&1 | 
                                          grep "Alternative name" | 
                                          sed 's/.*"\(.*\)".*/\1/')
                config[audio_system]="dshow"
            fi
            ;;
    esac
    
    if [[ ${#AUDIO_DEVICES[@]} -eq 0 ]]; then
        warning "No audio input devices detected"
        return 1
    fi
    
    log "Found ${#AUDIO_DEVICES[@]} audio input devices"
    return 0
}

setup_live_input() {
    local device="${config[audio_device]}"
    local rate="${config[sample_rate]:-44100}"
    local buffer="${config[buffer_size]:-1024}"
    local channels="${config[channels]:-2}"
    
    # Construct FFmpeg input arguments based on detected audio system
    case "${config[audio_system]}" in
        pulse)
            input_args=(-f pulse -i "$device" 
                       -sample_rate "$rate" -channels "$channels")
            ;;
        alsa)
            input_args=(-f alsa -i "$device" 
                       -sample_rate "$rate" -channels "$channels")
            ;;
        avfoundation)
            input_args=(-f avfoundation -i ":$device" 
                       -sample_rate "$rate" -channels "$channels")
            ;;
        dshow)
            input_args=(-f dshow -audio_buffer_size "$buffer" 
                       -i audio="$device" -sample_rate "$rate" -channels "$channels")
            ;;
        *)
            critical_error "Unsupported audio system: ${config[audio_system]}"
            ;;
    esac
    
    # Set real-time processing flags
    if [[ "${config[latency]}" == "low" ]]; then
        input_args+=(-avioflags direct -fflags nobuffer 
                    -flags low_delay -strict experimental)
    fi
    
    log "Live audio input configured: ${config[audio_device]}"
    return 0
}

list_audio_devices() {
    detect_audio_devices
    
    echo "Available audio input devices:"
    echo "-----------------------------"
    for i in "${!AUDIO_DEVICES[@]}"; do
        echo "[$i] ${AUDIO_DEVICES[$i]}"
    done
    
    echo -e "\nUsage: $0 --live [device]"
    echo "Example: $0 --live 0"
}

# =============================================================================
# PRESET MANAGEMENT SYSTEM
# =============================================================================

initialize_preset_system() {
    # Create preset directory if it doesn't exist
    if [[ ! -d "$PRESET_DIR" ]]; then
        mkdir -p "$PRESET_DIR"
        log "Created preset directory: $PRESET_DIR"
        
        # Create default preset
        create_default_preset
    fi
}

create_default_preset() {
    cat > "$DEFAULT_PRESET_FILE" <<EOF
# AsciiSymphony Pro Default Preset
# Version: $PRESET_FORMAT_VERSION
# Created: $(date)

# Visualization settings
mode="waves"
fps="30"
quality="balanced"
colors="thermal"
charset="unicode"
dither="fstein"
hue="1.5"
saturation="1.2"

# Performance settings
threads="$(( $(nproc) / 2 ))"
gpu="auto"
latency="normal"

# Display settings
width="1280"
height="720"
EOF
    
    log "Created default preset"
}

save_preset() {
    local preset_name="$1"
    
    # Validate preset name
    if [[ -z "$preset_name" ]]; then
        warning "No preset name provided"
        echo "Usage: $0 --save-preset PRESET_NAME"
        return 1
    fi
    
    # Add .preset extension if not present
    [[ "$preset_name" != *.preset ]] && preset_name="${preset_name}.preset"
    
    local preset_file="${PRESET_DIR}/${preset_name}"
    
    # Create preset file
    cat > "$preset_file" <<EOF
# AsciiSymphony Pro Preset: $(basename "$preset_name" .preset)
# Version: $PRESET_FORMAT_VERSION
# Created: $(date)

# Visualization settings
mode="${config[mode]}"
fps="${config[fps]}"
quality="${config[quality]}"
colors="${config[colors]}"
charset="${config[charset]}"
dither="${config[dither]}"
hue="${config[hue]}"
saturation="${config[saturation]}"

# Performance settings
threads="${config[threads]}"
gpu="${config[gpu]}"
latency="${config[latency]}"

# Display settings
width="${config[width]}"
height="${config[height]}"

# Custom parameters
$(for key in "${!config[@]}"; do
    # Skip already handled parameters
    case "$key" in
        mode|fps|quality|colors|charset|dither|hue|saturation|threads|gpu|latency|width|height) continue ;;
        *) echo "${key}=\"${config[$key]}\""
    esac
done)
EOF
    
    log "Preset saved: $(basename "$preset_name" .preset)"
    return 0
}

load_preset() {
    local preset_name="$1"
    
    # Validate preset name format
    if [[ ! "$preset_name" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        critical_error "Invalid preset name: must contain only letters, numbers, hyphens and underscores"
    fi

    local preset_file="${PRESET_DIR}/${preset_name}.preset"
    
    # Security checks
    if [[ ! -f "$preset_file" ]]; then
        warning "Preset not found: $preset_name"
        return 1
    fi
    if [[ "$(realpath "$preset_file")" != "$PRESET_DIR"/* ]]; then
        critical_error "Invalid preset path detected - possible directory traversal attempt"
    fi

    log "Loading preset: $preset_name"
    
    # Safe preset loading with validation
    while IFS="=" read -r key value; do
        # Skip comments/empty lines and validate format
        [[ "$key" =~ ^# || -z "$key" ]] && continue
        [[ "$key" =~ [^a-zA-Z0-9_] ]] && continue
        
        # Remove quotes and whitespace
        value="${value//[\"\'\\]/}"
        value="${value//[[:space:]]/}"
        
        # Validate allowed parameters
        case "$key" in
            mode|fps|quality|colors|charset|dither|hue|saturation|threads|gpu|latency|width|height)
                # Validate numerical values
                if [[ "$value" =~ ^[0-9.]+$ ]]; then
                    (( $(echo "$value > 0" | bc -l) )) || continue
                fi
                
                # Validate string values
                case "$key" in
                    mode)
                        [[ "$value" =~ ^(waves|spectrum|cqt|combo|edge|kaleidoscope|spectrosynth|vortex|neural|typography|particles|fractal)$ ]] || continue
                        ;;
                    charset)
                        [[ "$value" =~ ^(unicode|ascii|extended)$ ]] || continue
                        ;;
                    dither)
                        [[ "$value" =~ ^(fstein|ordered2|bayer|none)$ ]] || continue
                        ;;
                    quality)
                        [[ "$value" =~ ^(low|balanced|high|ultra)$ ]] || continue
                        ;;
                esac
                
                config["$key"]="$value"
                ;;
            preset_version)
                [[ "$value" == "$PRESET_FORMAT_VERSION" ]] || warning "Preset version mismatch ($value vs $PRESET_FORMAT_VERSION)"
                ;;
            *)
                warning "Ignoring unknown preset parameter: $key"
                ;;
        esac
    done < <(grep -E '^[^#]' "$preset_file")
    
    log "Preset loaded: $(basename "$preset_name" .preset)"
    return 0
}

list_presets() {
    initialize_preset_system
    
    echo "Available presets:"
    echo "-----------------"
    
    # List all preset files
    for preset_file in "$PRESET_DIR"/*.preset; do
        [[ -f "$preset_file" ]] || continue
        
        # Extract preset name and creation date
        local preset_name=$(basename "$preset_file" .preset)
        local created_date=$(grep "^# Created:" "$preset_file" | sed 's/^# Created: //')
        local mode=$(grep "^mode=" "$preset_file" | sed 's/^mode="//' | sed 's/"$//')
        
        printf "%-20s | %-15s | %s\n" "$preset_name" "$mode" "$created_date"
    done
    
    echo ""
    echo "Usage:"
    echo "  $0 --load-preset PRESET_NAME [input_file] [output_file]"
    echo "  $0 --save-preset PRESET_NAME"
    echo "  $0 --export-preset PRESET_NAME [export_file]"
    echo "  $0 --import-preset IMPORT_FILE"
}

export_preset() {
    local preset_name="$1"
    local export_file="$2"
    
    # Validate preset name
    if [[ -z "$preset_name" ]]; then
        warning "No preset name provided"
        echo "Usage: $0 --export-preset PRESET_NAME [export_file]"
        return 1
    fi
    
    # Add .preset extension if not present
    [[ "$preset_name" != *.preset ]] && preset_name="${preset_name}.preset"
    
    local preset_file="${PRESET_DIR}/${preset_name}"
    
    # Check if preset file exists
    if [[ ! -f "$preset_file" ]]; then
        warning "Preset not found: $preset_name"
        return 1
    fi
    
    # If no export file specified, use preset name
    if [[ -z "$export_file" ]]; then
        export_file="$(basename "$preset_name" .preset).aspreset"
    fi
    
    # Export preset (with base64 encoding for portability)
    log "Exporting preset: $(basename "$preset_name" .preset) to $export_file"
    
    echo "# AsciiSymphony Pro Portable Preset" > "$export_file"
    echo "# Version: $PRESET_FORMAT_VERSION" >> "$export_file"
    echo "# Original: $(basename "$preset_name" .preset)" >> "$export_file"
    echo "# Exported: $(date)" >> "$export_file"
    echo "" >> "$export_file"
    
    base64 "$preset_file" >> "$export_file"
    
    log "Preset exported: $export_file"
    return 0
}

import_preset() {
    local import_file="$1"
    
    # Validate import file
    if [[ -z "$import_file" || ! -f "$import_file" ]]; then
        warning "Import file not found: $import_file"
        echo "Usage: $0 --import-preset IMPORT_FILE"
        return 1
    fi
    
    # Check file format
    if ! grep -q "^# AsciiSymphony Pro Portable Preset" "$import_file"; then
        warning "Invalid preset format: $import_file"
        return 1
    fi
    
    # Extract preset name
    local preset_name=$(grep "^# Original:" "$import_file" | sed 's/^# Original: //')
    
    # If no preset name found, use import filename
    if [[ -z "$preset_name" ]]; then
        preset_name=$(basename "$import_file" .aspreset)
    fi
    
    # Ensure preset directory exists
    initialize_preset_system
    
    # Decode preset
    log "Importing preset: $preset_name"
    
    # Extract the base64 content (skip the header lines)
    tail -n +6 "$import_file" | base64 -d > "${PRESET_DIR}/${preset_name}.preset"
    
    log "Preset imported: $preset_name"
    return 0
}

# =============================================================================
# INTELLIGENT ERROR HANDLING
# =============================================================================

trigger_fallback() {
    local error_code=$?
    local error_log=$(<"${LOGDIR}/asymphony.log")
    local retry_attempts=${config[retry_attempts]:-0}
    
    # Limit maximum retry attempts
    if (( retry_attempts >= 3 )); then
        critical_error "Maximum retry attempts (3) reached. Final error: $error_log"
    fi

    case $error_code in
        139)  # SIGSEGV
            if [[ $error_log =~ "libplacebo" ]]; then
                config[gpu]=0
                config[retry_attempts]=$((retry_attempts+1))
                log "GPU acceleration failed, switching to software renderer (attempt $((retry_attempts+1))/3)"
                retry_with "Software fallback" "--gpu 0"
            fi ;;
        255)  # FFmpeg error
            if [[ $error_log =~ "Hardware" ]]; then
                disable_feature "${BASH_REMATCH[0]}"
                config[retry_attempts]=$((retry_attempts+1))
                log "Hardware feature failed, disabling and retrying (attempt $((retry_attempts+1))/3)"
                retry_with "Hardware disabled"
            fi ;;
        *)
            # Analyze common error patterns
            if [[ "$error_log" =~ "Permission denied" ]]; then
                critical_error "Permission error detected: $error_log"
            elif [[ "$error_log" =~ "No such file" ]]; then
                critical_error "Missing file error: $error_log"
            elif [[ "$error_log" =~ "Invalid argument" ]]; then
                config[retry_attempts]=$((retry_attempts+1))
                log "Invalid argument detected, adjusting parameters (attempt $((retry_attempts+1))/3)"
                adjust_parameters
                retry_with "Parameter adjustment"
            else
                critical_error "$error_log"
            fi
            ;;
    esac
}

adjust_parameters() {
    # Automatically adjust problematic parameters
    [[ "${config[quality]}" == "ultra" ]] && config[quality]="high"
    [[ "${config[fps]}" -gt 60 ]] && config[fps]=60
    [[ "${config[width]}" -gt 3840 ]] && config[width]=1920
    [[ "${config[height]}" -gt 2160 ]] && config[height]=1080
}

retry_with() {
    log "Retrying with $1..."
    create_visualization
}

# =============================================================================
# RUNTIME EXECUTION
# =============================================================================


main() {
    trap 'emergency_shutdown' EXIT INT TERM

    # Initialize preset system
    initialize_preset_system

    # If no arguments, launch interactive menu
    if [[ $# -eq 0 ]]; then
        interactive_menu
        exit 0
    fi

    # Handle specific commands
    case "$1" in
        --help|-h)
            show_help
            exit 0
            ;;
        --list-devices)
            list_audio_devices
            exit 0
            ;;
        --list-presets)
            list_presets
            exit 0
            ;;
        --save-preset)
            init_engine
            save_preset "$2"
            exit $?
            ;;
        --load-preset)
            init_engine
            load_preset "$2"
            shift 2
            # Continue with visualization using preset settings
            ;;
        --export-preset)
            init_engine
            export_preset "$2" "$3"
            exit $?
            ;;
        --import-preset)
            init_engine
            import_preset "$2"
            exit $?
            ;;
        --live)
            config[live_input]=1
            shift # Remove --live from arguments

            # If a device specifier is provided
            if [[ "$1" =~ ^[0-9]+$ || "$1" =~ ^[a-zA-Z0-9_\.\-]+$ ]]; then
                config[audio_device]="$1"
                shift # Remove device specifier from arguments
            else
                # Auto-detect devices and use the first one
                detect_audio_devices
                config[audio_device]="${AUDIO_DEVICES[0]}"
            fi

            log "Live input mode enabled, using device: ${config[audio_device]}"
            ;;
    esac

    # Robust argument parsing: allow flags before/after input/output
    local input_file=""
    local output_file=""
    local args=()
    for arg in "$@"; do
        if [[ "$arg" == --* ]]; then
            args+=("$arg")
        elif [[ -z "$input_file" ]]; then
            input_file="$arg"
        elif [[ -z "$output_file" ]]; then
            output_file="$arg"
        else
            args+=("$arg")
        fi
    done

    # Set defaults if not provided
    input="${input_file:-input.mp3}"
    output="${output_file:-output.mp4}"

    init_engine "${args[@]}"

    {
        validate_input "$input"
        check_dependencies
        allocate_resources
        create_visualization | monitor_progress
    } 3>&-

    trap - EXIT
    optimize_output
}

validate_input() {
    # Skip validation for live input
    [[ "${config[live_input]}" -eq 1 ]] && return 0
    
    if [[ ! -f "$1" ]]; then
        critical_error "Input file not found: $1"
    fi
    
    # Check if file is readable by FFmpeg
    if ! ffprobe -v error -i "$1" -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 &>/dev/null; then
        critical_error "FFmpeg cannot read the input file: $1"
    fi
    
    return 0
}

check_dependencies() {
    for cmd in ffmpeg ffprobe pv; do
        if ! command -v $cmd &>/dev/null; then
            critical_error "$cmd is required but not installed"
        fi
    done
    
    return 0
}

allocate_resources() {
    # Calculate thread allocation based on CPU cores
    if [[ -z "${config[threads]}" || "${config[threads]}" == "auto" ]]; then
        config[threads]=$(( $(nproc) / 2 ))
        [[ ${config[threads]} -lt 1 ]] && config[threads]=1
    fi
    
    # Set environment variables for FFmpeg
    export FFREPORT=level=32:file="${LOGDIR}/ffmpeg_report.log"
    export LIBVA_DRIVER_NAME=iHD  # For Intel GPUs on Linux
    
    return 0
}

monitor_progress() {
    # Simple progress monitoring
    local total_frames
    
    if [[ "${config[live_input]}" -eq 1 ]]; then
        # For live input, we don't know the total frames
        cat
    else
        # For file input, calculate total frames
        total_frames=$(get_duration "$input")*${config[fps]}
        pv -N "Encoding" -petra "$total_frames" >/dev/null
    fi
}

get_duration() {
    ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$1"
}

optimize_output() {
    log "Visualization complete"
    log "Output saved to: $output"
    
    # Perform any optimization if needed
    if [[ "$output" == *.mp4 && -f "$output" ]]; then
        log "Optimizing MP4 file for streaming"
        local temp_file="${output}.temp.mp4"
        
        if ffmpeg -v error -i "$output" -c copy -movflags faststart "$temp_file"; then
            mv "$temp_file" "$output"
            log "MP4 optimization complete"
        else
            warning "MP4 optimization failed"
            [[ -f "$temp_file" ]] && rm "$temp_file"
        fi
    fi
}

emergency_shutdown() {
    # Cleanup on exit
    log "Shutting down"
    
    # Kill any running ffmpeg processes
    pkill -P $$ ffmpeg &>/dev/null || true
    
    exit 0
}

show_help() {
    echo "AsciiSymphony Pro v2.1.1: Enterprise-Grade ASCII Art Audio Visualizer"
    echo ""
    echo "Usage: $0 [options] [input_file] [output_file]"
    echo ""
    echo "Basic options:"
    echo "  --help, -h         Show this help message"
    echo "  --mode=MODE        Set visualization mode"
    echo "  --fps=FPS          Set frames per second (default: 30)"
    echo "  --quality=QUALITY  Set quality (low, balanced, high, ultra)"
    echo ""
    echo "Visualization modes:"
    echo "  waves        - Audio waveform visualization (default)"
    echo "  spectrum     - Frequency spectrum visualization"
    echo "  cqt          - Constant Q transform visualization"
    echo "  combo        - Combined waveform and spectrum"
    echo "  edge         - Edge-detected audio visualization"
    echo "  kaleidoscope - Kaleidoscope effect on spectrum"
    echo "  spectrosynth - Multi-band spectral synthesis"
    echo "  vortex       - Rotating audio vortex"
    echo "  neural       - Neural network-inspired multi-band visualization"
    echo "  typography   - Dynamic text-based audio visualization"
    echo "  particles    - Particle system audio visualization"
    echo "  fractal      - Fractal-inspired recursive visualization"
    echo ""
    echo "Live input options:"
    echo "  --live [device]   Use live audio input"
    echo "  --list-devices    List available audio input devices"
    echo "  --latency=VALUE   Set latency mode (normal, low, realtime)"
    echo "  --buffer=SIZE     Set audio buffer size (default: 1024)"
    echo ""
    echo "Preset management:"
    echo "  --list-presets     List available presets"
    echo "  --save-preset NAME Save current settings as preset"
    echo "  --load-preset NAME Load settings from preset"
    echo "  --export-preset NAME [FILE] Export preset to portable format"
    echo "  --import-preset FILE Import preset from portable format"
    echo ""
    echo "Examples:"
    echo "  $0 input.mp3 output.mp4 --mode=neural"
    echo "  $0 --live --mode=typography"
    echo "  $0 --load-preset MyPreset input.mp3 output.mp4"
    echo ""
    echo "For full documentation, visit https://github.com/asciisymphony/docs"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    # Check for debug mode
    if [[ "$1" == "--debug" ]]; then
        set -x
        shift
    fi
    
    main "$@"
fi
