#!/usr/bin/env python3
from __future__ import annotations

import os
import uuid
from pathlib import Path

from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

from zoom_gif import PRESETS, create_zoom_gif, parse_bg_color, parse_crop, validate_crop_region


BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "web_uploads"
OUTPUT_DIR = BASE_DIR / "web_outputs"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def cleanup_old_files(directory: Path, keep_last: int = 20) -> None:
    files = sorted(
        (path for path in directory.iterdir() if path.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for stale_file in files[keep_last:]:
        stale_file.unlink(missing_ok=True)


def parse_positive_int(raw_value: str, field_name: str, minimum: int) -> int:
    value = int(raw_value)
    if value < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}.")
    return value


@app.route("/", methods=["GET", "POST"])
def index():
    context = {
        "presets": list(PRESETS.keys()),
        "selected_crop_mode": "preset",
        "selected_preset": "right-top",
        "custom_crop": "",
        "width": 800,
        "hold_start": 1000,
        "hold_zoom": 1500,
        "zoom_in": 1000,
        "zoom_out": 400,
        "fps": 20,
        "bg": "255,255,255",
        "error": None,
        "result_file": None,
        "original_name": None,
    }

    if request.method == "POST":
        form = request.form
        context.update(
            {
                "selected_crop_mode": form.get("crop_mode", "preset"),
                "selected_preset": form.get("preset", "right-top"),
                "custom_crop": form.get("custom_crop", "").strip(),
                "width": form.get("width", "800"),
                "hold_start": form.get("hold_start", "1000"),
                "hold_zoom": form.get("hold_zoom", "1500"),
                "zoom_in": form.get("zoom_in", "1000"),
                "zoom_out": form.get("zoom_out", "400"),
                "fps": form.get("fps", "20"),
                "bg": form.get("bg", "255,255,255").strip(),
            }
        )

        uploaded_file = request.files.get("image")
        if not uploaded_file or not uploaded_file.filename:
            context["error"] = "Choose an image file."
            return render_template("index.html", **context)

        if not allowed_file(uploaded_file.filename):
            context["error"] = "Supported formats: PNG, JPG, JPEG, WEBP, BMP."
            return render_template("index.html", **context)

        try:
            width = parse_positive_int(str(context["width"]), "Width", 100)
            hold_start = parse_positive_int(str(context["hold_start"]), "Hold start", 0)
            hold_zoom = parse_positive_int(str(context["hold_zoom"]), "Hold zoom", 0)
            zoom_in = parse_positive_int(str(context["zoom_in"]), "Zoom in", 100)
            zoom_out = parse_positive_int(str(context["zoom_out"]), "Zoom out", 100)
            fps = parse_positive_int(str(context["fps"]), "FPS", 1)
            bg = parse_bg_color(str(context["bg"]))
        except ValueError as exc:
            context["error"] = f"Invalid parameters: {exc}"
            return render_template("index.html", **context)

        safe_name = secure_filename(uploaded_file.filename)
        upload_id = uuid.uuid4().hex
        input_path = UPLOAD_DIR / f"{upload_id}_{safe_name}"
        output_name = f"{Path(safe_name).stem}_{upload_id[:8]}_zoom.gif"
        output_path = OUTPUT_DIR / output_name

        uploaded_file.save(input_path)
        context["original_name"] = safe_name

        try:
            from PIL import Image

            with Image.open(input_path) as img:
                img_w, img_h = img.size

            crop_value = (
                str(context["selected_preset"])
                if context["selected_crop_mode"] == "preset"
                else str(context["custom_crop"])
            )
            crop_region = validate_crop_region(parse_crop(crop_value, img_w, img_h), img_w, img_h)

            create_zoom_gif(
                input_path=str(input_path),
                output_path=str(output_path),
                crop_region=crop_region,
                width=width,
                hold_start_ms=hold_start,
                hold_zoom_ms=hold_zoom,
                zoom_in_ms=zoom_in,
                zoom_out_ms=zoom_out,
                fps=fps,
                bg_color=bg,
            )
            context["result_file"] = output_name
        except Exception as exc:
            context["error"] = str(exc)
        finally:
            input_path.unlink(missing_ok=True)
            cleanup_old_files(UPLOAD_DIR)
            cleanup_old_files(OUTPUT_DIR)

    return render_template("index.html", **context)


@app.route("/generated/<path:filename>")
def generated_file(filename: str):
    return send_from_directory(OUTPUT_DIR, filename)


@app.route("/download/<path:filename>")
def download_file(filename: str):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "").lower() in {"1", "true", "yes", "on"}
    app.run(host=host, port=port, debug=debug)
