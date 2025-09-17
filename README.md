# Duck Hunt

Duck Hunt — Improved Graphics is a Python arcade-style shooting game featuring 10 levels, animated ducks, smooth parallax clouds, particle hit effects, and an engaging HUD. Players aim with the mouse to hit ducks, manage limited bullets after level 5, and progress through increasingly challenging levels.

---

## Features
- 10 levels of increasing difficulty
- 5 health per level
- 10 hits required per level to advance
- Limited bullets after level 5 (configurable)
- Click to shoot; crosshair follows the mouse
- Smooth sky gradient, moving clouds, and parallax effects
- Ducks with shading, wing-flap animation, and soft shadows
- Particle hit effects for extra visual feedback
- HUD displays level, score, health, bullets, and hits
- Victory, level cleared, and fail screens

---

## Requirements
- Python 3.8+
- pygame  
Install pygame via pip:  
```bash
pip install pygame
How to Run
bash
Copy code
python DuckHunt.py
Left-click to shoot

Press ESC to quit

Press P to pause/resume

Press N to skip level (debug)

Configuration
TOTAL_LEVELS — total number of levels

HEALTH_PER_LEVEL — starting health per level

DUCKS_TO_CLEAR — hits required per level

BULLETS_AFTER_LEVEL_5 — bullets available starting from level 6

DUCK_BASE_SPEED — base duck speed

DUCK_SCALE — duck size scaling factor

License
This project is licensed under the Apache License 2.0.
