"""Colored report icons for UI and PDF (vector-drawn PNGs, not emoji)."""

from pathlib import Path

from PIL import Image, ImageDraw

from config.settings import ASSETS_DIR

ICON_DIR = ASSETS_DIR / "report_icons"

ICON_COLORS = {
    "daily_income": "#2563EB",
    "monthly_income": "#7C3AED",
    "yearly_income": "#059669",
    "patients": "#0EA5E9",
    "consultations": "#8B5CF6",
    "inventory": "#10B981",
    "low_stock": "#F59E0B",
    "expiring": "#EF4444",
    "billing": "#2563EB",
    "philhealth": "#007749",
    "default": "#475569",
}


def _hex_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _draw_calendar(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=max(4, (x1 - x0) // 8), outline=color, width=3, fill=(255, 255, 255, 255))
    header_h = max(8, (y1 - y0) // 4)
    draw.rectangle((x0 + 2, y0 + 2, x1 - 2, y0 + header_h), fill=color)
    cx = (x0 + x1) // 2
    for px in (cx - (x1 - x0) // 5, cx + (x1 - x0) // 5):
        draw.rectangle((px - 2, y0 - 4, px + 2, y0 + 4), fill=color)
    cell_w = (x1 - x0 - 12) // 3
    cell_h = (y1 - y0 - header_h - 10) // 2
    base_y = y0 + header_h + 6
    for row in range(2):
        for col in range(3):
            cx0 = x0 + 6 + col * cell_w
            cy0 = base_y + row * cell_h
            draw.rectangle((cx0, cy0, cx0 + cell_w - 3, cy0 + cell_h - 3), outline=color, width=1)


def _draw_chart(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    draw.line((x0, y1, x1, y1), fill=color, width=3)
    bars = [0.45, 0.75, 0.55, 0.9, 0.65]
    w = (x1 - x0 - 16) // len(bars)
    for i, h in enumerate(bars):
        bx0 = x0 + 8 + i * w
        bh = int((y1 - y0 - 12) * h)
        draw.rectangle((bx0, y1 - bh, bx0 + w - 4, y1), fill=color)


def _draw_person(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    r = (x1 - x0) // 5
    draw.ellipse((cx - r, y0 + 4, cx + r, y0 + 4 + 2 * r), fill=color)
    draw.pieslice((x0 + 6, y0 + 2 * r + 8, x1 - 6, y1), 180, 0, fill=color)


def _draw_stethoscope(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    draw.arc((x0 + 4, y0 + 4, x1 - 4, y1 - 8), 200, 340, fill=color, width=3)
    draw.ellipse((x1 - 18, y1 - 18, x1 - 4, y1 - 4), outline=color, width=3)
    draw.ellipse((x0 + 4, y1 - 16, x0 + 16, y1 - 4), fill=color)


def _draw_pill(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    mid = (x0 + x1) // 2
    h = y1 - y0 - 8
    draw.rounded_rectangle((x0 + 4, y0 + 8, mid, y0 + 8 + h), radius=h // 2, fill=color)
    light = tuple(min(255, c + 60) for c in color)
    draw.rounded_rectangle((mid, y0 + 8, x1 - 4, y0 + 8 + h), radius=h // 2, fill=light)


def _draw_warning(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    draw.polygon([(cx, y0 + 4), (x1 - 4, y1 - 4), (x0 + 4, y1 - 4)], outline=color, fill=(255, 255, 255, 255), width=3)
    draw.line((cx, y0 + 14, cx, y1 - 18), fill=color, width=3)
    draw.ellipse((cx - 2, y1 - 14, cx + 2, y1 - 10), fill=color)


def _draw_clock(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    draw.ellipse(box, outline=color, width=3)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    draw.line((cx, cy, cx, y0 + 12), fill=color, width=3)
    draw.line((cx, cy, x1 - 12, cy), fill=color, width=3)


def _draw_receipt(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle((x0 + 6, y0 + 4, x1 - 6, y1 - 4), radius=6, outline=color, width=3, fill=(255, 255, 255, 255))
    for i in range(4):
        yy = y0 + 14 + i * 10
        draw.line((x0 + 14, yy, x1 - 14, yy), fill=color, width=2)


def _draw_hospital(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    draw.rectangle((x0 + 10, y0 + 16, x1 - 10, y1 - 4), outline=color, width=3, fill=(255, 255, 255, 255))
    cx = (x0 + x1) // 2
    draw.rectangle((cx - 8, y0 + 4, cx + 8, y0 + 20), fill=color)
    draw.rectangle((cx - 3, y0 + 24, cx + 3, y0 + 40), fill=color)
    draw.rectangle((cx - 10, y0 + 31, cx + 10, y0 + 37), fill=color)


_DRAWERS = {
    "daily_income": _draw_calendar,
    "monthly_income": _draw_calendar,
    "yearly_income": _draw_chart,
    "patients": _draw_person,
    "consultations": _draw_stethoscope,
    "inventory": _draw_pill,
    "low_stock": _draw_warning,
    "expiring": _draw_clock,
    "billing": _draw_receipt,
    "philhealth": _draw_hospital,
}


def render_report_icon(report_key: str, size: int = 64) -> Image.Image:
    """Render a crisp icon image for the given report type."""
    color = _hex_rgb(ICON_COLORS.get(report_key, ICON_COLORS["default"]))
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = max(4, size // 10)
    box = (pad, pad, size - pad, size - pad)
    drawer = _DRAWERS.get(report_key, _draw_chart)
    drawer(draw, box, color)
    return img


def ensure_report_icon_path(report_key: str, size: int = 64) -> Path:
    """Return cached PNG path for a report icon."""
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    path = ICON_DIR / f"{report_key}_{size}.png"
    if not path.exists():
        render_report_icon(report_key, size).save(path, format="PNG")
    return path
