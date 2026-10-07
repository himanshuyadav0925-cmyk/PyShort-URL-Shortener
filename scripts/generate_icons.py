"""
Generate crisp, modern, high-resolution PWA icons for PyShort.
Uses supersampling (4x) and downscales with Lanczos for anti-aliased results.
"""

import os
from PIL import Image, ImageDraw

ICONS_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "icons")
os.makedirs(ICONS_DIR, exist_ok=True)


def draw_pyshort_icon(size: int, is_maskable: bool = False) -> Image.Image:
    scale = 4
    canvas_size = size * scale
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center = canvas_size / 2

    if is_maskable:
        for y in range(canvas_size):
            factor = y / canvas_size
            r = int(11 + (22 - 11) * factor)
            g = int(15 + (32 - 15) * factor)
            b = int(25 + (50 - 25) * factor)
            draw.line([(0, y), (canvas_size, y)], fill=(r, g, b, 255))
        content_scale = 0.65
    else:
        corner_radius = int(canvas_size * 0.22)
        mask = Image.new("L", (canvas_size, canvas_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [(0, 0), (canvas_size - 1, canvas_size - 1)],
            radius=corner_radius,
            fill=255,
        )

        bg = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        bg_draw = ImageDraw.Draw(bg)
        for y in range(canvas_size):
            factor = y / canvas_size
            r = int(11 + (22 - 11) * factor)
            g = int(15 + (32 - 15) * factor)
            b = int(25 + (50 - 25) * factor)
            bg_draw.line([(0, y), (canvas_size, y)], fill=(r, g, b, 255))

        bg_draw.rounded_rectangle(
            [(scale * 2, scale * 2), (canvas_size - scale * 2, canvas_size - scale * 2)],
            radius=corner_radius - scale * 2,
            outline=(99, 102, 241, 70),
            width=scale * 3,
        )

        img.paste(bg, (0, 0), mask)
        draw = ImageDraw.Draw(img)
        content_scale = 0.82

    glow_radius = int(canvas_size * 0.28 * content_scale)
    glow_layer = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.ellipse(
        [
            (center - glow_radius, center - glow_radius),
            (center + glow_radius, center + glow_radius),
        ],
        fill=(99, 102, 241, 45),
    )
    img = Image.alpha_composite(img, glow_layer)
    draw = ImageDraw.Draw(img)

    s = canvas_size * content_scale
    ox = center - s / 2
    oy = center - s / 2

    ring_w = int(s * 0.08)
    link1_box = [
        ox + s * 0.20,
        oy + s * 0.42,
        ox + s * 0.52,
        oy + s * 0.74,
    ]
    draw.rounded_rectangle(link1_box, radius=int(s * 0.16), outline=(6, 182, 212, 230), width=ring_w)

    link2_box = [
        ox + s * 0.48,
        oy + s * 0.26,
        ox + s * 0.80,
        oy + s * 0.58,
    ]
    draw.rounded_rectangle(link2_box, radius=int(s * 0.16), outline=(6, 182, 212, 230), width=ring_w)

    bolt_points = [
        (ox + s * 0.54, oy + s * 0.12),
        (ox + s * 0.32, oy + s * 0.50),
        (ox + s * 0.48, oy + s * 0.50),
        (ox + s * 0.42, oy + s * 0.88),
        (ox + s * 0.72, oy + s * 0.46),
        (ox + s * 0.56, oy + s * 0.46),
    ]

    shadow_offset = int(scale * 3)
    shadow_points = [(x + shadow_offset, y + shadow_offset) for x, y in bolt_points]
    draw.polygon(shadow_points, fill=(11, 15, 25, 140))
    draw.polygon(bolt_points, fill=(129, 140, 248, 255))

    inner_bolt = [
        (ox + s * 0.52, oy + s * 0.18),
        (ox + s * 0.36, oy + s * 0.49),
        (ox + s * 0.49, oy + s * 0.49),
        (ox + s * 0.45, oy + s * 0.80),
        (ox + s * 0.67, oy + s * 0.47),
        (ox + s * 0.55, oy + s * 0.47),
    ]
    draw.polygon(inner_bolt, fill=(244, 247, 254, 230))

    return img.resize((size, size), Image.Resampling.LANCZOS)


def main():
    sizes = [
        (512, "icon-512.png", False),
        (512, "icon-maskable.png", True),
        (192, "icon-192.png", False),
        (180, "apple-touch-icon.png", False),
        (32, "favicon-32.png", False),
    ]

    for size, filename, is_maskable in sizes:
        path = os.path.join(ICONS_DIR, filename)
        icon = draw_pyshort_icon(size, is_maskable=is_maskable)
        icon.save(path, "PNG", optimize=True)
        print(f"Generated: {path} ({size}x{size})")


if __name__ == "__main__":
    main()
