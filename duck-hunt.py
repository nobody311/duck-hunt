"""
DuckHunt.py — Improved graphics, full game

Features
- 10 levels
- 5 health per level
- 10 hits required per level to advance
- After level 5, bullets are limited (configurable)
- Click to shoot. Crosshair follows the mouse.
- Smooth sky gradient, moving clouds, parallax, ground
- Ducks with shading, wing-flap animation, soft shadows
- Particle hit effects, HUD, messages, victory & fail screens

Requirements:
- Python 3.8+
- pygame (pip install pygame)

Run:
python DuckHunt.py
"""
import pygame
import random
import math
import sys
from typing import List

# -------------------- Config --------------------
TOTAL_LEVELS = 10
HEALTH_PER_LEVEL = 5
DUCKS_TO_CLEAR = 10          # hits required per level
BULLETS_AFTER_LEVEL_5 = 15    # bullets available starting from level 6
SCREEN_W, SCREEN_H = 1000, 640
FPS = 60

# Graphics tuning
DUCK_BASE_SPEED = 120
DUCK_SCALE = 1.0

# Colors
WHITE = (255, 255, 255)
BLACK = (12, 12, 12)
SKY_TOP = (142, 198, 255)
SKY_BOTTOM = (88, 151, 215)
GRASS = (60, 145, 70)
GROUND_DARK = (35, 100, 40)
CLOUD_COLOR = (255, 255, 255, 220)

# Safety for mixer if not available
SOUND_ENABLED = True

# -------------------- Pygame init --------------------
pygame.init()
try:
    pygame.mixer.init()
except Exception:
    SOUND_ENABLED = False

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption('Duck Hunt — Improved Graphics')
clock = pygame.time.Clock()

# Fonts
def get_font(name, size, bold=False):
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.SysFont(None, size, bold=bold)

font = get_font('Segoe UI', 20)
bigfont = get_font('Segoe UI', 48, bold=True)
smallfont = get_font('Segoe UI', 16)

# Load sounds (graceful fallback)
sound_shot = None
sound_hit = None
try:
    if SOUND_ENABLED:
        # Using simple beep-like tones is complicated here, skip if not present.
        # If you have sound files, you can load them here.
        pass
except Exception:
    pass

# -------------------- Utility --------------------
def clamp(x, a, b):
    return max(a, min(b, x))

def lerp(a, b, t):
    return a + (b - a) * t

# -------------------- Visual helpers --------------------
def draw_sky_gradient(surf):
    # vertical gradient
    for y in range(SCREEN_H):
        t = y / SCREEN_H
        r = int(lerp(SKY_TOP[0], SKY_BOTTOM[0], t))
        g = int(lerp(SKY_TOP[1], SKY_BOTTOM[1], t))
        b = int(lerp(SKY_TOP[2], SKY_BOTTOM[2], t))
        pygame.draw.line(surf, (r, g, b), (0, y), (SCREEN_W, y))

class Cloud:
    def __init__(self, x, y, scale, speed):
        self.x = x
        self.y = y
        self.scale = scale
        self.speed = speed
        self.w = int(260 * scale)
        self.h = int(80 * scale)
        # cloud surface for soft alpha
        self.surface = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self._render()

    def _render(self):
        s = self.surface
        s.fill((0,0,0,0))
        # draw multiple overlapping ellipses
        for i in range(6):
            rx = int(self.w * (0.2 + random.random() * 0.6))
            ry = int(self.h * (0.5 + random.random() * 0.4))
            ox = int(random.random() * (self.w - rx))
            oy = int(random.random() * (self.h - ry))
            alpha = 200 - i * 20
            pygame.draw.ellipse(s, (255,255,255,alpha), (ox, oy, rx, ry))

    def update(self, dt):
        self.x += self.speed * dt
        if self.speed > 0 and self.x - self.w > SCREEN_W + 100:
            self.x = -self.w - random.randint(0, 200)
        if self.speed < 0 and self.x + self.w < -200:
            self.x = SCREEN_W + random.randint(0, 200)

    def draw(self, surf):
        surf.blit(self.surface, (int(self.x), int(self.y)))

# -------------------- Game objects --------------------
class Duck:
    def __init__(self, level:int):
        self.level = level
        side = random.choice(['left', 'right'])
        self.y = random.randint(110, SCREEN_H - 220)
        if side == 'left':
            self.x = -80
            self.vx = 1
        else:
            self.x = SCREEN_W + 80
            self.vx = -1
        speed_factor = 1.0 + (level - 1) * 0.12
        dir_sign = 1 if self.vx > 0 else -1
        self.vx = dir_sign * DUCK_BASE_SPEED * speed_factor * (0.95 + random.random() * 0.35)
        self.amp = 18 + random.random() * 18
        self.period = 1.0 + random.random() * 1.6
        self.age = 0.0
        self.dead = False
        self.fall_speed = 0.0
        self.hit_anim = 0.0
        self.width = int(68 * DUCK_SCALE)
        self.height = int(56 * DUCK_SCALE)
        self.flap = random.random() * 2 * math.pi
        # color palette (vary slightly by level)
        base = clamp(140 + level * 6, 140, 250)
        self.body_color = (base, clamp(90 + level*3, 90, 200), clamp(50, 50, 180))
        self.wing_color = (clamp(base+30,0,255), clamp(140 + level*2,0,255), clamp(90,0,255))
        self.head_color = (60, 70, 95)
        self.spawn_time = 0.0

    def update(self, dt):
        self.spawn_time += dt
        if self.dead:
            self.fall_speed += 600 * dt
            self.y += self.fall_speed * dt
            self.x += 60 * dt * (1 if random.random() > 0.5 else -1)
            self.hit_anim += dt
            return
        self.age += dt
        # subtle vertical wobble
        self.y += math.sin(self.age * (2 * math.pi) / self.period) * self.amp * dt
        self.x += self.vx * dt
        self.flap += dt * 20

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        # soft shadow below the duck: draw to an alpha surface and blit
        shadow_w = int(self.width * 1.1)
        shadow_h = int(self.height * 0.4)
        shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0,0,0,90), (0, 0, shadow_w, shadow_h))
        surf.blit(shadow_surf, (cx - shadow_w//2, cy + self.height//2 + 6))

        # body ellipse
        body_rect = pygame.Rect(cx - self.width//2, cy - self.height//2, self.width, self.height)
        # subtle shading: draw two ellipses
        dark = tuple(clamp(c-20,0,255) for c in self.body_color)
        pygame.draw.ellipse(surf, dark, (body_rect.x+6, body_rect.y+6, body_rect.w, body_rect.h))
        pygame.draw.ellipse(surf, self.body_color, body_rect)

        # wing - flap animation (slightly rotated by sin)
        wing_offset = int(math.sin(self.flap) * 12)
        wing_rect = pygame.Rect(cx - self.width//2, cy - self.height//4 - wing_offset, int(self.width*0.9), int(self.height*0.6))
        pygame.draw.ellipse(surf, self.wing_color, wing_rect)

        # head
        head_w, head_h = 34, 30
        head_x = cx + (self.width//3) * (1 if self.vx > 0 else -1) - (0 if self.vx > 0 else head_w)
        head_rect = pygame.Rect(head_x, cy - self.height//2 - 2, head_w, head_h)
        pygame.draw.ellipse(surf, self.head_color, head_rect)
        # beak
        if self.vx > 0:
            beak = [(head_rect.right-4, head_rect.centery), (head_rect.right+20, head_rect.centery-6), (head_rect.right+20, head_rect.centery+6)]
        else:
            beak = [(head_rect.left+4, head_rect.centery), (head_rect.left-20, head_rect.centery-6), (head_rect.left-20, head_rect.centery+6)]
        pygame.draw.polygon(surf, (240,200,60), beak)
        # eye
        eye_x = head_rect.centerx + (6 if self.vx > 0 else -6)
        eye_y = head_rect.centery - 4
        pygame.draw.circle(surf, WHITE, (eye_x, eye_y), 5)
        pygame.draw.circle(surf, BLACK, (eye_x, eye_y), 2)

    def hit_test(self, px, py):
        # elliptical hit area
        if self.dead:
            return False
        dx = px - self.x
        dy = py - self.y
        rx = self.width * 0.6
        ry = self.height * 0.6
        if (dx*dx)/(rx*rx) + (dy*dy)/(ry*ry) <= 1:
            return True
        return False

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-220, 220)
        self.vy = random.uniform(-160, -40)
        self.life = random.uniform(0.5, 1.1)
        self.age = 0.0
        self.size = random.uniform(2, 6)
        self.color = (255, 220, 110)

    def update(self, dt):
        self.age += dt
        self.vy += 600 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surf):
        t = clamp(1 - self.age / self.life, 0, 1)
        if t <= 0:
            return
        r = int(self.size * t)
        if r < 1:
            r = 1
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), r)

# -------------------- Game --------------------
class Game:
    def __init__(self):
        self.level = 1
        self.score = 0
        self.health = HEALTH_PER_LEVEL
        self.bullets = math.inf
        self.ducks: List[Duck] = []
        self.particles: List[Particle] = []
        self.hits_this_level = 0
        self.time_since_last_spawn = 0.0
        self.spawn_rate = 1.2
        self.running = True
        self.paused = False
        self.message = ''
        self.message_time = 0.0
        self.state = 'playing'   # playing, level_end, game_over, victory
        self.clouds = []
        self._make_clouds()
        self._setup_level()

    def _make_clouds(self):
        self.clouds = []
        for i in range(7):
            x = random.randint(-400, SCREEN_W + 400)
            y = random.randint(30, 180)
            scale = random.uniform(0.6, 1.4)
            speed = random.uniform(8, 30) * (0.5 if i % 2 == 0 else 1.0)
            if random.random() < 0.4:
                speed *= -1
            c = Cloud(x, y, scale, speed)
            self.clouds.append(c)

    def _setup_level(self):
        self.health = HEALTH_PER_LEVEL
        self.hits_this_level = 0
        self.ducks.clear()
        self.particles.clear()
        self.time_since_last_spawn = 0.0
        if self.level > 5:
            self.bullets = BULLETS_AFTER_LEVEL_5
        else:
            self.bullets = math.inf
        self.spawn_rate = max(0.35, 1.2 - (self.level - 1) * 0.08)
        self.message = f'Level {self.level} — Get {DUCKS_TO_CLEAR} hits!'
        self.message_time = 2.2
        self.state = 'playing'

    def spawn_duck(self):
        d = Duck(self.level)
        self.ducks.append(d)

    def update(self, dt):
        # update clouds (parallax)
        for i, c in enumerate(self.clouds):
            # slower movement for far clouds
            c.update(dt)

        if self.state != 'playing':
            self.message_time = max(0, self.message_time - dt)
            return

        # spawn control
        self.time_since_last_spawn += dt
        if self.time_since_last_spawn >= self.spawn_rate:
            self.time_since_last_spawn = 0
            self.spawn_duck()
            if random.random() < clamp((self.level - 1) * 0.06, 0, 0.45):
                self.spawn_duck()

        # update ducks
        for d in list(self.ducks):
            d.update(dt)
            # escaped ducks
            if not d.dead:
                if d.x < -140 or d.x > SCREEN_W + 140:
                    # duck escaped
                    try:
                        self.ducks.remove(d)
                    except ValueError:
                        pass
                    self.health -= 1
                    self.message = 'Duck escaped! -1 health'
                    self.message_time = 1.6
                    if self.health <= 0:
                        self._on_level_failed()
            else:
                # remove after falling past ground or long enough
                if d.y > SCREEN_H + 120 or d.hit_anim > 3.0:
                    try:
                        self.ducks.remove(d)
                    except ValueError:
                        pass

        # update particles
        for p in list(self.particles):
            p.update(dt)
            if p.age > p.life:
                try:
                    self.particles.remove(p)
                except ValueError:
                    pass

        # level completion
        if self.hits_this_level >= DUCKS_TO_CLEAR:
            self._on_level_cleared()

    def draw_hud(self, surf):
        # hud background
        pygame.draw.rect(surf, (255,255,255,230), (8, 8, SCREEN_W - 16, 46), border_radius=8)
        # level
        lv = font.render(f'Level: {self.level}/{TOTAL_LEVELS}', True, BLACK)
        surf.blit(lv, (18, 14))
        # score
        sc = font.render(f'Score: {self.score}', True, BLACK)
        surf.blit(sc, (170, 14))
        # health hearts
        hx = 320
        for i in range(HEALTH_PER_LEVEL):
            r = pygame.Rect(hx + i*30, 12, 24, 24)
            if i < self.health:
                # draw a heart (simple)
                pygame.draw.ellipse(surf, (255,80,90), (r.x+4, r.y+6, 12, 12))
                pygame.draw.ellipse(surf, (255,80,90), (r.x+12, r.y+6, 12, 12))
                points = [(r.x+4, r.y+12), (r.x+12, r.y+22), (r.x+20, r.y+12)]
                pygame.draw.polygon(surf, (255,80,90), points)
            else:
                pygame.draw.ellipse(surf, (220,220,220), (r.x+4, r.y+6, 12, 12))
                pygame.draw.ellipse(surf, (220,220,220), (r.x+12, r.y+6, 12, 12))
                points = [(r.x+4, r.y+12), (r.x+12, r.y+22), (r.x+20, r.y+12)]
                pygame.draw.polygon(surf, (220,220,220), points)
        # bullets
        bx = 520
        btxt = '∞' if math.isinf(self.bullets) else str(int(self.bullets))
        bl = font.render(f'Bullets: {btxt}', True, BLACK)
        surf.blit(bl, (bx, 14))
        # hits
        hits = font.render(f'Hits: {self.hits_this_level}/{DUCKS_TO_CLEAR}', True, BLACK)
        surf.blit(hits, (700, 14))

    def draw(self, surf):
        # background sky
        draw_sky_gradient(surf)
        # clouds (drawed behind ducks)
        for c in self.clouds:
            c.draw(surf)
        # ground / horizon
        pygame.draw.rect(surf, GRASS, (0, SCREEN_H - 120, SCREEN_W, 120))
        # subtle ground stripes
        for i in range(0, SCREEN_W, 60):
            pygame.draw.rect(surf, GROUND_DARK, (i, SCREEN_H - 80, 30, 80))

        # ducks
        for d in self.ducks:
            d.draw(surf)

        # particles
        for p in self.particles:
            p.draw(surf)

        # HUD
        self.draw_hud(surf)

        # draw crosshair at mouse
        mx, my = pygame.mouse.get_pos()
        pygame.draw.circle(surf, WHITE, (mx, my), 12, 2)
        pygame.draw.line(surf, WHITE, (mx-22, my), (mx-8, my), 2)
        pygame.draw.line(surf, WHITE, (mx+8, my), (mx+22, my), 2)
        pygame.draw.line(surf, WHITE, (mx, my-22), (mx, my-8), 2)
        pygame.draw.line(surf, WHITE, (mx, my+8), (mx, my+22), 2)

        # message
        if self.message_time > 0 and self.message:
            msg = smallfont.render(self.message, True, BLACK)
            surf.blit(msg, (SCREEN_W//2 - msg.get_width()//2, 64))

        # overlays for states
        if self.state == 'level_end':
            s = bigfont.render(f'Level {self.level} Cleared!', True, BLACK)
            surf.blit(s, (SCREEN_W//2 - s.get_width()//2, SCREEN_H//2 - 80))
            sub = font.render('Click to continue', True, BLACK)
            surf.blit(sub, (SCREEN_W//2 - sub.get_width()//2, SCREEN_H//2 - 10))
        elif self.state == 'game_over':
            s = bigfont.render('Level Failed', True, BLACK)
            surf.blit(s, (SCREEN_W//2 - s.get_width()//2, SCREEN_H//2 - 80))
            sub = font.render('Click to retry level', True, BLACK)
            surf.blit(sub, (SCREEN_W//2 - sub.get_width()//2, SCREEN_H//2 - 10))
        elif self.state == 'victory':
            s = bigfont.render('Victory!', True, BLACK)
            surf.blit(s, (SCREEN_W//2 - s.get_width()//2, SCREEN_H//2 - 80))
            sub = font.render('You cleared all levels. Click to restart.', True, BLACK)
            surf.blit(sub, (SCREEN_W//2 - sub.get_width()//2, SCREEN_H//2 - 10))

    def shoot_at(self, x, y):
        if self.state != 'playing':
            return
        if self.bullets == 0:
            self.message = 'No bullets!'
            self.message_time = 1.6
            return
        if not math.isinf(self.bullets):
            self.bullets -= 1
        # hit test sorted by nearest
        hit_any = False
        for d in sorted(self.ducks, key=lambda k: math.hypot(k.x - x, k.y - y)):
            if d.hit_test(x, y):
                hit_any = True
                d.dead = True
                d.fall_speed = 80 + random.random()*80
                self.score += 100 + self.level * 20
                self.hits_this_level += 1
                # particles
                for _ in range(16):
                    self.particles.append(Particle(d.x, d.y))
                self.message = 'Hit!'
                self.message_time = 1.2
                # play sound if available
                try:
                    if SOUND_ENABLED and sound_hit:
                        sound_hit.play()
                except Exception:
                    pass
                break
        if not hit_any:
            self.message = 'Miss!'
            self.message_time = 0.9

    def on_click(self, x, y):
        if self.state == 'playing':
            self.shoot_at(x, y)
        elif self.state == 'level_end':
            # advance
            if self.level >= TOTAL_LEVELS:
                self.state = 'victory'
            else:
                self.level += 1
                self._setup_level()
        elif self.state == 'game_over':
            self._setup_level()
        elif self.state == 'victory':
            # restart game
            self.level = 1
            self.score = 0
            self._setup_level()

    def _on_level_cleared(self):
        self.message = f'Level {self.level} complete!'
        self.message_time = 2.5
        if self.level >= TOTAL_LEVELS:
            self.state = 'victory'
        else:
            self.state = 'level_end'

    def _on_level_failed(self):
        self.message = f'Level {self.level} failed.'
        self.message_time = 2.5
        self.state = 'game_over'

# -------------------- Main loop --------------------
def main():
    game = Game()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                game.on_click(mx, my)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_p:
                    game.paused = not game.paused
                elif event.key == pygame.K_n:
                    # debug: skip level
                    if game.state == 'playing':
                        game.hits_this_level = DUCKS_TO_CLEAR
        if not running:
            break

        if not game.paused:
            game.update(dt)

        # draw everything
        game.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
