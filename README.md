# Eye Tracker Simulator

A local Pygame app for eye-training exercises. A red ball follows 12 movement patterns on screen.

## Setup

```bash
cd ~/eye-tracker-simulator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| `←` `→` | Previous / next pattern |
| `1`–`9` | Jump to pattern 1–9 |
| `0` | Pattern 10 (spiral) |
| `[` | Pattern 11 (ellipse) |
| `]` | Pattern 12 (random jump) |
| `A` | Toggle auto-play (1 → 12, then closes) |
| `,` / `.` | Decrease / increase time per pattern (5s steps, default 30s) |
| `B` / `S` | Bigger / smaller ball |
| `C` | Cycle ball color (10 colors; blue and red first) |
| `+` / `-` | Increase / decrease speed |
| `Space` | Pause / resume |
| `G` | Toggle path guide line |
| `H` | Hide / show on-screen text (HUD) |
| `Esc` | Quit |

During auto-play, a **blink reminder** appears for 5 seconds between patterns, and an **eyes-closed rest** screen appears for 1 minute after pattern 12 — then the app closes.

## Ball colors

1. Blue (default)
2. Red
3. Teal
4. Green
5. Purple
6. Orange
7. Rose
8. Indigo
9. Amber
10. Cyan

## Patterns

1. Vertical line
2. Horizontal line
3. Square (clockwise)
4. Bowtie
5. Hourglass
6. Circle (clockwise)
7. Sawtooth (vertical up, diagonal down)
8. Serpentine (horizontal rows)
9. Star (pentagram)
10. Spiral
11. Horizontal ellipse
12. Random jump (alternates left/right every second)
