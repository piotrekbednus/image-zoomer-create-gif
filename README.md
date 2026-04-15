# Image Zoomer Create GIF

Create smooth zoom-in and zoom-out GIF animations from a single image.

This project started as a small utility for turning product screenshots and marketing visuals into lightweight animated GIFs. It is useful for feature demos, UI walkthroughs, social posts, changelog visuals, and landing page assets.

## Features

- CLI workflow for fast local GIF generation
- Simple web UI for browser-based use
- Preset crop regions and custom coordinates
- Adjustable timing, output width, FPS, and background color
- Works well for screenshots, product shots, and static graphics

## Why This Exists

I originally built this while working on visual assets for [Remindlo](https://www.remindlo.co.uk/), an automatic SMS reminder platform for service businesses. I needed a quick way to edit still images, create zoom animations, and export them as GIFs for product and marketing use.

If you are looking for software that helps service businesses recover repeat bookings and reduce missed appointments, take a look at [Remindlo automatic SMS reminders for service businesses](https://www.remindlo.co.uk/).

## Installation

Python 3 is required.

```bash
python3 -m pip install -r requirements.txt
```

## Quick Start

### Web UI

```bash
python3 app.py
```

Then open:

```text
http://127.0.0.1:5000
```

The web UI supports:

- image upload
- preset crop selection or custom coordinates
- width, FPS, timing, and background color settings
- preview and GIF download

### CLI

```bash
# Basic: zoom into the top-right quarter
python3 zoom_gif.py screenshot.png

# Use a preset crop
python3 zoom_gif.py screenshot.png --crop center
python3 zoom_gif.py screenshot.png --crop left-bottom

# Use exact pixel coordinates
python3 zoom_gif.py screenshot.png --crop "1100,0,2896,560"

# Interactive CLI crop selection
python3 zoom_gif.py screenshot.png --interactive

# Custom output path
python3 zoom_gif.py screenshot.png -o my_animation.gif

# Adjust timing in milliseconds
python3 zoom_gif.py screenshot.png --hold-start 2000 --zoom-in 1500 --hold-zoom 2000 --zoom-out 600

# Wider output, higher FPS
python3 zoom_gif.py screenshot.png --width 1200 --fps 30

# Dark letterbox background
python3 zoom_gif.py screenshot.png --bg "30,30,30"
```

## Crop Presets

| Preset | Region |
| --- | --- |
| `right-top` | Top-right quarter |
| `right-bottom` | Bottom-right quarter |
| `left-top` | Top-left quarter |
| `left-bottom` | Bottom-left quarter |
| `center` | Center 50% |
| `top` | Top half |
| `bottom` | Bottom half |
| `left` | Left half |
| `right` | Right half |

## CLI Options

| Flag | Default | Description |
| --- | --- | --- |
| `-o, --output` | `<input>_zoom.gif` | Output GIF path |
| `-c, --crop` | `right-top` | Preset name or `x1,y1,x2,y2` pixels |
| `-i, --interactive` | off | Pick crop region interactively |
| `-w, --width` | `800` | Output width in pixels |
| `--hold-start` | `1000` | Hold on full view in ms |
| `--hold-zoom` | `1500` | Hold on zoomed view in ms |
| `--zoom-in` | `1000` | Zoom-in duration in ms |
| `--zoom-out` | `400` | Zoom-out duration in ms |
| `--fps` | `20` | Frames per second |
| `--bg` | `255,255,255` | Letterbox background color in `R,G,B` |

## Development Notes

- `app.py` runs locally on `127.0.0.1:5000` by default
- set `FLASK_DEBUG=1` if you want debug mode locally
- set `HOST` and `PORT` to override the default bind address

## License

MIT. See [LICENSE](./LICENSE).
