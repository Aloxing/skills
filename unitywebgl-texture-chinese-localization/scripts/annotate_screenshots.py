#!/usr/bin/env python3
"""Annotate game screenshots with numbered control boxes and batch-crop OCR regions."""

import argparse
import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PALETTE = [
    (255, 64, 64), (64, 160, 255), (64, 210, 110), (255, 190, 40),
    (200, 90, 255), (0, 220, 220), (255, 120, 200), (170, 170, 255),
]


BUNDLED_FONT = Path(__file__).resolve().parent.parent / "assets/FontLibrary/Sans/SourceHanSansSC/SourceHanSansSC-Regular.otf"

CJK_FONTS = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]


def load_font(size):
    for path in [os.environ.get("ANNOTATE_FONT"), str(BUNDLED_FONT), *CJK_FONTS]:
        if path and Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def load_screens(registry_path):
    data = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("screens") or data.get("controls") or []
    if data and "controls" not in data[0] and "bounds" in data[0]:
        data = [{"screen_id": data[0].get("screen_id", "screen"), "screenshot": None, "controls": data}]
    return data


def resolve(path, registry_dir):
    p = Path(path)
    if p.is_absolute():
        return p
    for base in (registry_dir, Path.cwd()):
        candidate = base / p
        if candidate.exists():
            return candidate
    return registry_dir / p


def control_number(control, position):
    value = control.get("index", control.get("number", position))
    try:
        return int(value)
    except (TypeError, ValueError):
        return position


def draw_control(draw, image_size, control, number, scale, font_ratio=0.022):
    bounds = control.get("bounds") or {}
    x = int(bounds.get("x", 0) * scale)
    y = int(bounds.get("y", 0) * scale)
    w = int(bounds.get("width", 0) * scale)
    h = int(bounds.get("height", 0) * scale)
    if w <= 0 or h <= 0:
        return None

    color = PALETTE[number % len(PALETTE)]
    line = max(2, int(min(image_size) / 400))
    draw.rectangle([x, y, x + w, y + h], outline=color, width=line)

    label = str(control.get("translated_label") or control.get("label") or control.get("control_id") or "")
    label = label.strip()
    if len(label) > 28:
        label = label[:27] + "…"
    text = f"[{number:02d}] {label}".strip()

    size = max(12, int(min(image_size) * font_ratio))
    font = load_font(size)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    tw, th = right - left, bottom - top
    pad = max(2, size // 4)
    tag_w = min(tw + pad * 2, image_size[0])
    tag_h = th + pad * 2

    tag_x = min(max(0, x), max(0, image_size[0] - tag_w))
    tag_y = y - tag_h if y - tag_h >= 0 else y
    draw.rectangle([tag_x, tag_y, tag_x + tag_w, tag_y + tag_h], fill=color)
    draw.text((tag_x + pad - left, tag_y + pad - top), text, fill=(0, 0, 0), font=font)
    return (x, y, w, h)


def annotate(args):
    registry_path = Path(args.registry)
    registry_dir = registry_path.parent
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    screens = load_screens(registry_path)

    total = 0
    for screen in screens:
        screenshot = screen.get("screenshot") or args.screenshot
        if not screenshot:
            print(f"SKIP screen={screen.get('screen_id')} reason=no_screenshot_field")
            continue
        image_path = resolve(screenshot, registry_dir)
        if not image_path.exists():
            print(f"SKIP screen={screen.get('screen_id')} reason=screenshot_not_found path={image_path}")
            continue

        with Image.open(image_path) as source:
            image = source.convert("RGBA")
        draw = ImageDraw.Draw(image)
        count = 0
        for position, control in enumerate(screen.get("controls") or [], start=1):
            if draw_control(draw, image.size, control, control_number(control, position), args.scale):
                count += 1

        target = out_dir / f"{image_path.stem}_annotated.png"
        image.convert("RGB").save(target)
        total += count
        print(f"OK image={target} controls={count} size={image.size[0]}x{image.size[1]}")

    print(f"DONE screens={len(screens)} controls_drawn={total} out_dir={out_dir}")
    return 0


def crop(args):
    registry_path = Path(args.registry)
    registry_dir = registry_path.parent
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    screens = load_screens(registry_path)

    total = 0
    for screen in screens:
        screenshot = screen.get("screenshot") or args.screenshot
        if not screenshot:
            continue
        image_path = resolve(screenshot, registry_dir)
        if not image_path.exists():
            print(f"SKIP screen={screen.get('screen_id')} reason=screenshot_not_found path={image_path}")
            continue

        with Image.open(image_path) as source:
            image = source.convert("RGB")
        screen_dir = out_dir / str(screen.get("screen_id") or image_path.stem)
        screen_dir.mkdir(parents=True, exist_ok=True)

        for position, control in enumerate(screen.get("controls") or [], start=1):
            bounds = control.get("bounds") or {}
            factor = args.scale
            x, y = int(bounds.get("x", 0) * factor), int(bounds.get("y", 0) * factor)
            w, h = int(bounds.get("width", 0) * factor), int(bounds.get("height", 0) * factor)
            if w <= 0 or h <= 0:
                continue
            left, top = max(0, x), max(0, y)
            right, bottom = min(image.width, x + w), min(image.height, y + h)
            if right <= left or bottom <= top:
                continue
            piece = image.crop((left, top, right, bottom))
            if args.enlarge != 1:
                piece = piece.resize(
                    (piece.width * args.enlarge, piece.height * args.enlarge),
                    Image.LANCZOS,
                )
            name = control.get("control_id") or f"control_{position:03d}"
            target = screen_dir / f"{name}.png"
            piece.save(target)
            total += 1
        print(f"OK screen={screen.get('screen_id')} crops={len(list(screen_dir.glob('*.png')))} dir={screen_dir}")

    print(f"DONE crops={total} out_dir={out_dir}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Annotate screenshots and crop OCR regions from a control registry.")
    sub = parser.add_subparsers(dest="command", required=True)

    a = sub.add_parser("annotate", help="draw numbered boxes for every control")
    a.add_argument("--registry", required=True, help="control_registry.json")
    a.add_argument("--out-dir", default="AnnotatedScreenshots")
    a.add_argument("--screenshot", help="screenshot path to use for a flat control list")
    a.add_argument("--scale", type=float, default=1.0, help="coordinate-to-pixel factor, e.g. 2 when bounds are CSS px and the screenshot is 2x")
    a.set_defaults(func=annotate)

    c = sub.add_parser("crop", help="crop every control region, optionally enlarged for OCR")
    c.add_argument("--registry", required=True)
    c.add_argument("--out-dir", default="CroppedRegions")
    c.add_argument("--screenshot", help="screenshot path to use for a flat control list")
    c.add_argument("--scale", type=float, default=1.0, help="coordinate-to-pixel factor for cropping")
    c.add_argument("--enlarge", type=int, default=1)
    c.set_defaults(func=crop)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"ERROR file_not_found: {exc}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR invalid_registry_json: {exc}")
        return 1
    except Exception as exc:
        print(f"ERROR {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
