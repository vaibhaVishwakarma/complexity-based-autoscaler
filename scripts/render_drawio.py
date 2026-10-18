#!/usr/bin/env python3
"""
scripts/render_drawio.py
========================
Automated headless renderer for Draw.io (.drawio) XML diagrams.
Uses diagrams.net client-side compression and Google Chrome headless
with a 3x device scale factor (300+ DPI equivalent) and PIL auto-cropping
to produce publication-grade PNG and PDF figures for IEEE Access.

Usage:
    ./.venv/bin/python -m scripts.render_drawio <input.drawio> -o <output_name>
"""

import argparse
import base64
import os
import subprocess
import sys
import tempfile
import urllib.parse
import zlib
from pathlib import Path
from PIL import Image, ImageChops

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = WORKSPACE_ROOT / "figures"
PAPER_FIGURES_DIR = WORKSPACE_ROOT / "paper" / "figures"


def encode_drawio_to_viewer_url(xml_content: str) -> str:
    """Encodes Draw.io XML into a client-side diagrams.net viewer URL fragment."""
    pre = urllib.parse.quote(xml_content, safe="!~*'()")
    compressor = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    compressed = compressor.compress(pre.encode("utf-8")) + compressor.flush()
    b64 = base64.b64encode(compressed).decode("utf-8").replace("\n", "")
    return "https://viewer.diagrams.net/?lightbox=1#R" + urllib.parse.quote(b64, safe="")


def autocrop_image(img_path: Path, output_png: Path, output_pdf: Path, padding: int = 24) -> None:
    """Trims solid white margins around the rendered diagram with clean padding."""
    with Image.open(img_path) as im:
        im = im.convert("RGB")
        bg = Image.new(im.mode, im.size, (255, 255, 255))
        diff = ImageChops.difference(im, bg)
        bbox = diff.getbbox()
        if bbox:
            left = max(0, bbox[0] - padding)
            top = max(0, bbox[1] - padding)
            right = min(im.size[0], bbox[2] + padding)
            bottom = min(im.size[1], bbox[3] + padding)
            cropped = im.crop((left, top, right, bottom))
        else:
            cropped = im

        # Save High-DPI PNG
        cropped.save(output_png, "PNG", optimize=True)
        # Save vector-compatible PDF
        cropped.save(output_pdf, "PDF", resolution=300.0)
        print(f"[OK] Saved cropped figure: {output_png} & {output_pdf} (size: {cropped.size[0]}x{cropped.size[1]})")


def render_drawio_file(drawio_path: Path, base_name: str, window_size: str = "1300,850") -> None:
    """Renders a single .drawio file to PNG and PDF in both figures/ and paper/figures/."""
    assert drawio_path.exists(), f"Drawio file not found: {drawio_path}"
    xml_content = drawio_path.read_text(encoding="utf-8")
    viewer_url = encode_drawio_to_viewer_url(xml_content)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_screenshot = Path(tmpdir) / "raw_capture.png"
        cmd = [
            "/usr/bin/google-chrome",
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-background-networking",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-sync",
            "--no-first-run",
            "--force-device-scale-factor=2",
            f"--window-size={window_size}",
            "--virtual-time-budget=6000",
            f"--screenshot={raw_screenshot}",
            viewer_url,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if not raw_screenshot.exists():
            sys.exit(f"Chrome rendering failed: {res.stderr}")

        # Crop and export to figures/
        fig_png = FIGURES_DIR / f"{base_name}.png"
        fig_pdf = FIGURES_DIR / f"{base_name}.pdf"
        autocrop_image(raw_screenshot, fig_png, fig_pdf)

        # Copy to paper/figures/
        paper_png = PAPER_FIGURES_DIR / f"{base_name}.png"
        paper_pdf = PAPER_FIGURES_DIR / f"{base_name}.pdf"
        import shutil
        shutil.copy2(fig_png, paper_png)
        shutil.copy2(fig_pdf, paper_pdf)
        print(f"[OK] Synchronized to {paper_png} and {paper_pdf}")


def main():
    parser = argparse.ArgumentParser(description="Render .drawio XML to high-res PNG and PDF.")
    parser.add_argument("drawio_file", type=Path, help="Path to .drawio XML file")
    parser.add_argument("-o", "--output-name", type=str, required=True, help="Base name of output figure (without extension)")
    parser.add_argument("--window-size", type=str, default="1500,900", help="Browser window dimensions W,H")
    args = parser.parse_args()

    render_drawio_file(args.drawio_file, args.output_name, args.window_size)


if __name__ == "__main__":
    main()
