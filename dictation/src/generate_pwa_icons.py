"""Generate deterministic PNG PWA icons matching web/icon.svg."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 192px and 512px PWA icons.")
    parser.add_argument("--out-dir", default=str(Path(__file__).resolve().parent / "web"))
    args = parser.parse_args()

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise SystemExit("Pillow is missing. Install it with: python -m pip install Pillow") from exc

    output_dir = Path(args.out_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    font_path = find_japanese_font()
    for size in (192, 512):
        image = Image.new("RGB", (size, size), "#0d4a3c")
        draw = ImageDraw.Draw(image, "RGBA")
        margin = round(size * 0.165)
        draw.ellipse((margin, margin, size - margin, size - margin), fill=(246, 201, 112, 36))
        font = ImageFont.truetype(str(font_path), round(size * 0.48))
        glyph = "听"
        box = draw.textbbox((0, 0), glyph, font=font)
        width = box[2] - box[0]
        height = box[3] - box[1]
        position = ((size - width) / 2 - box[0], (size - height) / 2 - box[1] - size * 0.01)
        draw.text(position, glyph, font=font, fill="#ffffff")
        path = output_dir / f"icon-{size}.png"
        image.save(path, format="PNG", optimize=True)
        print(f"Generated: {path} ({size}x{size})")


def find_japanese_font() -> Path:
    candidates = (
        Path(r"C:\Windows\Fonts\YuGothB.ttc"),
        Path(r"C:\Windows\Fonts\meiryob.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise SystemExit("No suitable font found for the PWA icon.")


if __name__ == "__main__":
    main()
