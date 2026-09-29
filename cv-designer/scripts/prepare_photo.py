#!/usr/bin/env python3
"""
Prepare a CV photo: fix EXIF rotation, crop to a square, resize, save as JPEG.

    python prepare_photo.py --in IMG_2031.jpg --out photo.jpg [--anchor top|center] [--size 600]

--anchor top   keeps the top of a portrait image (faces usually sit high); default.
--anchor center  plain centre crop.
Prints a JSON line with the output path and dimensions.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageOps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--anchor", choices=["top", "center"], default="top")
    ap.add_argument("--size", type=int, default=600)
    ap.add_argument("--quality", type=int, default=88)
    args = ap.parse_args()

    img = Image.open(args.src)
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    if args.anchor == "top":
        top = 0 if h > w else 0
        # keep a small margin above the head when the image is much taller than wide
        top = int((h - side) * 0.15) if h > w else 0
    else:
        top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((args.size, args.size), Image.LANCZOS)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    img.save(args.out, "JPEG", quality=args.quality, optimize=True)
    print(json.dumps({"photo": str(args.out), "size": args.size, "source": f"{w}x{h}", "anchor": args.anchor}))


if __name__ == "__main__":
    main()
