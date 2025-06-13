#!/bin/bash

# ASCII Symphony FFmpeg Pipeline
# Usage: ./asciisymphony_ffmpeg.sh input_video.mp4 output_format [width] [height] [fps]

INPUT=$1
FORMAT=${2:-svg}
WIDTH=${3:-120}
HEIGHT=${4:-40}
FPS=${5:-12}
TEMP_DIR=$(mktemp -d)

# Validate input
if [ -z "$INPUT" ]; then
    echo "Error: Input file required"
    echo "Usage: $0 input_video.mp4 output_format [width] [height] [fps]"
    exit 1
fi

if [ ! -f "$INPUT" ]; then
    echo "Error: Input file not found: $INPUT"
    exit 1
fi

# Create output directory
OUTPUT_DIR="ascii_output_$(date +%s)"
mkdir -p "$OUTPUT_DIR"

echo "Processing video: $INPUT"
echo "Output format: $FORMAT"
echo "Resolution: ${WIDTH}x${HEIGHT}"
echo "FPS: $FPS"

# Extract audio
echo "Extracting audio..."
ffmpeg -i "$INPUT" -q:a 0 -map a "$TEMP_DIR/audio.wav" -y -loglevel error

# Extract frames at specified FPS
echo "Extracting video frames..."
ffmpeg -i "$INPUT" -vf "fps=$FPS" "$TEMP_DIR/frame_%04d.png" -y -loglevel error

# Count frames
FRAME_COUNT=$(ls "$TEMP_DIR"/frame_*.png | wc -l)
echo "Total frames: $FRAME_COUNT"

# Process frames with libcaca
echo "Converting frames to ASCII art..."

# Use img2txt with optimized parameters
for i in $(seq -f "%04g" 1 $FRAME_COUNT); do
    if [ -f "$TEMP_DIR/frame_$i.png" ]; then
        echo -ne "Processing frame $i/$FRAME_COUNT\r"
        
        # Calculate frame position in audio for reactive effects
        POSITION=$(echo "scale=6; $i / $FPS" | bc)
        
        # Extract audio features for this frame (simplified)
        # In a real implementation, you would analyze the audio more thoroughly
        # This is a basic approximation using sox to get RMS volume
        FRAME_TIME=$(echo "scale=3; ($i-1) / $FPS" | bc)
        DURATION=$(echo "scale=3; 1 / $FPS" | bc)
        
        # Get audio features for this time segment
        VOLUME=$(sox "$TEMP_DIR/audio.wav" -n stat -t "$FRAME_TIME" -d "$DURATION" 2>&1 | grep "RMS" | head -1 | awk '{print $3}')
        
        # Default values if audio analysis fails
        if [ -z "$VOLUME" ]; then
            VOLUME=0.5
        fi
        
        # Scale values for img2txt parameters
        BRIGHTNESS=$(echo "scale=2; 0.8 + $VOLUME * 0.8" | bc)
        CONTRAST=$(echo "scale=2; 1.0 + $VOLUME * 0.6" | bc)
        
        # Select dithering algorithm based on volume
        # Higher volume = faster algorithm for performance
        DITHER="fstein"
        VOLUME_THRESHOLD=0.1
        if (( $(echo "$VOLUME > $VOLUME_THRESHOLD" | bc -l) )); then
            DITHER="ordered4"
        fi
        
        # Convert frame to ASCII art
        img2txt -W $WIDTH -H $HEIGHT -f $FORMAT -d $DITHER -b $BRIGHTNESS -c $CONTRAST \
            "$TEMP_DIR/frame_$i.png" > "$OUTPUT_DIR/ascii_$i.$FORMAT"
    fi
done

echo -e "\nCreating output files..."

# Create appropriate output based on format
if [ "$FORMAT" = "html" ]; then
    # Create HTML animation file
    HTML_FILE="$OUTPUT_DIR/animation.html"
    
    # HTML header
    cat > "$HTML_FILE" << EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AsciiSymphony Visualization</title>
    <style>
        body { background: #000; margin: 0; padding: 20px; }
        ".container { max-width: 1200px; margin: 0 auto; }"
        .frame { display: none; }
        .frame.active { display: block; }
        .ascii-art { font-family: monospace; line-height: 1; white-space: pre; color: #fff; }
    </style>
</head>
<body>
    <div class="container">
        <div id="visualization">
EOF
    
    # Add frames
    for i in $(seq -f "%04g" 1 $FRAME_COUNT); do
        if [ -f "$OUTPUT_DIR/ascii_$i.$FORMAT" ]; then
            if [ "$i" = "0001" ]; then
                echo "<div class=\"frame active\" id=\"frame-$i\">" >> "$HTML_FILE"
            else
                echo "<div class=\"frame\" id=\"frame-$i\">" >> "$HTML_FILE"
            fi
            
            echo "<div class=\"ascii-art\">" >> "$HTML_FILE"
            cat "$OUTPUT_DIR/ascii_$i.$FORMAT" >> "$HTML_FILE"
            echo "</div>" >> "$HTML_FILE"
            echo "</div>" >> "$HTML_FILE"
        fi
    done
    
    # HTML footer with player controls
    cat >> "$HTML_FILE" << EOF
        </div>
        <div class="controls">
            <button id="play-pause">Pause</button>
            <input type="range" id="progress" min="0" max="$FRAME_COUNT" value="0">
        </div>
    </div>
    
    <script>
        // Add audio
        const audio = new Audio();
        audio.src = "audio.wav";
        audio.loop = true;
        
        // Animation controller
        const frames = document.querySelectorAll('.frame');
        const playPauseBtn = document.getElementById('play-pause');
        const progressBar = document.getElementById('progress');
        
        let currentFrame = 0;
        let isPlaying = true;
        let animationInterval;
        const fps = $FPS;
        const frameDuration = 1000 / fps;
        
        function updateFrame() {
            // Hide all frames
            frames.forEach(frame => frame.classList.remove('active'));
            
            // Show current frame
            frames[currentFrame].classList.add('active');
            
            // Update progress bar
            progressBar.value = currentFrame + 1;
            
            // Advance to next frame
            currentFrame = (currentFrame + 1) % frames.length;
        }
        
        function startAnimation() {
            animationInterval = setInterval(updateFrame, frameDuration);
            isPlaying = true;
            playPauseBtn.textContent = 'Pause';
            audio.play();
        }
        
        function stopAnimation() {
            clearInterval(animationInterval);
            isPlaying = false;
            playPauseBtn.textContent = 'Play';
            audio.pause();
        }
        
        // Initialize
        startAnimation();
        
        // Event listeners
        playPauseBtn.addEventListener('click', () => {
            if (isPlaying) {
                stopAnimation();
            } else {
                startAnimation();
            }
        });
        
        progressBar.addEventListener('input', () => {
            currentFrame = parseInt(progressBar.value) - 1;
            updateFrame();
            if (!isPlaying) {
                currentFrame = parseInt(progressBar.value) - 1;
            }
            
            // Sync audio position
            const audioTime = currentFrame / fps;
            audio.currentTime = audioTime;
        });
    </script>
</body>
</html>
EOF
    
    # Copy audio file for HTML player
    cp "$TEMP_DIR/audio.wav" "$OUTPUT_DIR/"
    
    echo "HTML animation created at: $HTML_FILE"
    echo "Open in a browser to view the animation with audio."

elif [ "$FORMAT" = "ansi" ]; then
    # Create a simple player script for terminal playback
    PLAYER_SCRIPT="$OUTPUT_DIR/play_animation.sh"
    
    cat > "$PLAYER_SCRIPT" << EOF
#!/bin/bash

# Terminal ASCII Animation Player
FPS=$FPS
FRAME_DELAY=\$(echo "scale=6; 1 / \$FPS" | bc)

# Check if sox is available for audio playback
if command -v sox > /dev/null; then
    # Play audio in background
    sox "$OUTPUT_DIR/audio.wav" -d &
    AUDIO_PID=\$!
fi

# Clear screen
clear

# Play animation
echo "Playing ASCII animation. Press Ctrl+C to exit."
echo ""

for i in \$(seq -f "%04g" 1 $FRAME_COUNT); do
    if [ -f "$OUTPUT_DIR/ascii_\$i.$FORMAT" ]; then
        clear
        cat "$OUTPUT_DIR/ascii_\$i.$FORMAT"
        sleep \$FRAME_DELAY
    fi
done

# Kill audio playback if running
if [ -n "\$AUDIO_PID" ]; then
    kill \$AUDIO_PID 2>/dev/null
fi
EOF
    
    chmod +x "$PLAYER_SCRIPT"
    cp "$TEMP_DIR/audio.wav" "$OUTPUT_DIR/"
    
    echo "Terminal animation player created at: $PLAYER_SCRIPT"
    echo "Run the script to play the animation in your terminal."

else
    # For other formats, just create a directory with all frames
    echo "ASCII frames generated in: $OUTPUT_DIR"
    echo "You can use these frames with other tools or viewers."
fi

# Clean up temp files
rm -rf "$TEMP_DIR"

echo "Processing complete!"
