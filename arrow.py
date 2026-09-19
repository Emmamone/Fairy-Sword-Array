
import math
import pygame
import config as cfg
from config import (
    ROWS, COLS, CELL,
    CYAN, CYAN_LIGHT, CYAN_DARK, CYAN_GLOW,
    GOLD, GOLD_LIGHT, GOLD_DARK, JADE_DARK, PETAL, WARNING,
)


def board_bounds():
    """棋盘像素范围 (left, right, top, bottom)，随窗口布局实时变化。"""
    return (cfg.GRID_OFFSET_X,
            cfg.GRID_OFFSET_X + cfg.COLS * cfg.CELL,
            cfg.GRID_OFFSET_Y,
            cfg.GRID_OFFSET_Y + cfg.ROWS * cfg.CELL)


def cell_center(row, col):
    return (cfg.GRID_OFFSET_X + col * cfg.CELL + cfg.CELL // 2,
            cfg.GRID_OFFSET_Y + row * cfg.CELL + cfg.CELL // 2)


def inside(row, col):
    return 0 <= row < ROWS and 0 <= col < COLS


VEC = {"up": (0, -1), "down": (0, 1),
       "left": (-1, 0), "right": (1, 0)}

# 格子方向（row 增量, col 增量）
GRID_VEC = {"up": (-1, 0), "down": (1, 0),
            "left": (0, -1), "right": (0, 1)}


def trace_path(row, col, direction, occupied):
    """沿剑阵模拟飞剑直线轨迹（纯函数，棋盘与测试共用）。

    occupied: 回调 occupied(r, c) -> bool，该格是否停有其他飞剑
    返回 (blocked, path)：
      blocked=True  前方剑阻路
      path          依次经过的 (行, 列)，含出发格
    """
    dr, dc = GRID_VEC[direction]
    path = [(row, col)]
    r, c = row, col
    while True:
        nr, nc = r + dr, c + dc
        if not inside(nr, nc):
            return False, path            # 飞出棋盘，畅通
        if occupied(nr, nc):
            return True, path             # 被其他飞剑挡住
        r, c = nr, nc
        path.append((r, c))


class Sword:
    """飞剑。

    状态：
      idle    静待点击
      fly     已释放，沿直线飞行
      blocked 前方有剑阻挡，震剑+红闪后回到 idle
      gone    已飞离棋盘
    """

    FLY_SPEED = CELL * 9          # 每秒跨越九格
    LEAVE_DIST = 46               # 最后一格冲出场外的距离

    def __init__(self, row, col, direction, particles=None):
        self.row = row
        self.col = col
        self.direction = direction
        self.x, self.y = cell_center(row, col)
        self.fly_x = float(self.x)
        self.fly_y = float(self.y)
        self.state = "idle"
        self.particles = particles
        self.pulse = 0.0

        # 飞行计划：尚未抵达的格 [(r, c)]
        self.plan = []
        self.target = None
        self.leaving = False
        self.on_reach = None
        self.trail = []              # 剑气拖尾点
        self.afterimages = []        # (x, y, dir) 光影残像
        self.sample_timer = 0.0

        # blocked 动画参数
        self.block_timer = 0.0
        self.block_duration = 0.55
        self.block_origin_x = float(self.x)
        self.block_origin_y = float(self.y)

        self._sword_surf = self._render_surface(False)
        self._block_surf = self._render_surface(True)

    # ---------- 表面渲染 ----------

    def _render_surface(self, blocked):
        """绘制一柄朝上的短剑（长剑身 / 金护手 / 玉柄 / 剑穗）。"""
        surf = pygame.Surface((60, 60), pygame.SRCALPHA)
        blade = (255, 200, 200) if blocked else (238, 248, 255)
        edge = WARNING if blocked else CYAN_DARK
        guard = (220, 90, 90) if blocked else GOLD
        # 剑身
        pygame.draw.polygon(surf, blade,
                            [(30, 5), (26, 33), (34, 33)])
        pygame.draw.polygon(surf, edge,
                            [(30, 5), (26, 33), (34, 33)], 2)
        # 剑脊高光
        pygame.draw.line(surf, CYAN_LIGHT, (30, 10), (30, 31), 2)
        # 护手
        pygame.draw.rect(surf, guard, (19, 32, 22, 5), border_radius=2)
        pygame.draw.rect(surf, GOLD_DARK, (19, 32, 22, 5), 1, border_radius=2)
        # 剑柄与柄首
        pygame.draw.rect(surf, JADE_DARK, (28, 37, 4, 12), border_radius=2)
        pygame.draw.circle(surf, guard, (30, 52), 3)
        # 剑穗
        pygame.draw.line(surf, PETAL, (30, 52), (26, 59), 2)
        return surf

    def _directed_surface(self, direction, blocked=False):
        base = self._block_surf if blocked else self._sword_surf
        angle = {"up": 0, "right": -90, "down": 180, "left": 90}[direction]
        return pygame.transform.rotate(base, angle)

    # ---------- 触发 ----------

    def launch(self, plan, on_reach):
        """plan 为含出发格的 [(r, c)]，on_reach(r, c) 抵格回调。"""
        if self.state != "idle" or len(plan) < 1:
            return False
        self.state = "fly"
        self.plan = plan[1:]
        self.on_reach = on_reach
        self.fly_x, self.fly_y = cell_center(plan[0][0], plan[0][1])
        self.trail.clear()
        self.afterimages.clear()
        self.leaving = False
        self._set_next_target()
        return True

    def trigger_blocked(self):
        if self.state != "idle":
            return False
        self.state = "blocked"
        self.block_timer = 0.0
        self.block_origin_x = float(self.x)
        self.block_origin_y = float(self.y)
        if self.particles:
            self.particles.emit_collision(self.x, self.y)
        return True

    def snap_to_cell(self):
        """窗口布局变化后按新格心重置位置（飞行中的剑回到出发格续飞）。"""
        self.x, self.y = cell_center(self.row, self.col)
        self.fly_x = float(self.x)
        self.fly_y = float(self.y)
        self.block_origin_x = float(self.x)
        self.block_origin_y = float(self.y)
        self.trail.clear()
        self.afterimages.clear()
        if self.state == "fly":
            self._set_next_target()

    def _set_next_target(self):
        if self.plan:
            r, c = self.plan[0]
            self.target = cell_center(r, c)
        else:
            dx, dy = VEC[self.direction]
            self.target = (self.fly_x + dx * self.LEAVE_DIST,
                           self.fly_y + dy * self.LEAVE_DIST)
            self.leaving = True

    # ---------- 更新 ----------

    def update(self, dt):
        self.pulse += dt
        if self.state == "fly":
            self._update_fly(dt)
        elif self.state == "blocked":
            self._update_blocked(dt)

    def _update_fly(self, dt):
        tx, ty = self.target
        dx = tx - self.fly_x
        dy = ty - self.fly_y
        dist = math.hypot(dx, dy)
        step = self.FLY_SPEED * dt

        # 残像采样
        self.sample_timer -= dt
        if self.sample_timer <= 0:
            self.sample_timer = 0.045
            self.afterimages.append((self.fly_x, self.fly_y, self.direction))
            if len(self.afterimages) > 4:
                self.afterimages.pop(0)

        if step >= dist > 0:
            self.fly_x, self.fly_y = float(tx), float(ty)
        else:
            self.fly_x += dx / dist * step
            self.fly_y += dy / dist * step

        # 剑气拖尾
        self.trail.append((self.fly_x, self.fly_y))
        if len(self.trail) > 16:
            self.trail.pop(0)
        if self.particles:
            self.particles.emit_qi_trail(self.fly_x, self.fly_y)

        if step >= dist:
            if self.leaving:
                if self.particles:
                    bl, br, bt, bb = board_bounds()
                    ex = max(bl - 6, min(br + 6, self.fly_x))
                    ey = max(bt - 6, min(bb + 6, self.fly_y))
                    self.particles.emit_sword_burst(ex, ey)
                self.state = "gone"
                return
            r, c = self.plan.pop(0)
            if self.on_reach:
                self.on_reach(r, c)
            self._set_next_target()

    def _update_blocked(self, dt):
        self.block_timer += dt
        t = self.block_timer / self.block_duration
        if t >= 1.0:
            self.state = "idle"
            self.fly_x = float(self.x)
            self.fly_y = float(self.y)
            return
        # 朝方向冲一小段再被弹回
        dx, dy = VEC[self.direction]
        d = 26 * math.sin(t * math.pi)
        self.fly_x = self.block_origin_x + dx * d
        self.fly_y = self.block_origin_y + dy * d

    # ---------- 绘制 ----------

    def draw(self, screen):
        if self.state == "gone":
            return
        if self.state == "idle":
            self._draw_halo(screen, self.x, self.y, 36, pulse=True)
            self._draw_sword(screen, self.x, self.y, self.direction)
        elif self.state == "fly":
            self._draw_afterimages(screen)
            self._draw_trail(screen)
            self._draw_halo(screen, self.fly_x, self.fly_y, 24, pulse=False)
            self._draw_sword(screen, self.fly_x, self.fly_y, self.direction)
        elif self.state == "blocked":
            self._draw_blocked(screen)

    def _draw_sword(self, screen, x, y, direction, alpha=255):
        spr = self._directed_surface(direction)
        if alpha < 255:
            spr = spr.copy()
            spr.set_alpha(alpha)
        rect = spr.get_rect(center=(int(x), int(y)))
        screen.blit(spr, rect)

    def _draw_afterimages(self, screen):
        n = len(self.afterimages)
        for i, (px, py, d) in enumerate(self.afterimages):
            alpha = int(70 * (i + 1) / max(1, n))
            self._draw_sword(screen, px, py, d, alpha=alpha)

    def _draw_halo(self, screen, x, y, radius, pulse=False):
        r = radius + (4 * math.sin(self.pulse * 4) if pulse else 0)
        size = int(r * 2) + 4
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        for i in range(5, 0, -1):
            alpha = 16 + i * 6
            pygame.draw.circle(surf, (*CYAN_GLOW, alpha),
                               center, int(r * i / 5))
        screen.blit(surf, (int(x) - size // 2, int(y) - size // 2))

    def _draw_trail(self, screen):
        n = len(self.trail)
        for i, (px, py) in enumerate(self.trail):
            t = (i + 1) / max(1, n)
            r = max(2, int(2 + 5 * t))
            alpha = int(180 * t)
            surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*CYAN_LIGHT, alpha),
                               (r + 1, r + 1), r)
            screen.blit(surf, (int(px) - r - 1, int(py) - r - 1))

    def _draw_blocked(self, screen):
        blink = 0.5 + 0.5 * math.sin(self.block_timer * 30)
        radius = 44 + 6 * math.sin(self.block_timer * 20)
        size = int(radius * 2) + 4
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        for i in range(5, 0, -1):
            alpha = int((12 + i * 8) * blink)
            pygame.draw.circle(surf, (*WARNING, alpha),
                               center, int(radius * i / 5))
        screen.blit(surf, (int(self.fly_x) - size // 2,
                           int(self.fly_y) - size // 2))
        self._draw_sword(screen, self.fly_x, self.fly_y, self.direction)

    # ---------- 点击 ----------

    def rect(self):
        return pygame.Rect(
            self.x - CELL // 2, self.y - CELL // 2, CELL, CELL
        )

    def contains(self, pos):
        return self.state == "idle" and self.rect().collidepoint(pos)
