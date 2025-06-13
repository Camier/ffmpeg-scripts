#!/bin/bash

# Advanced CACA Effects - Creative ASCII Art Visualization Techniques
# Showcases innovative ways to use libcaca with FFMPEG filters

set -euo pipefail

# Effect configurations
declare -A EFFECTS=(
    ["ascii_rain"]="Matrix-style falling ASCII characters synced to audio"
    ["pulse_wave"]="Pulsating waveform that responds to beat detection"
    ["kaleidoscope"]="Symmetrical ASCII patterns from audio spectrum"
    ["particle_burst"]="Explosive particle effects triggered by audio peaks"
    ["glitch_art"]="Intentional visual glitches synced to rhythm"
    ["fluid_sim"]="Fluid-like ASCII motion driven by audio"
    ["fractal_zoom"]="Recursive fractal patterns responding to frequency"
    ["pixel_sort"]="Pixel sorting algorithm applied to ASCII output"
    ["data_moshing"]="Frame blending and corruption effects"
    ["ascii_3d"]="Pseudo-3D rotation of ASCII visualizations"
)

# Generate ASCII rain effect
generate_ascii_rain() {
    local input="$1"
    local output="${2:-}"
    
    ffmpeg -i "$input" -filter_complex "
        [0:a]showfreqs=s=160x50:mode=bar:cmode=combined:ascale=log[freq];
        [freq]split=2[f1][f2];
        [f1]negate[neg];
        [neg][f2]blend=all_mode=difference,
        drawtext=fontfile=/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf:
            text='%{localtime\\:%T}':fontcolor=green:fontsize=8:x=w-tw-10:y=10,
        format=pix_fmts=rgb24
    " -f caca -caca charset=ascii:driver=ncurses:color=mono ${output:+-o "$output"} -
}

# Generate pulsating waveform
generate_pulse_wave() {
    local input="$1"
    local output="${2:-}"
    
    ffmpeg -i "$input" -filter_complex "
        [0:a]showwaves=s=160x50:mode=p2p:colors=white[wave];
        [0:a]volume=1,aevalsrc=0:d=0.02[pulse];
        [wave]scale=iw:ih*(sin(t*10)*0.2+1):eval=frame,
        curves=all='0/0 0.5/0.8 1/1',
        format=pix_fmts=rgb24
    " -f caca -caca charset=blocks:dithering=ordered-4x4 ${output:+-o "$output"} -
}

# Generate kaleidoscope effect
generate_kaleidoscope() {
    local input="$1"
    local output="${2:-}"
    
    ffmpeg -i "$input" -filter_complex "
        [0:a]showcqt=s=80x50:count=3:gamma=5[cqt];
        [cqt]split=4[c1][c2][c3][c4];
        [c1]transpose=1[t1];
        [c2]hflip[h2];
        [c3]vflip[v3];
        [c4]transpose=2,vflip[t4];
        [t1][h2][v3][t4]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0,
        format=pix_fmts=rgb24
    " -f caca -caca charset=extended:antialias=prefilter ${output:+-o "$output"} -
}

# Generate particle burst effect
generate_particle_burst() {
    local input="$1"
    local output="${2:-}"
    
    ffmpeg -i "$input" -filter_complex "
        [0:a]showcqt=s=160x50:count=5:sono_h=0:bar_g=2[cqt];
        [0:a]showvolume=s=160x10:f=0.1:c=gradient:t=0[vol];
        [cqt][vol]vstack,
        erosion=coordinates=4x4:threshold0=100,
        format=pix_fmts=rgb24
    " -f caca -caca charset=blocks:dithering=random ${output:+-o "$output"} -
}

# Generate glitch art effect
generate_glitch_art() {
    local input="$1"
    local output="${2:-}"
    
    ffmpeg -i "$input" -filter_complex "
        [0:a]showspectrum=s=160x50:slide=fullframe:color=fire[spec];
        [spec]split=3[s1][s2][s3];
        [s1]lagfun=decay=0.95[l1];
        [s2]tmix=frames=3[t2];
        [s3]colorkey=color=black:similarity=0.1[c3];
        [l1][t2][c3]mix=inputs=3:weights='1 0.5 0.3',
        random=seed=42:frames=5,
        format=pix_fmts=rgb24
    " -f caca -caca charset=ascii:dithering=fstein ${output:+-o "$output"} -
}

# Generate fluid simulation effect
generate_fluid_sim() {
    local input="$1"
    local output="${2:-}"
    
    ffmpeg -i "$input" -filter_complex "
        [0:a]showwaves=s=160x50:mode=line:colors=blue|cyan[wave];
        [wave]gblur=sigma=2:steps=1,
        edgedetect=mode=wires:high=0.1:low=0.05,
        colorkey=color=black:similarity=0.01,
        format=pix_fmts=rgb24
    " -f caca -caca charset=blocks:dithering=ordered-8x8 ${output:+-o "$output"} -
}

# Generate fractal zoom effect
generate_fractal_zoom() {
    local input="$1"
    local output="${2:-}"
    
    ffmpeg -i "$input" -filter_complex "
        [0:a]showcqt=s=160x50:count=8:gamma=3:fontcolor=green[cqt];
        [cqt]rotate=a=t*0.1:c=black,
        zoompan=z='1.1':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=160x50,
        format=pix_fmts=rgb24
    " -f caca -caca charset=extended:antialias=fast ${output:+-o "$output"} -
}

# Generate pixel sort effect
generate_pixel_sort() {
    local input="$1"
    local output="${2:-}"
    
    ffmpeg -i "$input" -filter_complex "
        [0:a]showspectrum=s=160x50:scale=cbrt:color=moreland[spec];
        [spec]transpose=1,
        sobel,
        transpose=2,
        format=pix_fmts=rgb24
    " -f caca -caca charset=ascii:dithering=none ${output:+-o "$output"} -
}

# Generate data moshing effect
generate_data_mosh() {
    local input="$1"
    local output="${2:-}"
    
    ffmpeg -i "$input" -filter_complex "
        [0:a]showcqt=s=160x50:count=4:sono_v=bar_v/2[cqt];
        [cqt]split=2[c1][c2];
        [c1]setpts=0.5*PTS[slow];
        [c2]setpts=2*PTS[fast];
        [slow][fast]blend=all_mode=average,
        chromakey=color=black:similarity=0.3,
        format=pix_fmts=rgb24
    " -f caca -caca charset=blocks:dithering=random ${output:+-o "$output"} -
}

# Generate ASCII 3D effect
generate_ascii_3d() {
    local input="$1"
    local output="${2:-}"
    
    ffmpeg -i "$input" -filter_complex "
        [0:a]showcqt=s=160x50:count=6:sono_h=20:bar_g=2[cqt];
        [cqt]perspective=x0=0:y0=0:x1=W:y1=0:x2=W:y2=H:x3=0:y3=H:
            interpolation=linear:sense=destination,
        rotate=a=sin(t)*0.2:c=black,
        format=pix_fmts=rgb24
    " -f caca -caca charset=extended:antialias=prefilter ${output:+-o "$output"} -
}

# Combine multiple effects
generate_combo_effect() {
    local input="$1"
    local output="${2:-}"
    
    ffmpeg -i "$input" -filter_complex "
        [0:a]showcqt=s=80x25:count=4[cqt];
        [0:a]showwaves=s=80x25:mode=line[wave];
        [cqt][wave]hstack,
        split=3[s1][s2][s3];
        [s1]negate[n1];
        [s2]edgedetect=mode=wires[e2];
        [s3]colorkey=color=black:similarity=0.1[c3];
        [n1][e2][c3]mix=inputs=3,
        format=pix_fmts=rgb24
    " -f caca -caca charset=default:dithering=fstein ${output:+-o "$output"} -
}

# Performance test with different configurations
performance_test() {
    local input="$1"
    
    echo "Testing CACA performance with different settings..."
    
    declare -A configs=(
        ["minimal"]="charset=ascii:dithering=none:antialias=none"
        ["standard"]="charset=default:dithering=fstein:antialias=fast"
        ["quality"]="charset=extended:dithering=ordered-8x8:antialias=prefilter"
        ["experimental"]="charset=blocks:dithering=random:antialias=prefilter"
    )
    
    for config_name in "${!configs[@]}"; do
        echo "Testing $config_name configuration..."
        time ffmpeg -i "$input" -t 10 -filter_complex "
            [0:a]showcqt=s=160x50:count=6[v]
        " -map "[v]" -f caca -caca "${configs[$config_name]}" - >/dev/null 2>&1
    done
}

# Interactive menu
show_menu() {
    echo "Advanced CACA Effects Generator"
    echo "=============================="
    echo
    echo "Available effects:"
    
    local i=1
    for effect in "${!EFFECTS[@]}"; do
        printf "%2d. %-15s - %s\n" "$i" "$effect" "${EFFECTS[$effect]}"
        ((i++))
    done
    
    echo
    echo "11. Combination effect (multiple filters)"
    echo "12. Performance test"
    echo "13. Export all effects"
    echo "14. Exit"
    echo
}

# Export all effects to files
export_all_effects() {
    local input="$1"
    local output_dir="${2:-caca_effects}"
    
    mkdir -p "$output_dir"
    
    for effect in "${!EFFECTS[@]}"; do
        echo "Generating $effect..."
        case $effect in
            "ascii_rain") generate_ascii_rain "$input" "$output_dir/$effect.mp4";;
            "pulse_wave") generate_pulse_wave "$input" "$output_dir/$effect.mp4";;
            "kaleidoscope") generate_kaleidoscope "$input" "$output_dir/$effect.mp4";;
            "particle_burst") generate_particle_burst "$input" "$output_dir/$effect.mp4";;
            "glitch_art") generate_glitch_art "$input" "$output_dir/$effect.mp4";;
            "fluid_sim") generate_fluid_sim "$input" "$output_dir/$effect.mp4";;
            "fractal_zoom") generate_fractal_zoom "$input" "$output_dir/$effect.mp4";;
            "pixel_sort") generate_pixel_sort "$input" "$output_dir/$effect.mp4";;
            "data_moshing") generate_data_mosh "$input" "$output_dir/$effect.mp4";;
            "ascii_3d") generate_ascii_3d "$input" "$output_dir/$effect.mp4";;
        esac
    done
    
    echo "All effects exported to $output_dir/"
}

# Main execution
main() {
    if [ $# -lt 1 ]; then
        echo "Usage: $0 <input_audio_file> [output_file]"
        exit 1
    fi
    
    local input="$1"
    local output="${2:-}"
    
    if [ ! -f "$input" ]; then
        echo "Error: Input file not found: $input"
        exit 1
    fi
    
    while true; do
        clear
        show_menu
        read -p "Select an effect (1-14): " choice
        
        case $choice in
            1) generate_ascii_rain "$input" "$output";;
            2) generate_pulse_wave "$input" "$output";;
            3) generate_kaleidoscope "$input" "$output";;
            4) generate_particle_burst "$input" "$output";;
            5) generate_glitch_art "$input" "$output";;
            6) generate_fluid_sim "$input" "$output";;
            7) generate_fractal_zoom "$input" "$output";;
            8) generate_pixel_sort "$input" "$output";;
            9) generate_data_mosh "$input" "$output";;
            10) generate_ascii_3d "$input" "$output";;
            11) generate_combo_effect "$input" "$output";;
            12) performance_test "$input";;
            13) export_all_effects "$input" "$output";;
            14) echo "Goodbye!"; exit 0;;
            *) echo "Invalid choice";;
        esac
        
        if [ $choice -ne 14 ]; then
            echo
            read -p "Press Enter to continue..."
        fi
    done
}

# Run the script
main "$@"
