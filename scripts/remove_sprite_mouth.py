#!/usr/bin/env python3
"""Remove a small mouth arc by interpolating clean skin from both sides."""

import argparse

from PIL import Image, ImageFilter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("output")
    parser.add_argument("--center-x", type=int, required=True)
    parser.add_argument("--center-y", type=int, required=True)
    parser.add_argument("--width", type=int, default=48)
    parser.add_argument("--height", type=int, default=22)
    parser.add_argument(
        "--axis",
        choices=("horizontal", "vertical"),
        default="horizontal",
        help="Interpolate from the clean sides or from clean skin above/below.",
    )
    args = parser.parse_args()

    image = Image.open(args.source).convert("RGBA")
    left = args.center_x - args.width // 2
    top = args.center_y - args.height // 2
    box = (left, top, left + args.width, top + args.height)
    pixels = image.load()
    clean_skin = Image.new("RGBA", (args.width, args.height))
    clean_pixels = clean_skin.load()
    if args.axis == "horizontal":
        for local_y in range(args.height):
            y = top + local_y
            left_color = tuple(
                sum(pixels[left - offset, y][channel] for offset in range(2, 7))
                // 5
                for channel in range(4)
            )
            right_color = tuple(
                sum(
                    pixels[left + args.width + offset, y][channel]
                    for offset in range(2, 7)
                )
                // 5
                for channel in range(4)
            )
            for local_x in range(args.width):
                ratio = local_x / max(args.width - 1, 1)
                clean_pixels[local_x, local_y] = tuple(
                    round(
                        left_color[channel] * (1 - ratio)
                        + right_color[channel] * ratio
                    )
                    for channel in range(4)
                )
    else:
        for local_x in range(args.width):
            x = left + local_x
            top_color = tuple(
                sum(pixels[x, top - offset][channel] for offset in range(2, 7))
                // 5
                for channel in range(4)
            )
            bottom_color = tuple(
                sum(
                    pixels[x, top + args.height + offset][channel]
                    for offset in range(2, 7)
                )
                // 5
                for channel in range(4)
            )
            for local_y in range(args.height):
                ratio = local_y / max(args.height - 1, 1)
                clean_pixels[local_x, local_y] = tuple(
                    round(
                        top_color[channel] * (1 - ratio)
                        + bottom_color[channel] * ratio
                    )
                    for channel in range(4)
                )

    mask = Image.new("L", (args.width, args.height), 0)
    ellipse = Image.new("L", (args.width - 4, args.height - 4), 255)
    mask.paste(ellipse, (2, 2))
    mask = mask.filter(ImageFilter.GaussianBlur(2))
    image.paste(clean_skin, box, mask)
    image.save(args.output)


if __name__ == "__main__":
    main()
