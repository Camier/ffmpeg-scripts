import subprocess
from pathlib import Path
import ffmpeg

# 🧱 Setup
AUDIO_FILE = "Bees_nocover.flac"
FRAME_SIZE = "640x480"
ASCII_WIDTH = 100
TOTAL_FRAMES = 444
FPS = 30

# 🗂️ Create working directories
for folder in ["frames_raw", "frames_txt", "frames_ascii", "frames_colorized"]:
    Path(folder).mkdir(exist_ok=True)

def extract_cqt_frames():
    print("🎚️ Extracting CQT frames via showcqt...")
    (
        ffmpeg
        .input(AUDIO_FILE)
        .filter("showcqt",
                s=FRAME_SIZE,
                cscheme="1|0.5|0|0|0.5|1",  # Orange-to-blue scheme
                bar_v="1",
                bar_g="3")
        .output("frames_raw/frame_%04d.png", vframes=TOTAL_FRAMES)
        .overwrite_output()
        .run()
    )

def convert_to_ascii():
    print("🔣 Converting PNG frames to ASCII...")
    for f in sorted(Path("frames_raw").glob("*.png")):
        base = f.stem
        out_path = Path(f"frames_txt/{base}.txt")
        with out_path.open("w") as out:
            subprocess.run([
                "img2txt",
                "--width", str(ASCII_WIDTH),
                "--format", "utf8",
                str(f)
            ], stdout=out)

def glitch_glyphs():
    print("💀 Injecting text corruption/glitches...")
    for txt in sorted(Path("frames_txt").glob("*.txt")):
        base = txt.stem
        with open(txt) as f:
            content = f.read()
        # Glitch the text
        content = content.replace("%", "%%")
        content = content.replace("O", "@").replace("o", "@")
        content = content.replace("0", "@")
        content = content.replace("I", "|").replace("l", "|").replace("1", "|")
        content = content.replace("A", "#").replace("H", "#").replace("M", "#")
        out_path = Path(f"frames_ascii/{base}.txt")
        with out_path.open("w") as out:
            out.write(content)

def render_ascii_to_png():
    print("🖼️ Rendering ASCII to PNG...")
    for ascii_file in sorted(Path("frames_ascii").glob("*.txt")):
        base = ascii_file.stem
        image_out = Path(f"frames_colorized/{base}.png")
        with open(ascii_file) as infile:
            ascii_art = infile.read()
        # Use ImageMagick convert to turn ASCII into PNG
        subprocess.run([
            "convert",
            "-size", "1280x720",
            "xc:black",          # background
            "-font", "Courier",
            "-pointsize", "12",
            "-fill", "#66ccff",  # neon blue
            "-gravity", "northwest",
            "-annotate", "+20+20", ascii_art,
            str(image_out)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def hue_shift_frames():
    print("🌈 Drifting hues gently...")
    shifted_dir = Path("frames_shifted")
    shifted_dir.mkdir(exist_ok=True)
    for i, png in enumerate(sorted(Path("frames_colorized").glob("*.png"))):
        base = png.name
        hue_angle = (i % 60) - 30  # -30 to +30
        out_path = shifted_dir / base
        (
            ffmpeg
            .input(str(png))
            .filter("hue", h=hue_angle, s=1.15, b=1.1)
            .output(str(out_path), vframes=1, format="image2", update=1)
            .overwrite_output()
            .run(quiet=True)
        )

def combine_video():
    print("📼 Finalizing the ritual video...")

    # Input ASCII-colored video frames
    video_input = ffmpeg.input("frames_shifted/frame_%04d.png", framerate=30)

    # Input audio (no album art stream!)
    audio_input = ffmpeg.input(AUDIO_FILE)

    # Output to video file
    (
        ffmpeg
        .output(
            video_input,
            audio_input,
            "ascii_showcqt_ritual.mp4",
            vcodec="libx264",
            acodec="aac",
            crf=18,
            preset="slow",
            pix_fmt="yuv420p",
            shortest=None,
            movflags="faststart",  # Better for streaming
            metadata="title=ASCII ShowCQT Ritual Glitch"
        )
        .overwrite_output()
        .run()
    )
def main():
    extract_cqt_frames()
    convert_to_ascii()
    glitch_glyphs()
    render_ascii_to_png()
    hue_shift_frames()
    combine_video()
    print("✅ Ritual complete: ascii_showcqt_ritual.mp4")

if __name__ == "__main__":
    main()