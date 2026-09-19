
import pygame
from game import Game
import config as cfg
from config import WIDTH, HEIGHT, FPS

pygame.init()

# 游戏画面自适应窗口：内容按窗口尺寸实时布局，1:1 铺满（无黑边、不变形），
# 窗口可随意拖拽大小，F11 在全屏 / 窗口间切换；
# 窗口小于最小尺寸时画布整体等比缩小居中
window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("仙境飞剑阵：失落剑谱 · © 朱铭浩_Emmamone 版权所有")

clock = pygame.time.Clock()

cfg.set_view(*window.get_size())
canvas = pygame.Surface((cfg.VIEW_W, cfg.VIEW_H))
game = Game(canvas)

fullscreen = False


def apply_view():
    """按当前窗口尺寸重算游戏布局并重建画布。"""
    global canvas
    cfg.set_view(*window.get_size())
    canvas = pygame.Surface((cfg.VIEW_W, cfg.VIEW_H))
    game.screen = canvas
    game.on_view_changed()


def view_place():
    """画布在窗口中的摆放 (缩放, 偏移x, 偏移y)。

    窗口不小于画布时 1:1 铺满；小于最小尺寸时等比缩小居中。
    """
    ww, wh = window.get_size()
    cw, ch = canvas.get_size()
    if ww >= cw and wh >= ch:
        return 1.0, 0, 0
    scale = min(ww / cw, wh / ch)
    bw, bh = int(cw * scale), int(ch * scale)
    return scale, (ww - bw) // 2, (wh - bh) // 2


def to_canvas_pos(pos):
    """窗口坐标 → 画布坐标（点击判定用）。"""
    scale, off_x, off_y = view_place()
    return (int((pos[0] - off_x) / scale), int((pos[1] - off_y) / scale))


def toggle_fullscreen():
    global fullscreen, window
    fullscreen = not fullscreen
    if fullscreen:
        window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    apply_view()


running = True
while running:
    dt = clock.tick(FPS) / 1000.0  # 秒

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            apply_view()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            toggle_fullscreen()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mapped = pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, pos=to_canvas_pos(event.pos))
            game.handle_event(mapped)
        else:
            game.handle_event(event)

    game.update(dt)
    game.draw()

    scale, off_x, off_y = view_place()
    if scale == 1.0:
        window.blit(canvas, (0, 0))
    else:
        bw = int(canvas.get_width() * scale)
        bh = int(canvas.get_height() * scale)
        window.fill((4, 8, 18))
        window.blit(pygame.transform.smoothscale(canvas, (bw, bh)),
                    (off_x, off_y))
    pygame.display.flip()

pygame.quit()
