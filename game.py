
import random
import pygame
import config as cfg
from config import (
    MAX_MISTAKE, TOTAL_LEVELS,
    NIGHT_TOP, NIGHT_BOTTOM, CLOUD, MOON,
    CYAN, CYAN_LIGHT,
    JADE_LIGHT, JADE_DARK,
    GOLD, GOLD_LIGHT, GOLD_DARK, WARNING,
)
from board import Board
from audio import AudioManager
from particle import ParticleSystem


class Game:
    """游戏流程与状态管理。

    状态：start / playing / level_clear / victory / defeat
    """

    def __init__(self, screen):
        self.screen = screen
        self.font_l = pygame.font.SysFont("simhei,microsoftyahei,stkaiti", 64)
        self.font_m = pygame.font.SysFont("simhei,microsoftyahei,stkaiti", 36)
        self.font_s = pygame.font.SysFont("simhei,microsoftyahei,stkaiti", 24)
        # 版权行用雅黑：SimHei 缺 © 字形
        self.font_cp = pygame.font.SysFont("microsoftyahei,simhei", 22)
        self.state = "start"
        self.defeat_reason = "qi"     # qi 剑意耗尽 / stuck 困阵
        self.particles = ParticleSystem()
        self.audio = AudioManager()
        self.board = Board(self.particles)
        self.timer = 0.0
        self.petal_timer = 0.0
        self.eyes_seen = 0
        # 飘云（x, y, 横向缩放, 纵向缩放, 速度）
        self.clouds = []
        self.on_view_changed()

    def on_view_changed(self):
        """窗口尺寸变化：重算云海分布，并把飞剑重贴到新格心。"""
        self.clouds = [
            [random.uniform(-100, cfg.VIEW_W),
             random.uniform(60, max(61, cfg.VIEW_H - 120)),
             random.uniform(1.2, 2.6), random.uniform(0.5, 1.0),
             random.uniform(8, 26)]
            for _ in range(7)
        ]
        self.board.relayout()

    # ---------------- 事件 ----------------

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and self.state == "playing":
                self.board.restart_current()
                self.particles.clear()
                self.audio.play_sound("click")
                return
            if event.key == pygame.K_ESCAPE and self.state in ("victory", "defeat"):
                self._restart_from_beginning()
                self.state = "start"
                return

        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        pos = event.pos

        if self.state == "start":
            self.state = "playing"
            self.audio.play_scene("cloudsea")
            return

        if self.state == "playing":
            result = self.board.handle_click(pos)
            if result == "hit":
                self.audio.play_sound("shoot")
            elif result == "blocked":
                self.audio.play_sound("fail")
            return

        if self.state in ("victory", "defeat"):
            self._restart_from_beginning()
            return

        if self.state == "level_clear":
            self._enter_next_level()

    # ---------------- 更新 ----------------

    def update(self, dt):
        # 花瓣持续飘落
        self.petal_timer += dt
        if self.petal_timer > 0.18:
            self.petal_timer = 0
            self.particles.emit_petals(cfg.VIEW_W, cfg.VIEW_H, count=1)

        for cl in self.clouds:
            cl[0] += cl[4] * dt
            if cl[0] > cfg.VIEW_W + 220:
                cl[0] = -220
                cl[1] = random.uniform(60, max(61, cfg.VIEW_H - 120))

        self.particles.update(dt)

        if self.state == "playing":
            self.board.update(dt)

            # 阵眼新解除 → 符文启动音
            now_eyes = self.board.activated_count()
            if now_eyes > self.eyes_seen:
                self.audio.play_sound("click")
            self.eyes_seen = now_eyes

            if self.board.is_failed():
                self.state = "defeat"
                self.defeat_reason = "qi"
                self.audio.play_sound("fail")
                self.timer = 0
            elif self.board.is_stuck():
                self.state = "defeat"
                self.defeat_reason = "stuck"
                self.audio.play_sound("fail")
                self.timer = 0
            elif self.board.is_cleared():
                if self.board.is_last_level():
                    self.state = "victory"
                    # 九重天全部通关：不放音效，抬高背景音乐音量
                    self.audio.set_music_volume(
                        AudioManager.MUSIC_VOLUME_VICTORY)
                else:
                    self.state = "level_clear"
                    self.audio.play_sound("levelup")
                self.timer = 0
        elif self.state in ("level_clear", "victory", "defeat"):
            self.board.update(dt)
            self.timer += dt
            if self.state == "level_clear" and self.timer > 2.4:
                self._enter_next_level()

    # ---------------- 状态切换 ----------------

    def _enter_next_level(self):
        if self.board.next_level():
            self.state = "playing"
            self.timer = 0
            self.eyes_seen = 0

    def _restart_from_beginning(self):
        self.audio.set_music_volume(AudioManager.MUSIC_VOLUME_NORMAL)
        self.board.reset()
        self.particles.clear()
        self.state = "playing"
        self.timer = 0
        self.eyes_seen = 0

    # ---------------- 绘制 ----------------

    def draw(self):
        self._draw_background()

        if self.state == "start":
            self._draw_start()
        else:
            self.board.draw(self.screen)
            self._draw_hud()

        self.particles.draw(self.screen)

        if self.state == "level_clear":
            page = self.board.level_index
            self._draw_overlay(
                "剑阵已破",
                f"获得《剑谱残页·第 {page} 页》 · 灵气接引下一重天",
                GOLD_LIGHT)
        elif self.state == "victory":
            self._draw_overlay("九天剑主",
                               "失落剑谱终得圆满 · 点击再入仙境", GOLD)
        elif self.state == "defeat":
            if self.defeat_reason == "stuck":
                self._draw_overlay(
                    "剑困阵中",
                    "余剑无路可走，阵眼未破尽 · 点击重整剑诀",
                    WARNING)
            else:
                self._draw_overlay(
                    "剑阵反噬",
                    f"剑意耗尽 {MAX_MISTAKE} 点 · 点击重整剑诀",
                    WARNING)

    def _draw_background(self):
        for y in range(0, cfg.VIEW_H, 4):
            t = y / cfg.VIEW_H
            r = int(NIGHT_TOP[0] * (1 - t) + NIGHT_BOTTOM[0] * t)
            g = int(NIGHT_TOP[1] * (1 - t) + NIGHT_BOTTOM[1] * t)
            b = int(NIGHT_TOP[2] * (1 - t) + NIGHT_BOTTOM[2] * t)
            pygame.draw.rect(self.screen, (r, g, b),
                             (0, y, cfg.VIEW_W, 4))

        self._draw_moon(cfg.VIEW_W - 60, 148)
        for cl in self.clouds:
            self._draw_cloud(cl[0], cl[1], cl[2], cl[3])

    def _draw_moon(self, x, y):
        size = 120
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        for i in range(6, 0, -1):
            alpha = 7 + i * 3
            pygame.draw.circle(surf, (*MOON, alpha),
                               (size // 2, size // 2), 16 + i * 8)
        self.screen.blit(surf, (x - size // 2, y - size // 2))
        pygame.draw.circle(self.screen, MOON, (x, y), 27)
        pygame.draw.circle(self.screen, (228, 220, 190), (x - 8, y - 6), 5)
        pygame.draw.circle(self.screen, (232, 224, 196), (x + 9, y + 8), 3)

    def _draw_cloud(self, x, y, sx, sy):
        surf = pygame.Surface((int(190 * sx), int(70 * sy)),
                              pygame.SRCALPHA)
        col = (*CLOUD, 26)
        pygame.draw.ellipse(surf, col, (0, 18 * sy, 110 * sx, 34 * sy))
        pygame.draw.ellipse(surf, col, (40 * sx, 0, 80 * sx, 40 * sy))
        pygame.draw.ellipse(surf, col, (85 * sx, 16 * sy, 95 * sx, 30 * sy))
        self.screen.blit(surf, (int(x), int(y)))

    def _draw_start(self):
        title = self.font_l.render("仙境飞剑阵", True, GOLD)
        sub = self.font_m.render("失 落 剑 谱", True, CYAN_LIGHT)
        hint = self.font_s.render(
            f"点击进入仙境 · 共 {TOTAL_LEVELS} 重天 · F11 全屏", True, GOLD_DARK)
        self.screen.blit(title, (cfg.VIEW_W // 2 - title.get_width() // 2, 250))
        self.screen.blit(sub, (cfg.VIEW_W // 2 - sub.get_width() // 2, 342))
        self.screen.blit(hint, (cfg.VIEW_W // 2 - hint.get_width() // 2, 420))

        desc_lines = [
            "上古九大仙门共创《九天剑谱》，将失控剑灵封入九重仙境",
            "千年之后，你携残缺剑谱踏入遗迹，寻访失落的传承",
            "点击飞剑释放，飞剑沿直线飞行，剑气所经之处阵眼自解",
            "解除全部阵眼并放尽所有飞剑，方可升入下一重天",
            f"剑意耗尽 {MAX_MISTAKE} 点则遭剑阵反噬 · 游戏中按 R 重开本重天",
        ]
        for i, line in enumerate(desc_lines):
            t = self.font_s.render(line, True, (178, 200, 220))
            self.screen.blit(t, (cfg.VIEW_W // 2 - t.get_width() // 2,
                                 500 + i * 40))

        # 版权声明
        cp = self.font_cp.render("© 朱铭浩_Emmamone 版权所有",
                                 True, (128, 148, 176))
        self.screen.blit(cp, (cfg.VIEW_W // 2 - cp.get_width() // 2,
                              cfg.VIEW_H - 42))

    def _draw_hud(self):
        title = self.font_m.render(self.board.level_name, True, GOLD)
        self.screen.blit(title, (cfg.VIEW_W // 2 - title.get_width() // 2, 56))

        lv = self.font_s.render(
            f"第 {self.board.level_index} / {TOTAL_LEVELS} 重天",
            True, CYAN_LIGHT)
        self.screen.blit(lv, (30, 28))

        # 破阵进度
        prog = self.font_s.render(
            f"破阵进度  {self.board.activated_count()} / "
            f"{self.board.total_eyes()}",
            True, JADE_LIGHT)
        self.screen.blit(prog, (30, 66))
        bar_x, bar_y, bar_w, bar_h = 30, 102, 210, 10
        pygame.draw.rect(self.screen, JADE_DARK,
                         (bar_x, bar_y, bar_w, bar_h), border_radius=5)
        if self.board.total_eyes():
            ratio = self.board.activated_count() / self.board.total_eyes()
            fw = int(bar_w * ratio)
            if fw > 0:
                pygame.draw.rect(self.screen, JADE_LIGHT,
                                 (bar_x, bar_y, fw, bar_h), border_radius=5)

        # 余剑（全部放尽才能破阵）
        left = self.font_s.render(
            f"余剑  {self.board.remaining()} / {len(self.board.swords)}",
            True, CYAN_LIGHT)
        self.screen.blit(left, (30, 118))

        # 剑意值
        label = self.font_s.render("剑意值", True, GOLD_DARK)
        self.screen.blit(label, (cfg.VIEW_W - 180, 28))
        for i in range(MAX_MISTAKE):
            used = i < self.board.mistakes
            cx = cfg.VIEW_W - 30 - (MAX_MISTAKE - 1 - i) * 34
            if used:
                pygame.draw.circle(self.screen, (90, 60, 60), (cx, 72), 11)
                pygame.draw.circle(self.screen, WARNING, (cx, 72), 11, 2)
            else:
                pygame.draw.circle(self.screen, CYAN, (cx, 72), 11)
                pygame.draw.circle(self.screen, CYAN_LIGHT, (cx, 72), 11, 2)
        chances = self.font_s.render(
            f"残余 {self.board.remaining_chances} / {MAX_MISTAKE}",
            True, CYAN_LIGHT)
        self.screen.blit(chances, (cfg.VIEW_W - 180, 96))

        # 底部提示 + 版权声明（SimHei 缺 © 字形，用雅黑渲染）
        cp = self.font_cp.render(
            "点击飞剑释放 · 剑气经行阵眼自解 · © 朱铭浩_Emmamone 版权所有",
            True, (150, 172, 196))
        self.screen.blit(cp, (cfg.VIEW_W // 2 - cp.get_width() // 2,
                              cfg.VIEW_H - 42))

    def _draw_overlay(self, big, small, color):
        overlay = pygame.Surface((cfg.VIEW_W, cfg.VIEW_H), pygame.SRCALPHA)
        overlay.fill((6, 12, 26, 160))
        self.screen.blit(overlay, (0, 0))
        big_t = self.font_l.render(big, True, color)
        small_t = self.font_s.render(small, True, GOLD_LIGHT)
        self.screen.blit(big_t,
                         (cfg.VIEW_W // 2 - big_t.get_width() // 2,
                          cfg.VIEW_H // 2 - 80))
        self.screen.blit(small_t,
                         (cfg.VIEW_W // 2 - small_t.get_width() // 2,
                          cfg.VIEW_H // 2 + 12))
