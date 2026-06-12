"""Eye-training ball movement patterns (1–12)."""

from __future__ import annotations

import math
from typing import Callable

Point = tuple[float, float]
PatternFn = Callable[[float, float, float, float], Point]


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


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

    target = (t % 1.0) * total
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


# --- Pattern 3: diagonal line ---
def pattern_03_diagonal(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    s = _ping_pong(t)
    return _lerp(left, right, s), _lerp(bottom, top, s)


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


# --- Pattern 8: zigzag / sawtooth ---
def pattern_08_zigzag(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    waves = 6
    total = waves * 2
    pos = (t % 1.0) * total
    idx = int(pos)
    local = pos - idx
    col_w = (right - left) / waves
    x1 = left + (idx // 2) * col_w
    x2 = x1 + col_w
    if idx % 2 == 0:
        return _lerp(x1, x2, local), _lerp(top, bottom, local)
    return _lerp(x1, x2, local), _lerp(bottom, top, local)


# --- Pattern 9: horizontal spring loops ---
def pattern_09_horizontal_spring(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    cy = (top + bottom) / 2
    loops = 5
    amp = (bottom - top) * 0.22
    phase = 2.0 * math.pi * loops * (t % 1.0)
    x = _lerp(left, right, t % 1.0) + amp * 0.35 * math.sin(phase)
    y = cy + amp * math.sin(phase)
    return x, y


# --- Pattern 10: vertical spring loops ---
def pattern_10_vertical_spring(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    cx = (left + right) / 2
    loops = 5
    amp = (right - left) * 0.22
    phase = 2.0 * math.pi * loops * (t % 1.0)
    y = _lerp(top, bottom, t % 1.0) + amp * 0.35 * math.sin(phase)
    x = cx + amp * math.sin(phase)
    return x, y


# --- Pattern 11: outward spiral (clockwise) ---
def pattern_11_spiral(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    cx = (left + right) / 2
    cy = (top + bottom) / 2
    max_r = min(right - left, bottom - top) / 2
    turns = 3.5
    theta = -2.0 * math.pi * turns * (t % 1.0)
    r = max_r * (t % 1.0)
    return cx + r * math.cos(theta), cy + r * math.sin(theta)


# --- Pattern 12: horizontal ellipse ---
def pattern_12_ellipse(t: float, w: float, h: float, margin: float) -> Point:
    left, top, right, bottom = _bounds(w, h, margin)
    cx = (left + right) / 2
    cy = (top + bottom) / 2
    a = (right - left) / 2
    b = (bottom - top) / 4
    angle = -2.0 * math.pi * (t % 1.0)
    return cx + a * math.cos(angle), cy + b * math.sin(angle)


PATTERNS: list[tuple[str, str, PatternFn]] = [
    ("1", "Vertical line", pattern_01_vertical),
    ("2", "Horizontal line", pattern_02_horizontal),
    ("3", "Diagonal line", pattern_03_diagonal),
    ("4", "Square", pattern_04_square),
    ("5", "Bowtie", pattern_05_bowtie),
    ("6", "Hourglass", pattern_06_hourglass),
    ("7", "Circle", pattern_07_circle),
    ("8", "Zigzag", pattern_08_zigzag),
    ("9", "Horizontal spring", pattern_09_horizontal_spring),
    ("10", "Vertical spring", pattern_10_vertical_spring),
    ("11", "Spiral", pattern_11_spiral),
    ("12", "Ellipse", pattern_12_ellipse),
]
