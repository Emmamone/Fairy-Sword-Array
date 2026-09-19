
import math
import pygame
import config as cfg
from config import (
    ROWS, COLS, CELL,
    STONE, STONE_EDGE, STONE_HIGHLIGHT, BOARD_FRAME,
    GOLD, GOLD_LIGHT, GOLD_DARK, GOLD_GLOW,
    JADE_LIGHT, JADE_DARK, CYAN_GLOW,
    LEVELS, MAX_MISTAKE,
)
from arrow import Sword, trace_path, cell_center


class Board:
    """剑阵棋盘：关卡加载、阵眼、点击判定、阻挡模拟、关卡推进。"""

    def __init__(self, particles):
        self.particles = particles
        self.level = 0
        self.swords = []
        self.eyes = {}          # (r, c) -> bool（True 为已解除）
        self.mistakes = 0
        self.time = 0.0
        self.load()

    # ---------------- 关卡 ----------------

    def load(self):
        cfg = LEVELS[self.level]
        self.swords = [
            Sword(r, c, d, particles=self.particles)
            for (r, c, d) in cfg["swords"]
        ]
        self.eyes = {(r, c): False for (r, c) in cfg.get("eyes", [])}
        self.time = 0.0

    @property
    def level_name(self):
        return LEVELS[self.level]["name"]

    @property
    def level_index(self):
        return self.level + 1

    @property
    def remaining_chances(self):
        return max(0, MAX_MISTAKE - self.mistakes)

    def is_last_level(self):
        return self.level >= len(LEVELS) - 1

    def next_level(self):
        if self.level < len(LEVELS) - 1:
            self.level += 1
            self.load()
            return True
        return False

    def reset(self):
        self.level = 0
        self.mistakes = 0
        self.load()

    def restart_current(self):
        """重开本重：剑意复原，阵眼与飞剑归位。"""
        self.mistakes = 0
        self.load()

    def relayout(self):
        """窗口尺寸变化后，把飞剑重贴到新布局的格心。"""
        for s in self.swords:
            s.snap_to_cell()

    # ---------------- 阵眼 ----------------

    def total_eyes(self):
        return len(self.eyes)

    def activated_count(self):
        return sum(1 for v in self.eyes.values() if v)

    def is_cleared(self):
        """破阵条件：解除全部阵眼，且全部飞剑离场。"""
        eyes_ok = bool(self.eyes) and all(self.eyes.values())
        return eyes_ok and all(s.state == "gone" for s in self.swords)

    def is_stuck(self):
        """困阵判定：无剑在飞、未破阵，且所有待发飞剑都无路可走。

        此时本重天已无解（含飞剑放尽但阵眼未破尽的情况），判负。
        """
        if self.is_cleared():
            return False
        if any(s.state in ("fly", "blocked") for s in self.swords):
            return False
        for s in self.swords:
            if s.state != "idle":
                continue
            blocked, _path = self.trace_sword(s)
            if not blocked:
                return False
        return True

    def is_failed(self):
        return self.mistakes >= MAX_MISTAKE

    def remaining(self):
        return sum(1 for s in self.swords if s.state != "gone")

    # ---------------- 路径与点击 ----------------

    def _occupied(self, shooter, r, c):
        """该格是否停有其他待发飞剑。"""
        for s in self.swords:
            if s is shooter or s.state != "idle":
                continue
            if s.row == r and s.col == c:
                return True
        return False

    def trace_sword(self, sword):
        return trace_path(
            sword.row, sword.col, sword.direction,
            lambda r, c: self._occupied(sword, r, c),
        )

    def handle_click(self, pos):
        """返回 'hit'（成功释放）/ 'blocked'（剑阻路，失剑意）/
        'ignore'（点空或点棋盘外，不扣剑意）。"""
        for s in self.swords:
            if s.contains(pos):
                blocked, plan = self.trace_sword(s)
                if blocked:
                    s.trigger_blocked()
                    self.mistakes += 1
                    return "blocked"
                s.launch(plan, self._on_sword_reach)
                return "hit"
        return "ignore"

    def _on_sword_reach(self, r, c):
        """飞剑抵达一格：解除阵眼。"""
        x, y = cell_center(r, c)
        if not self.eyes.get((r, c), True):
            self.eyes[(r, c)] = True
            if self.particles:
                self.particles.emit_eye_awaken(x, y)

    # ---------------- 更新 / 绘制 ----------------

    def update(self, dt):
        self.time += dt
        for s in self.swords:
            s.update(dt)

    def draw(self, screen):
        board_rect = pygame.Rect(
            cfg.GRID_OFFSET_X - 14, cfg.GRID_OFFSET_Y - 14,
            COLS * CELL + 28, ROWS * CELL + 28
        )
        pygame.draw.rect(screen, BOARD_FRAME, board_rect, border_radius=12)
        pygame.draw.rect(screen, GOLD_DARK, board_rect, 2, border_radius=12)

        # 玉石阵台格
        for r in range(ROWS):
            for c in range(COLS):
                rect = pygame.Rect(
                    cfg.GRID_OFFSET_X + c * CELL,
                    cfg.GRID_OFFSET_Y + r * CELL,
                    CELL - 6, CELL - 6
                )
                pygame.draw.rect(screen, STONE, rect, border_radius=10)
                pygame.draw.rect(screen, STONE_EDGE, rect, 1, border_radius=10)
                pygame.draw.circle(screen, STONE_HIGHLIGHT,
                                   rect.center, 2, 1)

        # 阵眼（地面机关，先于飞剑绘制）
        for (r, c), active in self.eyes.items():
            self._draw_eye(screen, r, c, active)

        for s in self.swords:
            s.draw(screen)

    def _draw_eye(self, screen, r, c, active):
        x, y = cell_center(r, c)
        if not active:
            # 沉睡阵眼：暗玉圆环 + 暗金菱形符文
            pygame.draw.circle(screen, (22, 38, 54), (x, y), 30)
            pygame.draw.circle(screen, JADE_DARK, (x, y), 30, 2)
            pygame.draw.circle(screen, (44, 66, 84), (x, y), 22, 1)
            diamond = [(x, y - 12), (x + 9, y), (x, y + 12), (x - 9, y)]
            pygame.draw.polygon(screen, JADE_DARK, diamond, 2)
            return

        # 已解除：金青符文亮起，四点灵光绕转
        pulse = 2 + 2 * math.sin(self.time * 3)
        glow_r = 30 + pulse
        size = glow_r * 2 + 6
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cc = size // 2
        for i in range(4, 0, -1):
            pygame.draw.circle(surf, (*GOLD_GLOW, 14 + i * 7),
                               (cc, cc), int(glow_r * i / 4))
        screen.blit(surf, (x - cc, y - cc))

        pygame.draw.circle(screen, GOLD, (x, y), 28, 2)
        pygame.draw.circle(screen, JADE_LIGHT, (x, y), 22, 1)
        diamond = [(x, y - 13), (x + 10, y), (x, y + 13), (x - 10, y)]
        pygame.draw.polygon(screen, JADE_LIGHT, diamond)
        pygame.draw.polygon(screen, GOLD_LIGHT, diamond, 2)
        pygame.draw.circle(screen, GOLD_LIGHT, (x, y), 4)

        for k in range(4):
            ang = self.time * 1.6 + k * math.pi / 2
            px = x + math.cos(ang) * 30
            py = y + math.sin(ang) * 30
            pygame.draw.circle(screen, CYAN_GLOW, (int(px), int(py)), 3)
