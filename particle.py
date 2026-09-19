
import math
import random
import pygame
from config import (
    CYAN, CYAN_LIGHT, CYAN_GLOW,
    GOLD, GOLD_LIGHT, GOLD_GLOW,
    JADE_LIGHT,
    PETAL, PETAL_LIGHT, WARNING,
)


class Particle:
    """通用粒子：位置、速度、生命、颜色、尺寸、形态。

    kind: "circle" 光点 / "petal" 花瓣（自转菱形）/ "spark" 棱角星点
    """

    __slots__ = ("x", "y", "vx", "vy", "life", "max_life",
                 "color", "size", "gravity", "fade",
                 "kind", "ang", "ang_v")

    def __init__(self, x, y, vx, vy, life, color, size,
                 gravity=0.0, fade=True, kind="circle",
                 ang=0.0, ang_v=0.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.gravity = gravity
        self.fade = fade
        self.kind = kind
        self.ang = ang
        self.ang_v = ang_v

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.ang += self.ang_v * dt
        self.vx *= 0.985
        self.vy *= 0.985

    @property
    def alive(self):
        return self.life > 0

    def draw(self, screen):
        if self.life <= 0:
            return
        t = max(0.0, self.life / self.max_life)
        alpha = int(255 * t) if self.fade else 200
        r = max(1, int(self.size * (t if self.fade else 1.0)))

        if self.kind == "petal":
            d = r * 2 + 6
            surf = pygame.Surface((d, d), pygame.SRCALPHA)
            ca = math.cos(self.ang)
            sa = math.sin(self.ang)
            pts = []
            for px, py in [(0, -r * 1.7), (r * 0.8, 0),
                           (0, r * 1.7), (-r * 0.8, 0)]:
                rx = px * ca - py * sa + d // 2
                ry = px * sa + py * ca + d // 2
                pts.append((rx, ry))
            pygame.draw.polygon(surf, (*self.color, alpha), pts)
            screen.blit(surf, (int(self.x) - d // 2, int(self.y) - d // 2))
            return

        if self.kind == "spark":
            d = r * 2 + 2
            surf = pygame.Surface((d, d), pygame.SRCALPHA)
            pygame.draw.rect(surf, (*self.color, alpha),
                             (1, 1, r * 2, r * 2), border_radius=1)
            screen.blit(surf, (int(self.x) - r - 1, int(self.y) - r - 1))
            return

        surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (r + 1, r + 1), r)
        screen.blit(surf, (int(self.x) - r - 1, int(self.y) - r - 1))


class ParticleSystem:
    """粒子集合管理：发射、更新、绘制。"""

    def __init__(self):
        self.particles = []

    def add(self, p):
        self.particles.append(p)

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

    def draw(self, screen):
        for p in self.particles:
            p.draw(screen)

    def clear(self):
        self.particles.clear()

    # ---------- 工厂方法 ----------

    def emit_sword_burst(self, x, y, count=22):
        """飞剑离场：青金剑气四散，夹一瓣落花。"""
        for _ in range(count):
            ang = random.uniform(0, 6.2831853)
            speed = random.uniform(70, 250)
            vx = math.cos(ang) * speed
            vy = math.sin(ang) * speed
            col = random.choice([CYAN, CYAN_LIGHT, GOLD_GLOW, GOLD_LIGHT])
            self.add(Particle(x, y, vx, vy,
                              random.uniform(0.35, 0.7),
                              col, random.uniform(2, 5),
                              gravity=60, kind="spark"))
        for _ in range(3):
            self.add(Particle(
                x, y, random.uniform(-40, 40), random.uniform(-70, -10),
                random.uniform(0.8, 1.4),
                random.choice([PETAL, PETAL_LIGHT]),
                random.uniform(3, 5), gravity=30, kind="petal",
                ang=random.uniform(0, 6), ang_v=random.uniform(-3, 3)))

    def emit_eye_awaken(self, x, y, count=12):
        """阵眼解除：符文金青光环浮现，花瓣升起。"""
        for i in range(count):
            ang = (i / count) * 6.2831853
            speed = random.uniform(50, 100)
            vx = math.cos(ang) * speed
            vy = math.sin(ang) * speed - 30
            col = random.choice([GOLD_GLOW, GOLD_LIGHT, JADE_LIGHT])
            self.add(Particle(x, y, vx, vy,
                              random.uniform(0.5, 0.95),
                              col, random.uniform(2, 4),
                              gravity=-24, kind="spark"))
        for _ in range(2):
            self.add(Particle(
                x + random.uniform(-12, 12),
                y + random.uniform(-12, 12),
                random.uniform(-20, 20), random.uniform(-55, -25),
                random.uniform(1.0, 1.6),
                random.choice([PETAL, PETAL_LIGHT]),
                random.uniform(3, 5), gravity=-10, kind="petal",
                ang=random.uniform(0, 6), ang_v=random.uniform(-4, 4)))

    def emit_qi_trail(self, x, y):
        """剑气拖尾：青蓝微光。"""
        for _ in range(2):
            self.add(Particle(
                x + random.uniform(-4, 4),
                y + random.uniform(-4, 4),
                random.uniform(-18, 18),
                random.uniform(-18, 18),
                random.uniform(0.22, 0.45),
                random.choice([CYAN, CYAN_LIGHT, CYAN_GLOW]),
                random.uniform(2, 4)))

    def emit_collision(self, x, y, count=16):
        """受阻反噬：赤红火星四溅。"""
        for _ in range(count):
            ang = random.uniform(0, 6.2831853)
            speed = random.uniform(50, 200)
            vx = math.cos(ang) * speed
            vy = math.sin(ang) * speed
            col = random.choice([WARNING, (255, 120, 90), (255, 190, 140)])
            self.add(Particle(x, y, vx, vy,
                              random.uniform(0.3, 0.6),
                              col, random.uniform(2, 5),
                              gravity=120, kind="spark"))

    def emit_petals(self, width, height, count=2):
        """背景花瓣：自天穹旋转飘落。"""
        for _ in range(count):
            self.add(Particle(
                random.uniform(0, width),
                random.uniform(-20, height * 0.4),
                random.uniform(-18, 18),
                random.uniform(24, 60),
                random.uniform(5.0, 9.0),
                random.choice([PETAL, PETAL_LIGHT]),
                random.uniform(3, 6),
                gravity=0, fade=False, kind="petal",
                ang=random.uniform(0, 6),
                ang_v=random.uniform(-2.5, 2.5)))
