#!/usr/bin/env python3
"""Eye-training ball simulator — 12 movement patterns."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import pygame

from patterns import PATTERNS, estimate_path_length

# --- Display ---
INITIAL_WIDTH, INITIAL_HEIGHT = 1024, 768
MIN_WIDTH, MIN_HEIGHT = 480, 360
BG_COLOR = (255, 255, 255)
PATH_COLOR = (200, 200, 200)
TEXT_COLOR = (30, 30, 30)
HUD_BG = (245, 245, 245)

BALL_COLORS: list[tuple[str, tuple[int, int, int]]] = [
    ("Blue", (45, 118, 210)),
    ("Red", (214, 69, 69)),
    ("Teal", (0, 150, 136)),
    ("Green", (67, 160, 71)),
    ("Purple", (123, 97, 200)),
    ("Orange", (255, 138, 64)),
    ("Rose", (233, 99, 131)),
    ("Indigo", (84, 99, 186)),
    ("Amber", (230, 162, 60)),
    ("Cyan", (0, 172, 193)),
]

BLINK_BREAK_DURATION = 5.0
EYES_CLOSED_DURATION = 60.0
BLINK_MESSAGE = "Please blink actively"
EYES_CLOSED_MESSAGE = "Please sit with your eyes closed for a minute."

PATH_SAMPLES = 400
DEFAULT_SPEED = 0.32  # path-length multiplier (relative to pattern 1)
MIN_SPEED = 0.02
MAX_SPEED = 0.35

DEFAULT_PATTERN_DURATION = 30.0
MIN_PATTERN_DURATION = 5.0
MAX_PATTERN_DURATION = 180.0
DURATION_STEP = 5.0

DEFAULT_BALL_SCALE = 2.0
MIN_BALL_SCALE = 0.4
MAX_BALL_SCALE = 3.0
BALL_SCALE_STEP = 0.15

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"

# Patterns 7, 8, 10 — ball reverses at each end instead of jumping to the start.
PING_PONG_PATTERN_IDX = {6, 7, 9}
RANDOM_PATTERN_IDX = len(PATTERNS) - 1
RANDOM_JUMP_INTERVAL = 1.0


def load_window_size() -> tuple[int, int]:
    if not CONFIG_PATH.exists():
        return INITIAL_WIDTH, INITIAL_HEIGHT
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        w = int(data["width"])
        h = int(data["height"])
        return max(MIN_WIDTH, w), max(MIN_HEIGHT, h)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return INITIAL_WIDTH, INITIAL_HEIGHT


def save_window_size(width: int, height: int) -> None:
    CONFIG_PATH.write_text(
        json.dumps({"width": width, "height": height}, indent=2) + "\n",
        encoding="utf-8",
    )


def pick_random_ball_pos(
    width: int,
    height: int,
    margin: float,
    ball_radius: int,
    side: int,
) -> tuple[float, float]:
    """Pick a random position on the left (0) or right (1) half of the screen."""
    top = margin + ball_radius
    bottom = height - margin - ball_radius
    mid = width / 2
    if side == 0:
        x_min = margin + ball_radius
        x_max = mid - ball_radius
    else:
        x_min = mid + ball_radius
        x_max = width - margin - ball_radius

    if x_max <= x_min or bottom <= top:
        return width / 2, height / 2
    return random.uniform(x_min, x_max), random.uniform(top, bottom)


def sample_path(fn, w: float, h: float, margin: float, n: int = PATH_SAMPLES) -> list[tuple[int, int]]:
    # Sample [0, 1) so open paths don't draw a closing line back to the start.
    return [tuple(map(int, fn(i / n, w, h, margin))) for i in range(n)]


def layout_metrics(w: int, h: int, ball_scale: float = 1.0) -> tuple[float, int, int]:
    short = min(w, h)
    margin = max(40.0, short * 0.08)
    ball_radius = max(4, int(short * 0.014 * ball_scale))
    line_width = max(1, int(short * 0.002))
    return margin, ball_radius, line_width


def wrap_text(font: pygame.font.Font, text: str, max_width: int) -> list[pygame.Surface]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join(current + [word])
        if font.size(trial)[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return [font.render(line, True, TEXT_COLOR) for line in lines]


def draw_notification(
    screen: pygame.Surface,
    width: int,
    height: int,
    message: str,
    remaining: float | None = None,
) -> None:
    font_size = max(32, min(width, height) // 16)
    font = pygame.font.SysFont(None, font_size)
    pad = max(40, width // 12)
    surfaces = wrap_text(font, message, width - pad * 2)

    line_h = font.get_linesize()
    block_h = line_h * len(surfaces)
    if remaining is not None:
        block_h += line_h + 8

    y = (height - block_h) // 2
    for surf in surfaces:
        rect = surf.get_rect(center=(width // 2, y + line_h // 2))
        screen.blit(surf, rect)
        y += line_h

    if remaining is not None:
        countdown_font = pygame.font.SysFont(None, max(24, font_size - 8))
        countdown = countdown_font.render(f"{max(0, int(remaining + 0.999))}s remaining", True, TEXT_COLOR)
        countdown_rect = countdown.get_rect(center=(width // 2, y + line_h // 2 + 4))
        screen.blit(countdown, countdown_rect)


def draw_hud(
    screen: pygame.Surface,
    font: pygame.font.Font,
    pattern_idx: int,
    speed: float,
    paused: bool,
    width: int,
    auto_play: bool,
    pattern_duration: float,
    pattern_elapsed: float,
    ball_scale: float,
    color_name: str,
    session_state: str,
) -> None:
    _, name, _ = PATTERNS[pattern_idx]
    remaining = max(0.0, pattern_duration - pattern_elapsed)
    if session_state == "blink_break":
        status = "Blink break"
    elif session_state == "eyes_closed":
        status = "Eyes closed"
    else:
        status = f"{remaining:.0f}s left ({pattern_duration:.0f}s each)"

    lines = [
        f"Pattern {pattern_idx + 1}/{len(PATTERNS)}: {name}  |  Auto: {'ON' if auto_play else 'OFF'}  |  {status}",
        f"Speed: {speed:.2f}  Ball: {ball_scale:.1f}x  Color: {color_name}  {'[PAUSED]' if paused else ''}",
        "←/→ pattern  A:auto  ,/. time  B/S ball  C color  +/- speed  Space pause  G guide  H hide  Esc quit  (0 [ ] = 10-12)",
    ]
    pad = 10
    line_h = font.get_linesize()
    box_h = pad * 2 + line_h * len(lines)
    pygame.draw.rect(screen, HUD_BG, (0, 0, width, box_h))
    for i, line in enumerate(lines):
        surf = font.render(line, True, TEXT_COLOR)
        screen.blit(surf, (pad, pad + i * line_h))


def pattern_key_index(key: int) -> int | None:
    mapping = {
        pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3,
        pygame.K_5: 4, pygame.K_6: 5, pygame.K_7: 6, pygame.K_8: 7,
        pygame.K_9: 8, pygame.K_0: 9, pygame.K_LEFTBRACKET: 10, pygame.K_RIGHTBRACKET: 11,
    }
    return mapping.get(key)


def main() -> None:
    pygame.init()
    start_w, start_h = load_window_size()
    screen = pygame.display.set_mode((start_w, start_h), pygame.RESIZABLE)
    pygame.display.set_caption("Eye Tracker Simulator")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    pattern_idx = 0
    path_distance = 0.0
    path_direction = 1
    speed = DEFAULT_SPEED
    path_cache: dict[str, float] = {}
    paused = False
    show_guide = True
    show_hud = True
    auto_play = True
    pattern_duration = DEFAULT_PATTERN_DURATION
    pattern_elapsed = 0.0
    ball_scale = DEFAULT_BALL_SCALE
    color_idx = 0
    session_state = "playing"
    break_elapsed = 0.0
    random_ball_pos: tuple[float, float] | None = None
    random_jump_timer = 0.0
    random_side = 0

    def get_path_lengths(width: int, height: int, margin: float) -> tuple[float, float]:
        cache_key = f"{pattern_idx}:{width}:{height}:{margin:.1f}"
        if cache_key not in path_cache:
            _, _, fn = PATTERNS[pattern_idx]
            _, _, ref_fn = PATTERNS[0]
            path_cache[cache_key] = estimate_path_length(fn, width, height, margin)
            path_cache[f"ref:{width}:{height}:{margin:.1f}"] = estimate_path_length(
                ref_fn, width, height, margin
            )
        ref_key = f"ref:{width}:{height}:{margin:.1f}"
        return path_cache[cache_key], path_cache[ref_key]

    def select_pattern(idx: int) -> None:
        nonlocal pattern_idx, path_distance, path_direction, pattern_elapsed
        nonlocal session_state, break_elapsed, random_ball_pos, random_jump_timer, random_side
        pattern_idx = idx % len(PATTERNS)
        path_distance = 0.0
        path_direction = 1
        pattern_elapsed = 0.0
        session_state = "playing"
        break_elapsed = 0.0
        random_ball_pos = None
        random_jump_timer = 0.0
        random_side = random.randint(0, 1)
        path_cache.clear()

    running = True
    try:
        while running:
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    w = max(MIN_WIDTH, event.w)
                    h = max(MIN_HEIGHT, event.h)
                    screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                    save_window_size(w, h)
                    path_cache.clear()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                    elif event.key == pygame.K_g:
                        show_guide = not show_guide
                    elif event.key == pygame.K_h:
                        show_hud = not show_hud
                    elif event.key == pygame.K_a:
                        auto_play = not auto_play
                        pattern_elapsed = 0.0
                    elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                        select_pattern(pattern_idx + 1)
                    elif event.key in (pygame.K_LEFT, pygame.K_UP):
                        select_pattern(pattern_idx - 1)
                    elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                        speed = min(MAX_SPEED, speed + 0.02)
                    elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        speed = max(MIN_SPEED, speed - 0.02)
                    elif event.key in (pygame.K_COMMA, pygame.K_LESS):
                        pattern_duration = max(MIN_PATTERN_DURATION, pattern_duration - DURATION_STEP)
                        pattern_elapsed = min(pattern_elapsed, pattern_duration)
                    elif event.key in (pygame.K_PERIOD, pygame.K_GREATER):
                        pattern_duration = min(MAX_PATTERN_DURATION, pattern_duration + DURATION_STEP)
                    elif event.key == pygame.K_b:
                        ball_scale = min(MAX_BALL_SCALE, ball_scale + BALL_SCALE_STEP)
                    elif event.key == pygame.K_s:
                        ball_scale = max(MIN_BALL_SCALE, ball_scale - BALL_SCALE_STEP)
                    elif event.key == pygame.K_c:
                        color_idx = (color_idx + 1) % len(BALL_COLORS)
                    else:
                        idx = pattern_key_index(event.key)
                        if idx is not None:
                            select_pattern(idx)

            width, height = screen.get_size()
            margin, ball_radius, line_width = layout_metrics(width, height, ball_scale)
            phase = 0.0
            path_length = 0.0
            if session_state == "playing" and pattern_idx != RANDOM_PATTERN_IDX:
                path_length, ref_length = get_path_lengths(width, height, margin)
                phase = path_distance / path_length if path_length > 0 else 0.0

            if not paused:
                if session_state == "playing":
                    if pattern_idx == RANDOM_PATTERN_IDX:
                        random_jump_timer += dt
                        if random_ball_pos is None or random_jump_timer >= RANDOM_JUMP_INTERVAL:
                            if random_ball_pos is not None:
                                random_side = 1 - random_side
                            random_ball_pos = pick_random_ball_pos(
                                width, height, margin, ball_radius, random_side,
                            )
                            random_jump_timer = 0.0
                    else:
                        pixels_per_second = speed * ref_length
                        if path_length > 0:
                            if pattern_idx in PING_PONG_PATTERN_IDX:
                                path_distance += pixels_per_second * dt * path_direction
                                if path_distance >= path_length:
                                    path_distance = path_length
                                    path_direction = -1
                                elif path_distance <= 0:
                                    path_distance = 0.0
                                    path_direction = 1
                            else:
                                path_distance = (path_distance + pixels_per_second * dt) % path_length
                    if auto_play:
                        pattern_elapsed += dt
                        if pattern_elapsed >= pattern_duration:
                            pattern_elapsed = 0.0
                            if pattern_idx < len(PATTERNS) - 1:
                                session_state = "blink_break"
                                break_elapsed = 0.0
                            else:
                                session_state = "eyes_closed"
                                break_elapsed = 0.0
                elif session_state == "blink_break":
                    if auto_play:
                        break_elapsed += dt
                        if break_elapsed >= BLINK_BREAK_DURATION:
                            pattern_idx += 1
                            path_distance = 0.0
                            path_direction = 1
                            pattern_elapsed = 0.0
                            session_state = "playing"
                            break_elapsed = 0.0
                            path_cache.clear()
                    else:
                        session_state = "playing"
                        break_elapsed = 0.0
                elif session_state == "eyes_closed":
                    if auto_play:
                        break_elapsed += dt
                        if break_elapsed >= EYES_CLOSED_DURATION:
                            running = False
                    else:
                        session_state = "playing"
                        break_elapsed = 0.0

            color_name, ball_color = BALL_COLORS[color_idx]

            screen.fill(BG_COLOR)

            if session_state == "playing":
                if pattern_idx == RANDOM_PATTERN_IDX:
                    if random_ball_pos is None:
                        random_ball_pos = pick_random_ball_pos(
                            width, height, margin, ball_radius, random_side,
                        )
                    bx, by = random_ball_pos
                else:
                    _, _, fn = PATTERNS[pattern_idx]
                    bx, by = fn(phase, width, height, margin)

                    if show_guide:
                        path_points = sample_path(fn, width, height, margin)
                        if len(path_points) > 1:
                            pygame.draw.lines(screen, PATH_COLOR, False, path_points, line_width)

                bx, by = int(bx), int(by)

                pygame.draw.circle(screen, ball_color, (bx, by), ball_radius)
                pygame.draw.circle(screen, (0, 0, 0), (bx, by), ball_radius, max(1, line_width))
            elif session_state == "blink_break":
                remaining = BLINK_BREAK_DURATION - break_elapsed
                draw_notification(screen, width, height, BLINK_MESSAGE, remaining)
            elif session_state == "eyes_closed":
                remaining = EYES_CLOSED_DURATION - break_elapsed
                draw_notification(screen, width, height, EYES_CLOSED_MESSAGE, remaining)

            if show_hud:
                draw_hud(
                    screen, font, pattern_idx, speed, paused, width,
                    auto_play, pattern_duration, pattern_elapsed, ball_scale,
                    color_name, session_state,
                )
            pygame.display.flip()
    finally:
        width, height = screen.get_size()
        save_window_size(width, height)
        pygame.quit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)
