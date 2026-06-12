"""Eye-training ball movement patterns (1–12)."""

from __future__ import annotations

import math
from typing import Callable

Point = tuple[float, float]
PatternFn = Callable[[float, float, float, float], Point]


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _path_phase(t: float) -> float:
    """Map time to [0, 1]; t=1.0 is the end of the path, not a wrap to the start."""
    frac = t % 1.0
    if frac == 0.0 and t > 0:
        return 1.0
    return frac


def _follow_polyline(points: list[Point], t: float) -> Point:
    """Move along a closed/open polyline with constant speed."""
    if len(points) < 2:
        return points[0] if points else (0.0, 0.0)

    segments: list[tuple[Point, Point, float]] = []
    total = 0.0
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        length = math.hypot(x2 - x1, y2 - y1)
        segments.append(((x1, y1), (x2, y2), length))
        total += length

    if total == 0:
        return points[0]

    target = _path_phase(t) * total
    walked = 0.0
    for (x1, y1), (x2, y2), length in segments:
        if walked + length >= target:
            local = (target - walked) / length if length else 0.0
            return (_lerp(x1, x2, local), _lerp(y1, y2, local))
        walked += length

    return points[-1]


def _ping_pong(t: float) -> float:
    """0→1→0 triangle wave for back-and-forth motion."""
    t = t % 1.0
    return 1.0 - abs(2.0 * t - 1.0)


def _bounds(w: float, h: float, margin: float) -> tuple[float, float, float, float]:
    return margin, margin, w - margin, h - margin


# --- Pattern 1: vertical line ---
def pattern_01_vertical(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    cx = (left + right) / 2
    y = _lerp(top, bottom, _ping_pong(t))
    return cx, y


# --- Pattern 2: horizontal line ---
def pattern_02_horizontal(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    cy = (top + bottom) / 2
    x = _lerp(left, right, _ping_pong(t))
    return x, cy


# --- Pattern 4: square (clockwise) ---
def pattern_04_square(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    points = [
        (left, top),
        (right, top),
        (right, bottom),
        (left, bottom),
        (left, top),
    ]
    return _follow_polyline(points, t)


# --- Pattern 5: bowtie ---
def pattern_05_bowtie(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    points = [
        (left, bottom),
        (left, top),
        (right, bottom),
        (right, top),
        (left, bottom),
    ]
    return _follow_polyline(points, t)


# --- Pattern 6: hourglass ---
def pattern_06_hourglass(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    points = [
        (left, top),
        (right, top),
        (left, bottom),
        (right, bottom),
        (left, top),
    ]
    return _follow_polyline(points, t)


# --- Pattern 7: circle (clockwise) ---
def pattern_07_circle(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    cx = (left + right) / 2
    cy = (top + bottom) / 2
    r = min(right - left, bottom - top) / 2
    angle = -2.0 * math.pi * (t % 1.0)
    return cx + r * math.cos(angle), cy + r * math.sin(angle)


# --- Pattern 8: vertical up, diagonal down-right (sawtooth) ---
def pattern_08_sawtooth(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    columns = 6
    col_w = (right - left) / (columns - 1)
    points: list[Point] = [(left, bottom)]
    for i in range(columns):
        x = left + i * col_w
        points.append((x, top))
        if i < columns - 1:
            points.append((left + (i + 1) * col_w, bottom))
    return _follow_polyline(points, t)


# --- Pattern 9: horizontal serpentine (zigzag rows) ---
def pattern_09_serpentine(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    rows = 5
    y_levels = [top + i * (bottom - top) / (rows - 1) for i in range(rows)]
    points: list[Point] = [(left, y_levels[0]), (right, y_levels[0])]
    for i in range(1, rows):
        points.append((left, y_levels[i]))
        points.append((right, y_levels[i]))
    return _follow_polyline(points, t)


# --- Pattern 10: five-pointed star (pentagram) ---
def pattern_10_star(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    cx = (left + right) / 2
    cy = (top + bottom) / 2
    r = min(right - left, bottom - top) / 2
    vertices: list[Point] = []
    for i in range(5):
        angle = -math.pi / 2 + i * 2 * math.pi / 5
        vertices.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    # Top -> bottom-right -> top-left -> top-right -> bottom-left -> top
    order = (0, 2, 4, 1, 3, 0)
    points = [vertices[i] for i in order]
    return _follow_polyline(points, t)


# --- Pattern 11: outward spiral (clockwise) ---
def pattern_11_spiral(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    cx = (left + right) / 2
    cy = (top + bottom) / 2
    max_r = min(right - left, bottom - top) / 2
    turns = 3.5
    samples = 400
    points: list[Point] = []
    for i in range(samples + 1):
        phase = i / samples
        theta = -2.0 * math.pi * turns * phase
        r = max_r * phase
        points.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))
    return _follow_polyline(points, t)


# --- Pattern 12: horizontal ellipse ---
def pattern_12_ellipse(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    cx = (left + right) / 2
    cy = (top + bottom) / 2
    a = (right - left) / 2
    b = (bottom - top) / 4
    angle = -2.0 * math.pi * (t % 1.0)
    return cx + a * math.cos(angle), cy + b * math.sin(angle)


def estimate_path_length(
    fn: PatternFn,
    w: float,
    h: float,
    margin: float,
    samples: int = 500,
) -> float:
    """Approximate total path length for constant-speed movement."""
    points = [fn(i / samples, w, h, margin) for i in range(samples + 1)]
    total = 0.0
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        total += math.hypot(x2 - x1, y2 - y1)
    return total


# Position is driven by the main loop; this is a list placeholder only.
def pattern_13_random(_t: float, w: float, h: float, margin: float) -> Point:
    return (w / 2, h / 2)


PATTERNS: list[tuple[str, str, PatternFn]] = [
    ("1", "Vertical line", pattern_01_vertical),
    ("2", "Horizontal line", pattern_02_horizontal),
    ("3", "Square", pattern_04_square),
    ("4", "Bowtie", pattern_05_bowtie),
    ("5", "Hourglass", pattern_06_hourglass),
    ("6", "Circle", pattern_07_circle),
    ("7", "Sawtooth", pattern_08_sawtooth),
    ("8", "Serpentine", pattern_09_serpentine),
    ("9", "Star", pattern_10_star),
    ("10", "Spiral", pattern_11_spiral),
    ("11", "Ellipse", pattern_12_ellipse),
    ("12", "Random jump", pattern_13_random),
]
