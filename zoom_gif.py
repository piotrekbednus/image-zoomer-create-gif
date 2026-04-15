#!/usr/bin/env python3
"""
zoom_gif.py - Create a smooth zoom-in/zoom-out GIF from a static image.

Usage:
    python zoom_gif.py input.png
    python zoom_gif.py input.png --crop "1100,0,2896,560"
    python zoom_gif.py input.png --crop "right-top" --width 800
    python zoom_gif.py input.png --interactive
"""

import argparse
import math
import sys
from pathlib import Path

from PIL import Image


# --- Preset crop regions (relative to image, 0.0-1.0) ---
PRESETS = {
    "right-top":    (0.5, 0.0, 1.0, 0.5),
    "right-bottom": (0.5, 0.5, 1.0, 1.0),
    "left-top":     (0.0, 0.0, 0.5, 0.5),
    "left-bottom":  (0.0, 0.5, 0.5, 1.0),
    "center":       (0.25, 0.25, 0.75, 0.75),
    "top":          (0.0, 0.0, 1.0, 0.5),
    "bottom":       (0.0, 0.5, 1.0, 1.0),
    "left":         (0.0, 0.0, 0.5, 1.0),
    "right":        (0.5, 0.0, 1.0, 1.0),
}


def ease_in_out(t: float) -> float:
    return (1 - math.cos(t * math.pi)) / 2


def parse_bg_color(bg_str: str) -> tuple[int, int, int]:
    parts = [int(x.strip()) for x in bg_str.split(",")]
    if len(parts) != 3 or any(part < 0 or part > 255 for part in parts):
        raise ValueError("Background colour must be in format R,G,B with values 0-255.")

    return tuple(parts)


def parse_crop(crop_str: str, img_w: int, img_h: int) -> tuple[int, int, int, int]:
    """Parse crop string - either a preset name or 'x1,y1,x2,y2' pixel values."""
    crop_str = crop_str.strip().lower()

    if crop_str in PRESETS:
        rx1, ry1, rx2, ry2 = PRESETS[crop_str]
        return (
            int(rx1 * img_w),
            int(ry1 * img_h),
            int(rx2 * img_w),
            int(ry2 * img_h),
        )

    # Try pixel values
    try:
        parts = [int(x.strip()) for x in crop_str.split(",")]
    except ValueError as exc:
        raise ValueError(
            f"Crop must be a preset name or 'x1,y1,x2,y2'. Got: {crop_str}"
        ) from exc

    if len(parts) != 4:
        raise ValueError(
            f"Crop must be a preset name or 'x1,y1,x2,y2'. Got: {crop_str}"
        )

    return tuple(parts)


def validate_crop_region(
    crop_region: tuple[int, int, int, int], img_w: int, img_h: int
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = crop_region

    if not (0 <= x1 < x2 <= img_w and 0 <= y1 < y2 <= img_h):
        raise ValueError(
            f"Crop must stay inside image bounds 0,0,{img_w},{img_h} and satisfy x1<x2, y1<y2."
        )

    return crop_region


def interactive_crop(img: Image.Image) -> tuple[int, int, int, int]:
    """Let user pick crop region interactively."""
    W, H = img.size
    print(f"\nImage size: {W} x {H}")
    print(f"\nPresets: {', '.join(PRESETS.keys())}")
    print("Or enter pixel values as: x1,y1,x2,y2\n")

    choice = input("Pick a region: ").strip()
    return validate_crop_region(parse_crop(choice, W, H), W, H)


def make_frame(
    img: Image.Image,
    x1: int, y1: int, x2: int, y2: int,
    out_w: int, out_h: int,
    bg_color: tuple[int, int, int],
) -> Image.Image:
    """Crop and resize with aspect ratio preservation + letterboxing."""
    crop = img.crop((x1, y1, x2, y2))
    cw, ch = crop.size
    cr = cw / ch
    target_r = out_w / out_h

    if cr > target_r:
        new_w = out_w
        new_h = int(out_w / cr)
    else:
        new_h = out_h
        new_w = int(out_h * cr)

    resized = crop.resize((new_w, new_h), Image.LANCZOS)

    frame = Image.new("RGB", (out_w, out_h), bg_color)
    px = (out_w - new_w) // 2
    py = (out_h - new_h) // 2
    frame.paste(resized, (px, py))
    return frame


def create_zoom_gif(
    input_path: str,
    output_path: str,
    crop_region: tuple[int, int, int, int],
    width: int = 800,
    hold_start_ms: int = 1000,
    hold_zoom_ms: int = 1500,
    zoom_in_ms: int = 1000,
    zoom_out_ms: int = 400,
    fps: int = 20,
    bg_color: tuple[int, int, int] = (255, 255, 255),
):
    img = Image.open(input_path).convert("RGB")
    W, H = img.size
    out_w = width
    out_h = int(width / (W / H))

    crop_x1, crop_y1, crop_x2, crop_y2 = validate_crop_region(crop_region, W, H)

    frame_ms = 1000 / fps
    n_hold_start = max(1, round(hold_start_ms / frame_ms))
    n_zoom_in    = max(2, round(zoom_in_ms / frame_ms))
    n_hold_zoom  = max(1, round(hold_zoom_ms / frame_ms))
    n_zoom_out   = max(2, round(zoom_out_ms / frame_ms))

    frames = []
    durations = []

    # Phase 1: Hold on full image
    for _ in range(n_hold_start):
        frames.append(make_frame(img, 0, 0, W, H, out_w, out_h, bg_color))
        durations.append(int(frame_ms))

    # Phase 2: Zoom in
    for i in range(n_zoom_in):
        t = ease_in_out(i / (n_zoom_in - 1))
        x1 = int(crop_x1 * t)
        y1 = int(crop_y1 * t)
        x2 = int(W - (W - crop_x2) * t)
        y2 = int(H - (H - crop_y2) * t)
        frames.append(make_frame(img, x1, y1, x2, y2, out_w, out_h, bg_color))
        durations.append(int(frame_ms))

    # Phase 3: Hold on zoomed view
    for _ in range(n_hold_zoom):
        frames.append(
            make_frame(img, crop_x1, crop_y1, crop_x2, crop_y2, out_w, out_h, bg_color)
        )
        durations.append(int(frame_ms))

    # Phase 4: Zoom back out
    for i in range(n_zoom_out):
        t = ease_in_out(i / (n_zoom_out - 1))
        x1 = int(crop_x1 * (1 - t))
        y1 = int(crop_y1 * (1 - t))
        x2 = int(crop_x2 + (W - crop_x2) * t)
        y2 = int(crop_y2 + (H - crop_y2) * t)
        frames.append(make_frame(img, x1, y1, x2, y2, out_w, out_h, bg_color))
        durations.append(int(frame_ms))

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )

    size_kb = Path(output_path).stat().st_size / 1024
    total_ms = sum(durations)
    print(f"Done! {output_path}")
    print(f"  {len(frames)} frames, {size_kb:.0f} KB, ~{total_ms/1000:.1f}s loop")


def main():
    parser = argparse.ArgumentParser(
        description="Create a smooth zoom-in/zoom-out GIF from a static image.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Crop presets: {', '.join(PRESETS.keys())}\n"
               "Or use pixel values: --crop '1100,0,2896,560'",
    )
    parser.add_argument("input", help="Input image path")
    parser.add_argument("-o", "--output", help="Output GIF path (default: input_zoom.gif)")
    parser.add_argument(
        "-c", "--crop",
        default="right-top",
        help="Crop target: preset name or 'x1,y1,x2,y2' pixels (default: right-top)",
    )
    parser.add_argument("-i", "--interactive", action="store_true", help="Pick crop region interactively")
    parser.add_argument("-w", "--width", type=int, default=800, help="Output width in px (default: 800)")
    parser.add_argument("--hold-start", type=int, default=1000, help="Hold on full view, ms (default: 1000)")
    parser.add_argument("--hold-zoom", type=int, default=1500, help="Hold on zoomed view, ms (default: 1500)")
    parser.add_argument("--zoom-in", type=int, default=1000, help="Zoom-in duration, ms (default: 1000)")
    parser.add_argument("--zoom-out", type=int, default=400, help="Zoom-out duration, ms (default: 400)")
    parser.add_argument("--fps", type=int, default=20, help="Frames per second (default: 20)")
    parser.add_argument("--bg", default="255,255,255", help="Letterbox background R,G,B (default: 255,255,255)")

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: {args.input} not found")
        sys.exit(1)

    output = args.output or str(Path(args.input).stem + "_zoom.gif")
    try:
        bg = parse_bg_color(args.bg)
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    img = Image.open(args.input)
    W, H = img.size

    try:
        if args.interactive:
            crop = interactive_crop(img)
        else:
            crop = validate_crop_region(parse_crop(args.crop, W, H), W, H)
    except ValueError as exc:
        print(f"Error: {exc}")
        print(f"Available presets: {', '.join(PRESETS.keys())}")
        sys.exit(1)

    print(f"Input:  {args.input} ({W}x{H})")
    print(f"Crop:   {crop}")
    print(f"Output: {output} ({args.width}px wide)")

    create_zoom_gif(
        input_path=args.input,
        output_path=output,
        crop_region=crop,
        width=args.width,
        hold_start_ms=args.hold_start,
        hold_zoom_ms=args.hold_zoom,
        zoom_in_ms=args.zoom_in,
        zoom_out_ms=args.zoom_out,
        fps=args.fps,
        bg_color=bg,
    )


if __name__ == "__main__":
    main()
