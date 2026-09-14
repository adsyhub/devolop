import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pages")
    parser.add_argument("output")
    parser.add_argument("--columns", type=int, default=2)
    parser.add_argument("--rows", type=int, default=2)
    parser.add_argument("--cell-width", type=int, default=760)
    args = parser.parse_args()

    page_dir = Path(args.pages)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = sorted(page_dir.glob("page-*.png"))
    if not paths:
        raise SystemExit("no page PNGs found")

    margin = 28
    label_height = 32
    cell_width = args.cell_width
    with Image.open(paths[0]) as sample:
        ratio = sample.height / sample.width
    image_height = int(cell_width * ratio)
    cell_height = label_height + image_height
    per_sheet = args.columns * args.rows
    font = ImageFont.load_default()

    for sheet_index in range(math.ceil(len(paths) / per_sheet)):
        subset = paths[sheet_index * per_sheet : (sheet_index + 1) * per_sheet]
        canvas = Image.new(
            "RGB",
            (
                margin + args.columns * (cell_width + margin),
                margin + args.rows * (cell_height + margin),
            ),
            "#D9DEE5",
        )
        draw = ImageDraw.Draw(canvas)
        for offset, path in enumerate(subset):
            row, column = divmod(offset, args.columns)
            x = margin + column * (cell_width + margin)
            y = margin + row * (cell_height + margin)
            draw.text((x, y + 8), path.stem, fill="#1F2933", font=font)
            with Image.open(path) as page:
                page = page.convert("RGB")
                page.thumbnail((cell_width, image_height), Image.Resampling.LANCZOS)
                canvas.paste(page, (x, y + label_height))
        output_path = output_dir / f"contact-{sheet_index + 1:02d}.png"
        canvas.save(output_path, optimize=True)

    print(f"Created {math.ceil(len(paths) / per_sheet)} contact sheets in {output_dir}")


if __name__ == "__main__":
    main()
